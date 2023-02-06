import asyncio
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from decouple import config
from motor import motor_asyncio


client = motor_asyncio.AsyncIOMotorClient(config('URI'))
client.get_io_loop = asyncio.get_event_loop
db = client['HLTV']
db['actual_news'].create_index([('title', 1)], unique=True)
db['history_news'].create_index([('date', 1)], unique=True)


async def htlv_actual_news_update(result: dict):
    current_time = str(datetime.utcnow())
    async with await client.start_session() as session:
        for item in result:
            for data in result[item]:
                await db['actual_news'].find_one_and_update(
                    {'title': data['title']},
                    {'$set': {
                        'title': data['title'],
                        'time': data['time'],
                        'current_time': current_time,
                        'source_link': data['source_link'],
                        'type': item
                    }},
                    upsert=True,
                    session=session
                )
        await db['actual_news'].delete_many(
            {'current_time': {'$ne': current_time}},
            {},
            session=session
        )


async def hltv_all_news_update(result: dict, year: str, month: str):
    date = f'{year}-{month}'
    if not result[date]:
        return
    async with await client.start_session() as session:
        await db['history_news'].find_one_and_update(
            {'date': date},
            {'$set': {
                'date': date,
                'year': year,
                'month': month,
                'data': result[date]
            }},
            upsert=True,
            session=session
        )