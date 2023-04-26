import asyncio
import os
from datetime import datetime

from loguru import logger

from database import hltv_all_news_update
from hltv_org import hltv_history_news


async def hltv_all_news_parsing():
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    year = 2005

    if not os.path.exists('./logs'):
        os.mkdir('./logs')

    if not os.path.exists('./logs/logs_news_history.txt'):
        with open('./logs/logs_news_history.txt', 'w') as _:
            pass
    else:
        with open('./logs/logs_news_history.txt', 'r') as file:
            year = int(file.read())

    current_time = datetime.utcnow()
    while year != current_time.year + 1:
        for month in months:
            with open('./logs/logs_news_history.txt', 'w') as file:
                file.write(f'{year}')
            result = await hltv_history_news(year, month)
            if not result:
                return

            await hltv_all_news_update(result, str(year), month)
            await asyncio.sleep(5)
        year += 1


if __name__ == '__main__':
    try:
        asyncio.run(hltv_all_news_parsing())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')