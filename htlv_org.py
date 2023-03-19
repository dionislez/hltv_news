import asyncio
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

from database import htlv_all_players_update


HTLV_LINKS = {'actual_news': 'https://www.hltv.org',
              'history_news': 'https://www.hltv.org/news/archive/{year}/{month}',
              'stats_teams': ('https://www.hltv.org/stats/teams'
                              '?startDate={year}-01-01&endDate={year}-12-31'
                              '&minMapCount=0'),
              'stats_team': ('https://www.hltv.org/stats/teams/{team_id}'
                             '/natus-vincere?startDate={year}-01-01'
                             '&endDate={year}-12-31'),
              'matches_team': ('https://www.hltv.org/stats/teams/'
                               'matches/{team_id}/{team_name}?startDate=all')}
HLTV_MONTH = {'01': 'january', '02': 'february', '03': 'march', '04': 'april',
              '05': 'may', '06': 'june', '07': 'july', '08': 'august',
              '09': 'september', '10': 'october', '11': 'november', '12': 'december'}
DRIVER_OPTIONS = ['--log-level=1', 'headless', ('user-agent=Mozilla/5.0 '
                                                '(Windows NT 10.0; Win64; x64)'
                                                ' AppleWebKit/537.36 (KHTML, '
                                                'like Gecko) Chrome/111.0.0.0'
                                                ' Safari/537.36')]


async def hltv_get_html(link: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=link) as response:
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


async def hltv_actual_news():
    html = await hltv_get_html(HTLV_LINKS['actual_news'])
    if not html:
        return

    category_news = html.find_all(class_='standard-box standard-list')
    type_news = html.find_all('h2')[:3]

    result_dict = dict()
    for index, category in enumerate(category_news):
        news = category.find_all('a')
        result_dict[type_news[index].text] = list()
        for item in news:
            data = item.text.strip().replace('\n\n', '\n').split('\n')
            result_dict[type_news[index].text].append(
                {
                    'title': data[0].replace("'", '`'),
                    'time': data[1],
                    'source_link': HTLV_LINKS['actual_news'] + item['href']
                }
            )
    return result_dict


async def hltv_history_news(year: str, month: str):
    link = HTLV_LINKS['history_news'].format(year=year, month=HLTV_MONTH[month])
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
                'source_link': HTLV_LINKS['actual_news'] + item['href']
            }]
            continue
        result_dict[f'{year}-{month}'][data[1]].append(
            {
                'title': data[0].replace("'", '`'),
                'source_link': HTLV_LINKS['actual_news'] + item['href']
            }
        )
    return result_dict


async def hltv_stats_teams(current_time: datetime):
    team_fields = ['team', 'maps', 'kd_diff', 'kd', 'rating', 'team_id', 'location'] 
    html = await hltv_get_html(HTLV_LINKS['stats_teams'].format(year=current_time.year))
    if not html:
        return

    teams = html.find(class_='stats-table player-ratings-table').find('tbody').find_all('tr')
    for team in tqdm(teams, desc='loop for teams of 2023'):
        team_data = team.text.strip().split('\n')
        team_data.append(team.find('a')['href'].split('/')[-2])
        team_data.append(team.find('img')['title'])
        team_data = dict(zip(team_fields, team_data))
        await hltv_stats_by_team(team_data, current_time.year)
        await asyncio.sleep(5)
        team_data['current_time'] = str(current_time)
        await htlv_all_players_update(team_data)
        logger.info(f'{team_data["team_id"]}: {team_data["team"]}')


async def hltv_stats_by_team(team_data: dict, year: int):
    html = await hltv_get_html(
        HTLV_LINKS['stats_team'].format(team_id=team_data['team_id'],
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


if __name__ == '__main__':
    asyncio.run(hltv_stats_teams(datetime.utcnow()))
