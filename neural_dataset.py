import csv
import os
import re
from asyncio import run

import pandas as pd
from loguru import logger
from tqdm import tqdm

from database import hltv_get_upcoming
from hltv_org import hltv_get_html

PLAYER_MATCHES = 50


async def main():
    link = 'https://www.hltv.org/stats/players/matches/{_id}/{nickname}?startDate=all&rankingFilter=Top50'
    events = await hltv_get_upcoming()

    if not events:
        logger.info('No upcoming events')
        return

    if not os.path.exists('./forecasts'):
        os.mkdir('./forecasts')

    if not os.path.exists('./forecasts/test_data.csv'):
        with open('./forecasts/test_data.csv', 'w') as _:
            pass

    for event in tqdm(events, 'All events'):
        if not event['teams']:
            continue

        for team in event['teams']:
            if not event['teams'][team]:
                continue

            for player in tqdm(event['teams'][team]['players'], 'Players'):
                player_info = event['teams'][team]['players'][player]['profileLinkUrl'].split('/')

                try:
                    dataframe = pd.read_csv('./forecasts/test_data.csv')
                    unique_players = dataframe.iloc[:, 0].unique()
                except pd.errors.EmptyDataError:
                    unique_players = []
                if int(player_info[2]) in unique_players:
                    continue

                player_link = link.format(_id=player_info[2], nickname=player_info[3])
                html = await hltv_get_html(player_link)
                matches_table = html.find(class_='stats-table no-sort')
                if not matches_table:
                    continue

                matches_info = matches_table.find('tbody')
                if not matches_info:
                    continue

                all_matches = matches_info.find_all('tr')[:PLAYER_MATCHES]
                for match in tqdm(all_matches, f'Matches {player_info[3]}'):
                    data = {'player_id': player_info[2], 'nickname': player_info[3], 'player_link': player_link}
                    params = match.find_all('td')[:3]
                    data['match_link'] = params[0].find('a')['href']
                    for index, param in enumerate(params[1:]):
                        stats_class = param.find(class_='gtSmartphone-only')
                        spans = stats_class.find_all('span')
                        if index == 0:
                            data['team_player'] = spans[0].text.lower()
                            data['team_player_link'] = stats_class.find('a')['href']
                            data['team_player_score'] = int(re.findall(r'\((.*?)\)', spans[1].text)[0])
                            continue
                        data['team_opponent'] = spans[0].text.lower()
                        data['team_opponent_link'] = stats_class.find('a')['href']
                        data['team_opponent_score'] = stats_class.find('span').text.strip()
                        data['team_opponent_score'] = int(re.findall(r'\((.*?)\)', spans[1].text)[0])

                    data['match_result'] = 0
                    if data['team_player_score'] > data['team_opponent_score']:
                        data['match_result'] = 1

                    try:
                        await player_stats(data)
                    except Exception as err:
                        logger.error(f'{err}\n{data["match_link"]}')
                        continue
                    await increase_dataset(data)

async def player_stats(data: dict):
    match_html = await hltv_get_html('https://www.hltv.org' + data['match_link'])
    teams_info = match_html.find(class_='match-info-box-con')
    if not teams_info:
        return

    teams_info = teams_info.find_all(class_=re.compile(r'^match-info-'))
    is_left = False
    for index, value in enumerate(teams_info[2:5]):
        if index == 0:
            position = value.find(class_='team-left').find('a')['href']
            if position == data['team_player_link']:
                is_left = True
        if index != 2:
            continue
        teams_rating = value.find(class_='right').text.split(' : ')
        data['team_rating'] = float(teams_rating[1])
        data['opponent_rating'] = float(teams_rating[0])
        if is_left:
            data['team_rating'] = float(teams_rating[0])
            data['opponent_rating'] = float(teams_rating[1])

    both_stats = match_html.find_all(class_='stats-table totalstats')
    for stat in both_stats:
        trs = stat.find('tbody').find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            check_player = (f'/stats/players/{data["player_id"]}/{data["nickname"]}'
                            '?startDate=all&rankingFilter=Top50')
            if tds[0].find(class_='flag-align').find('a')['href'] == check_player:
                data['kast'] = float(tds[4].text.replace('%', ''))
                data['adr'] = float(tds[6].text)
                data['rating'] = float(tds[8].text)

async def increase_dataset(data: dict):
    selected_tables = ['player_id', 'nickname', 'team_player', 'team_opponent', 'team_rating',
                       'opponent_rating', 'adr', 'kast', 'rating', 'match_result']
    row = {key: data[key] for key in selected_tables}
    with open('./forecasts/test_data.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=selected_tables)
        writer.writerow(row)

if __name__ == '__main__':
    try:
        run(main())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')
