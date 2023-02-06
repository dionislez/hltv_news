import asyncio
from htlv_org import hltv_actual_news
from database import htlv_actual_news_update


async def hltv_actual_news_parsing():
    result = await hltv_actual_news()
    await htlv_actual_news_update(result)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(hltv_actual_news_parsing())