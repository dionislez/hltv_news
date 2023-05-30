import json
import os
from asyncio import run

import matplotlib.pyplot as plt
import pandas as pd
from joblib import dump, load
from loguru import logger
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neural_network import MLPClassifier

from database import hltv_get_team, hltv_get_upcoming


async def upcoming_data():
    matches = (await hltv_get_upcoming())[0:1]
    team_names = []
    for match in matches:
        if not match.get('teams') or not match['teams']:
            continue
        prediction_data = []
        _ids = list(match['teams'].keys())

        for index, team in enumerate(match['teams']):
            team_stats = []
            team_names.append(match['teams'][team]['team'])
            rating_team = (await hltv_get_team(_ids[index]))['rating']

            if index == 0:
                rating_opponent = (await hltv_get_team(_ids[1]))['rating']
            elif index == 1:
                rating_opponent = (await hltv_get_team(_ids[0]))['rating']

            for stats in match['teams'][team]['players']:
                try:
                    adr = float(match['teams'][team]['players'][stats]['adr'])
                    kast = float(match['teams'][team]['players'][stats]['kast'].replace('%', ''))
                    rating = float(match['teams'][team]['players'][stats]['rating'])
                except Exception:
                    continue
                player = [rating_team, rating_opponent, adr, kast, rating]
                team_stats.append(player)

            prediction_data.append(team_stats)

        if not prediction_data[0] or not prediction_data[1]:
            print({'prediction': {}})
            return

        prediction_result = await neural_network(prediction_data, team_names)
        print(prediction_result)

async def neural_network(prediction_data, team_names):
    clf = await model()

    predictions1 = clf.predict_proba(prediction_data[0])
    predictions2 = clf.predict_proba(prediction_data[1])

    plt.figure()
    plt.plot(predictions1[:, 1], label=team_names[0])
    plt.plot(predictions2[:, 1], label=team_names[1])
    plt.xlabel('Номер образца')
    plt.ylabel('Вероятность победы')
    plt.legend()
    plt.savefig(f'./forecasts/{team_names[0]}_{team_names[1]}.png')

    win_prob_1 = predictions1[:, 1].mean()
    win_prob_2 = predictions2[:, 1].mean()
    win_ratio_1 = (win_prob_1 / (win_prob_1 + win_prob_2)) * 100
    win_ratio_2 = (win_prob_2 / (win_prob_1 + win_prob_2)) * 100
    return {'prediction': {team_names[0]: win_ratio_1, team_names[1]: win_ratio_2}}

async def model():
    data = pd.read_csv('./forecasts/test_data.csv', header=None)
    _json = {'shape': -1}
    if os.path.exists('./forecasts/dataset_shape.json'):
        with open('./forecasts/dataset_shape.json', 'r') as json_file:
            _json = json.load(json_file)

    if os.path.exists('./forecasts/model.joblib') and _json['shape'] == data.shape[0]:
        return load('./forecasts/model.joblib')

    features = data.iloc[:, [4, 5, 6, 7, 8]]
    target = data.iloc[:, -1]
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.33, random_state=42)
    mlp = MLPClassifier(max_iter=data.shape[0])
    parameter_space = {
        'hidden_layer_sizes': [(300, 150, 50)],
        'activation': ['logistic'],
        'solver': ['adam'],
        'alpha': [0.05],
        'learning_rate': ['adaptive'],
    }
    clf = GridSearchCV(mlp, parameter_space, n_jobs=-1, cv=3)
    clf.fit(X_train, y_train)

    dump(clf, './forecasts/model.joblib')
    with open('./forecasts/dataset_shape.json', 'w') as json_file:
        json.dump({'shape': data.shape[0]}, json_file)
    return clf

if __name__ == '__main__':
    try:
        run(upcoming_data())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')