from pprint import pprint

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


HTLV_LINKS = {
    'actual_news': 'https://www.hltv.org',
    'history_news': 'https://www.hltv.org/news/archive/{year}/{month}'
}
HLTV_MONTH = {
    '01': 'january',
    '02': 'february',
    '03': 'march',
    '04': 'april',
    '05': 'may',
    '06': 'june',
    '07': 'july',
    '08': 'august',
    '09': 'september',
    '10': 'october',
    '11': 'november',
    '12': 'december'
}


async def hltv_get_html(link: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            if response.status != 200:
                logger.error(f'Status {link} = {response.status}')
            html = await response.text()

    soup = BeautifulSoup(html, 'lxml')
    return soup


async def hltv_actual_news():
    html = await hltv_get_html(HTLV_LINKS['actual_news'])
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
