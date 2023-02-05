from motor import motor_asyncio
from decouple import config


client = motor_asyncio.AsyncIOMotorClient(config('URI'))
db = client['HLTV']
db['news'].create_index([('', 1)], unique=True)


async def htlv_actual_news():
    ...


async def hltv_all_news():
    ...