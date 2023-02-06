import asyncio
from datetime import datetime

from database import hltv_all_news_update
from htlv_org import hltv_history_news


async def hltv_all_news_parsing():
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    year = 2005

    while year != datetime.utcnow().year + 1:
        for month in months:
            result = await hltv_history_news(year, month)
            await hltv_all_news_update(result, str(year), month)
            await asyncio.sleep(5)
        year += 1


if __name__ == '__main__':
    asyncio.run(hltv_all_news_parsing())