import asyncio
from pprint import pprint
from database import hltv_get_upcoming

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


async def main():
    matches = await hltv_get_upcoming()
    for match in matches:
        if not match['teams']:
            continue

        filter_ = {}
        for team in match['teams']:
            past_matches = []
            filter_[match['teams'][team]['team']] = {}

            for past in match['teams'][team]['past_matches']:
                score = past['bo'].split(' - ') if not past.get('score') else past['score'].split(' - ')
                score = [int(x) for x in score]
                if sum(score) > 5:
                    score = [1, 0] if past['result'] == 'win' else [0, 1]
                past_matches.append(score)
            
            filter_[match['teams'][team]['team']]['players'] = {}
            for player in match['teams'][team]['players']:
                filter_[
                    match['teams'][team]['team']
                ][
                    'players'
                ][
                    match['teams'][team]['players'][player]['nickname']
                ] = [
                    match['teams'][team]['players'][player]['numericAdr'],
                    match['teams'][team]['players'][player]['numericDpr'],
                    match['teams'][team]['players'][player]['numericImpact'],
                    match['teams'][team]['players'][player]['numericKast'],
                    match['teams'][team]['players'][player]['numericKpr'],
                    match['teams'][team]['players'][player]['numericRating']
                ]

            filter_[match['teams'][team]['team']]['scores'] = past_matches
        await data_check(filter_)
        return

async def data_check(data: dict):
    result = {}
    for team in data:
        result[team] = {}
        sum_ = 0
        for score in data[team]['scores']:
            if score[0] > score[1]:
                sum_ += 1
        result[team]['%_wins'] = (sum_ / len(data[team]['scores'])) * 100
    print(result)

async def model_check(data: dict):
    X, y = [], []
    for team in data:
        for player in data[team]['players']:
            player_features = data[team]['players'][player]
            scores = data[team]['scores']
            player_labels = [1 if score[0] > score[1] else 0 for score in scores]
            X.extend([player_features] * len(scores))
            y.extend(player_labels)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LogisticRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print("Accuracy:", accuracy)

if __name__ == '__main__':
    asyncio.run(main())