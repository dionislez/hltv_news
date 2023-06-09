import asyncio
import json
import re
from asyncio import TimeoutError
from datetime import datetime, timedelta

import aiohttp
from aiohttp.client_exceptions import ClientOSError, ServerDisconnectedError
from bs4 import BeautifulSoup
from decouple import config
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

from database import (hltv_delete_live, hltv_delete_upcoming, hltv_update_live,
                      hltv_update_upcoming, htlv_all_players_update)
from formetters.players_format import (hltv_career_check,
                                       html_individual_check,
                                       html_overview_check)

HLTV_MONTH = {'01': 'january', '02': 'february', '03': 'march', '04': 'april',
              '05': 'may', '06': 'june', '07': 'july', '08': 'august',
              '09': 'september', '10': 'october', '11': 'november', '12': 'december'}
DRIVER_OPTIONS = ['--log-level=1', 'headless', ('user-agent=Mozilla/5.0 '
                                                '(Windows NT 10.0; Win64; x64)'
                                                ' AppleWebKit/537.36 (KHTML, '
                                                'like Gecko) Chrome/111.0.0.0'
                                                ' Safari/537.36')]
HEADERS = {
    'referer': 'https://www.hltv.org/stats',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}
COOKIES = {'hltvTimeZone': 'Europe/Copenhagen'}


async def hltv_get_html(link: str):
    await asyncio.sleep(0.5)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
        async with session.get(url=link) as response:
            if response.status < 400:
                html = await response.text()
                return BeautifulSoup(html, 'lxml')
        if response.status == 403:
            link_params = await params_formatter(link)
            async with session.get(
                url=link_params[0],
                headers=HEADERS,
                cookies=COOKIES,
                params=link_params[1]
            ) as response:
                if response.status < 400:
                    html = await response.text()
                    return BeautifulSoup(html, 'lxml')
        try:
            service = Service(executable_path='chromedriver\chromedriver.exe')
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            for driver_option in DRIVER_OPTIONS:
                options.add_argument(driver_option)
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(link)
            html = driver.page_source
            return BeautifulSoup(html, 'lxml')
        except Exception as error:
            logger.error(error)
            return
        finally:
            driver.close()
            driver.quit()

async def params_formatter(link: str):
    check_link = link.split('?')
    if len(check_link) == 1:
        return link, None

    params_dict = {}
    params = check_link[1].split('&')
    for param in params:
        key_value = param.split('=')
        params_dict[key_value[0]] = key_value[1]
    return check_link[0], params_dict

async def hltv_actual_news():
    html = await hltv_get_html(config('actual_news'))
    if not html:
        return

    category_news = html.find_all(class_='standard-box standard-list')
    type_news = html.find_all('h2')[:3]
    utcnow = datetime.utcnow()

    result_dict = dict()
    for index, category in enumerate(category_news):
        news = category.find_all('a')
        result_dict[type_news[index].text] = list()
        for item in news:
            data = item.text.strip().replace('\n\n', '\n').split('\n')
            time_ago = utcnow - timedelta(hours=await title_ago(data[1]))
            result_dict[type_news[index].text].append(
                {
                    'title': data[0].replace("'", '`'),
                    'time': data[1],
                    'title_time': time_ago,
                    'source_link': config('actual_news') + item['href']
                }
            )
    return result_dict

async def title_ago(time: str) -> str:
    title_time = time.split(' ')
    if 'day' in title_time[1]:
        if 'a' == title_time[0]:
            ago = 24
        else:
            ago = int(title_time[0]) * 24
        return ago
    if 'an' == title_time[0]:
        return 1
    return int(title_time[0])

async def hltv_history_news(year: str, month: str):
    link = config('history_news').format(year=year, month=HLTV_MONTH[month])
    html = await hltv_get_html(link)
    if not html:
        return
    all_news = html.find_all(class_='standard-box standard-list')

    result_dict = dict()
    result_dict[f'{year}-{month}'] = {}
    for item in all_news[0]:
        data = item.text.strip().replace('\n\n', '\n').split('\n')
        if not result_dict[f'{year}-{month}'].get(data[1]):
            result_dict[f'{year}-{month}'][data[1]] = [{
                'title': data[0].replace("'", '`'),
                'source_link': config('actual_news') + item['href']
            }]
            continue
        result_dict[f'{year}-{month}'][data[1]].append(
            {
                'title': data[0].replace("'", '`'),
                'source_link': config('actual_news') + item['href']
            }
        )
    return result_dict

async def hltv_stats_teams(current_time: datetime):
    team_fields = ['team', 'maps', 'kd_diff', 'kd', 'rating', 'team_id', 'location'] 
    html = await hltv_get_html(config('stats_teams').format(year=current_time.year))
    if not html:
        return

    teams = html.find(class_='stats-table player-ratings-table').find('tbody').find_all('tr')
    for team in tqdm(teams, desc='loop for teams of 2023'):
        team_data = team.text.strip().split('\n')
        team_data.append(team.find('a')['href'].split('/')[-2])
        team_data.append(team.find('img')['title'])
        team_data = dict(zip(team_fields, team_data))
        await hltv_stats_by_team(team_data, current_time.year)
        await asyncio.sleep(1)
        team_data['maps_stats'] = await hltv_stats_maps(team_data["team_id"])
        team_data['current_time'] = str(current_time)
        await htlv_all_players_update(team_data)
        logger.info(f'{team_data["team_id"]}: {team_data["team"]}')

async def hltv_stats_by_team(team_data: dict, year: int):
    html = await hltv_get_html(
        config('stats_team').format(team_id=team_data['team_id'],
                                        year=year)
    )
    if not html:
        return

    columns = html.find(
        class_='stats-section stats-team stats-team-overview'
    ).find_all(class_='columns')
    for column in columns:
        stats = column.find_all(class_='col standard-box big-padding')
        for stat in stats:
            check_stat = stat.text.strip().split('\n')
            if check_stat[1] in ['Maps played', 'K/D Ratio']:
                continue
            if check_stat[1] == 'Wins / draws / losses':
                key = check_stat[1].lower().split(' / ')
                value = check_stat[0].split(' / ')
                for i in range(3):
                    team_data[key[i]] = int(value[i])
                continue
            key = check_stat[1].replace(' ', '_').lower()
            value = check_stat[0]
            team_data[key] = value

    team_data['teammates'] = {}
    teammates = html.find(class_='grid reset-grid').find_all(class_='col teammate')
    for teammate in teammates:
        teammate_info = teammate.text.strip().split('\n')
        teammate_info.append(teammate.find('a')['href'].split('/')[3])
        team_data['teammates'][teammate_info[-1]] = {'nikname': teammate_info[0],
                                                     'maps': int(teammate_info[-2].split(' ')[0])}

async def hltv_stats_maps(team_id: str):
    html = await hltv_get_html(config('stats_maps').format(team_id=team_id))
    if not html:
        return {}

    maps = html.find(class_='two-grid').find_all(class_='col')
    replace_ = {
        0: 'Wins / draws / losses',
        1: 'Win rate',
        2: 'Total rounds',
        3: 'Round win-% after getting first kill',
        4: 'Round win-% after receiving first death'
    }
    result = {}
    for map in maps:
        name = map.find(class_='map-pool-map-name')
        if not name:
            continue
        name = name.text.strip()

        stats = map.find_all(class_='stats-row')
        stats_dict = {}
        for index, stat in enumerate(stats):
            value = stat.text.strip().replace(replace_[index], '')
            if index == 0:
                value = value.split(' / ')
                value = [int(i) for i in value]
            if index == 2:
                value = float(value)
            elif index == 3:
                key = 'perc_first_k'
                value = float(value.replace('%', ''))
            elif index == 4:
                key = 'perc_first_d'
                value = float(value.replace('%', ''))
            else:
                key = replace_[index].lower().replace(' / ', '_').replace(' ', '_')
            stats_dict[key] = value
        result[name] = stats_dict
    return result

async def hltv_stats_player(player_id: str, player_nick: str):
    try:
        html_overview = await hltv_get_html(config('stats_players_overview').format(
            player_id=player_id,
            player_nick=player_nick
        ))
        html_individual = await hltv_get_html(config('stats_players_individual').format(
            player_id=player_id,
            player_nick=player_nick
        ))
        html_career = await hltv_get_html(config('stats_players_career').format(
            player_id=player_id,
            player_nick=player_nick
        ))
    except TimeoutError:
        logger.error(f'TimeoutError: {player_id} - {player_nick}')
        with open('./logs/logs_players.txt', 'a') as file:
            file.write(f'{player_id},{player_nick}\n')
        return
    except ServerDisconnectedError:
        logger.error(f'ServerDisconnectedError: {player_id} - {player_nick}')
        with open('./logs/logs_players.txt', 'a') as file:
            file.write(f'{player_id},{player_nick}\n')
        return
    except ClientOSError:
        logger.error(f'ClientOSError: {player_id} - {player_nick}')
        with open('./logs/logs_players.txt', 'a') as file:
            file.write(f'{player_id},{player_nick}\n')
        return

    rating_data = html_overview.find(class_='graph')
    if rating_data:
        rating_data = json.loads(rating_data['data-fusionchart-config'])['dataSource']

    try:
        overview_stats = html_overview.find_all(class_='stats-row')
        individual_stats = html_individual.find_all(class_='stats-row')
        career_stats = html_career.find(class_='stats-table').find_all(class_='stat-rating')
    except AttributeError as error:
        logger.error(f'AttributeError: {player_id} - {player_nick}\n{error}')
        return

    overview_ = {}
    for index, stat in enumerate(overview_stats):
        format_stat = stat.text.strip()
        await html_overview_check(index, format_stat, overview_)

    for index, stat in enumerate(individual_stats):
        format_stat = stat.text.strip()
        await html_individual_check(index, format_stat, overview_)

    cur_year = datetime.utcnow().year
    overview_['career'] = {}
    for year in range(int(len(career_stats) / 4) - 1, -1, -1):
        overview_['career'][str(cur_year - year)] = {}

    career_stats = [career_stats[i:i+4] for i in range(0, len(career_stats), 4)]
    for index, stats in enumerate(career_stats):
        key = list(overview_['career'].keys())[index]
        for index, stat in enumerate(stats):
            format_stat = stat.text.strip()
            await hltv_career_check(index, format_stat, overview_['career'][key])

    return [overview_, rating_data, player_id]

async def hltv_team_matches(team_id: str, team_name: str):
    try:
        html = await hltv_get_html(config('matches_team').format(team_id=team_id, team_name=team_name))
    except TimeoutError:
        logger.error(f'TimeoutError: {team_id} - {team_name}')
        with open('./logs/logs_matches.txt', 'a') as file:
            file.write(f'{team_id},{team_name}\n')
        return
    except ClientOSError:
        logger.error(f'ClientOSError: {team_id} - {team_name}')
        with open('./logs/logs_matches.txt', 'a') as file:
            file.write(f'{team_id},{team_name}\n')
        return

    if not html.find(class_='stats-table no-sort') or not html:
        logger.error('No data')
        return

    stats_table = html.find(class_='stats-table no-sort').find('tbody').find_all('tr')
    result = []
    fields = ['date', 'event', 'opponent', 'map', 'score', 'result']

    for stat in stats_table:
        format_stat = stat.text.strip().split('\n')
        stats = []
        [stats.append(v) for v in format_stat if v not in stats]

        dict_ = dict(zip(fields, stats))
        dict_['date'] = str(datetime.strptime(dict_['date'], '%d/%m/%y'))
        result.append(dict_)
    return {'matches': result, 'team_id': team_id, 'team': team_name}

async def hltv_updating_live(current_time: str, html):
    live_matches = html.find(class_='liveMatchesContainer')
    if not live_matches:
        logger.info('No live matches')
        await hltv_delete_live(current_time)
        return
    live_matches = live_matches.find(class_='liveMatches').find_all(class_='liveMatch-container')
    for match in tqdm(live_matches):
        links = match.find(class_='liveMatch').find_all('a')
        href = links[0]['href']
        match_info = await hltv_match_info('https://www.hltv.org' + href)
        if not match_info:
            logger.error(f'No match_info {href}')
            continue
        match_info['match_link'] = href
        match_info['analytics_link'] = links[1]['href']
        match_info['match_id'] = int(href.split('/')[2])
        match_info['current_time'] = current_time
        await hltv_update_live(match_info)
    await hltv_delete_live(current_time)

async def hltv_upcoming_events():
    html = await hltv_get_html(config('matches_upcoming'))
    current_time = str(datetime.utcnow())
    groups = html.find(class_='upcomingMatchesAll').find_all(class_='upcomingMatchesSection')
    for matches in tqdm(groups, desc='groups'):
        for match in tqdm(matches.find_all(class_='upcomingMatch'),
                          desc=matches.find(class_='matchDayHeadline').text):
            href = match.find('a')['href']
            match_info = await hltv_match_info('https://www.hltv.org' + href)
            if not match_info:
                logger.error(f'No match_info {href}')
                continue
            match_info['match_link'] = href
            match_info['match_id'] = int(href.split('/')[2])
            match_info['current_time'] = current_time
            await hltv_update_upcoming(match_info)
    await hltv_delete_upcoming(current_time)
    logger.info('Started updating live')
    await hltv_updating_live(current_time, html)

async def hltv_match_info(match_link: str):
    logger.info(match_link)
    html = await hltv_get_html(match_link)
    team_info = html.find(class_='standard-box teamsBox')
    teams = team_info.find_all(class_='team')
    start = team_info.find(class_='time')
    players = html.find(class_='lineups-compare-container')
    categs = html.find(class_='past-matches-grid')
    if categs:
        categs = categs.find_all(class_='past-matches-box text-ellipsis')
    else:
        categs = [[], []]
    bo = len(html.find(class_='g-grid maps').find_all(class_='mapholder'))

    result = {'teams': {}}
    for index, team in enumerate(teams):
        team_id = team.find('a')
        if not team_id or not team_id.find('img') or not team.find('img'):
            source = ''
            flag = ''
        else:
            source = team_id.find('img')['src']
            flag = team.find('img')['src']
        if team_id:
            team_id = team_id['href'].split('/')
            result['teams'][team_id[2]] = {'team': team_id[3], 'source': source, 'flag': flag}
        else:
            team_id = ['', '', str(index)]
            result['teams'][team_id[2]] = {'team': team.text.strip(), 'source': source, 'flag': flag}
            logger.info(f'No href data {match_link}')

        if index == 0:
            result['teams'][team_id[2]]['players'] = json.loads(players['data-team1-players-data']) if players else None
            result['teams'][team_id[2]]['past_matches'] = await hltv_past_matches(categs[0])
            continue

        result['teams'][team_id[2]]['players'] = json.loads(players['data-team2-players-data']) if players else None
        result['teams'][team_id[2]]['past_matches'] = await hltv_past_matches(categs[1])

    result['bo'] = bo
    result['start_time'] = str(datetime.utcfromtimestamp(int(start['data-unix']) / 1000))
    result['timestamp'] = int(start['data-unix'])
    return result

async def hltv_past_matches(category: str):
    if not category:
        return

    matches = category.find_all('tr')
    results = []
    for match in matches:
        match_link = match.find(class_='past-matches-score')
        if match_link:
            match_link = match_link.find('a')['href']
        fields = ['opponent', 'played', 'bo', 'score']
        data = match.text.strip().split('\n')
        data = list(filter(lambda x: x != '', data))
        past_3 = dict(zip(fields, data))
        if match.find(class_='past-matches-cell lost'):
            past_3['result'] = 'lose'
        else:
            past_3['result'] = 'win'
        past_3['link'] = match_link
        results.append(past_3)
    return results

async def hltv_match_score_total(match_link: str):
    html = await hltv_get_html(config('hltv_domain') + match_link)
    mapholders = html.find(class_='flexbox-column')
    players = html.find(class_='stats-content')

    if not players and mapholders:
        mapholder = mapholders.find_all(class_='mapholder')[0]
        # default_ = mapholder.find(class_='map-name-holder').find('img')['alt']
        # if default_ == 'Default':
        #     results = mapholder.find(class_='results played')
        #     team_0 = results.find(class_='results-left')['class']
        #     team_1 = results.find(class_='results-right')['class']
        #     if team_0[1] == 'won':
        #         return {'total_score': {'winner': 0}}
        #     return {'total_score': {'winner': 1}}
        results = mapholder.find(class_='results played')
        team_0 = results.find(class_='results-left')['class']
        team_1 = results.find(class_='results-right')['class']
        if team_0[1] == 'won':
            return {'total_score': {'winner': 0}}
        return {'total_score': {'winner': 1}}
    if not mapholders or not players:
        return

    mapholders = mapholders.find_all(class_='mapholder')
    players = players.find_all(class_='table totalstats')

    data = {}
    for index, mapholder in enumerate(mapholders):
        map_played = mapholder.find(class_='map-name-holder').find('img')
        data[str(index + 1)] = {'map': map_played['alt'], 'pic': map_played['src']}

        map_result = mapholder.find(class_='results played')
        if not map_result:
            data[str(index + 1)]['team_0'] = None
            data[str(index + 1)]['team_1'] = None
            data[str(index + 1)]['pick'] = 3
            continue
        team_left = map_result.find(class_='results-left')
        if team_left.find(class_='results-team-score').text.strip() == '-':
            logger.info('Match still in progress')
            return

        score = int(team_left.find(class_='results-team-score').text.strip())
        data[str(index + 1)]['team_0'] = {'score': score}
        team_right = map_result.find(class_='results-right')
        score = int(team_right.find(class_='results-team-score').text.strip())
        data[str(index + 1)]['team_1'] = {'score': score}

        if len(team_left['class']) == len(team_right['class']):
            data[str(index + 1)]['pick'] = 3
            continue
        elif len(team_left['class']) > len(team_right['class']):
            data[str(index + 1)]['pick'] = 0
            continue
        data[str(index + 1)]['pick'] = 1
    
    team_0 = team_1 = 0
    for map in data:
        if not data[map]['team_0'] or not data[map]['team_1']:
            continue
        if data[map]['team_0']['score'] > data[map]['team_1']['score']:
            team_0 += 1
            continue
        team_1 += 1

    if team_0 > team_1:
        data['total_score'] = {'score': [team_0, team_1], 'winner': 0}
    else:
        data['total_score'] = {'score': [team_0, team_1], 'winner': 1}

    for index, player in enumerate(players):
        team_data = player.find_all('tr')
        team_players = {}
        for team in team_data:
            if team['class'] == ['header-row']:
                continue
            href = team.find(class_='players').find('a')['href']
            name = href.split('/')[-1]
            team_players[name] = {}
            team_players[name]['player_link'] = href
            team_players[name]['kd'] = [
                int(value) for value in team.find(class_='kd text-center').text.strip().split('-')
            ]
            team_players[name]['kd_stat'] = team_players[name]['kd'][0] - team_players[name]['kd'][1]
            team_players[name]['adr'] = float(team.find(class_='adr text-center').text.strip())
            team_players[name]['kast_perc'] = float(team.find(class_='kast text-center').text.strip().replace('%', ''))
            team_players[name]['rating'] = float(team.find(class_='rating text-center').text.strip())
        data['players_after_' + str(index)] = team_players
    return data

async def hltv_teams_check_played(match_link: str):
    html = await hltv_get_html(config('hltv_domain') + match_link)
    match_ = html.find(class_='match-page')
    if not match_:
        return
    teams = match_.find(class_='standard-box teamsBox').find_all(class_='team')
    data = {'teams_current': {}}
    for index, team in enumerate(teams):
        srcs = team.find_all('img')
        flag = source = name = ''
        for inx, src in enumerate(srcs):
            if inx == 0:
                flag = src['src']
                continue
            source = src['src']
            name = src['alt'].lower()
        data['teams_current'][str(index)] = {'flag': flag, 'source': source, 'team': name}
    return data

async def hltv_team_rating(team_id: str):
    html = await hltv_get_html(config('stats_all_teams'))
    all_teams = html.find(class_='stats-table player-ratings-table').find('tbody').find_all('tr')
    for team in all_teams:
        tds = team.find_all('td')
        for td in tds:
            if td['class'][0] == 'teamCol-teams-overview':
                href = td.find('a')['href']
                if re.findall(r"\b" + re.escape(team_id) + r"\b", href, re.IGNORECASE):
                    return float(tds[4].text)
