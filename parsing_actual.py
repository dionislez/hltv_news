import asyncio

from loguru import logger

from database import htlv_actual_news_update
from htlv_org import hltv_actual_news


async def hltv_actual_news_parsing():
    result = await hltv_actual_news()
    if not result:
        return

    await htlv_actual_news_update(result)
    logger.info('[parsed actual news from www.hltv.org]')


async def gathering_tasks():
    tasks = [hltv_actual_news_parsing()]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(gathering_tasks())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')
