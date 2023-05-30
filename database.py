import asyncio
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from decouple import config
from motor import motor_asyncio


client = motor_asyncio.AsyncIOMotorClient(config('URI'))
client.get_io_loop = asyncio.get_event_loop
db = client['HLTV']
db['actual_news'].create_index([('source_link', 1)], unique=True)
db['history_news'].create_index([('date', 1)], unique=True)
db['all_teams'].create_index([('team_id', 1)], unique=True)
db['all_players'].create_index([('player_id', 1)], unique=True)
db['overview_data'].create_index([('player_id', 1)], unique=True)
db['matches'].create_index([('team_id', 1)], unique=True)
db['upcoming'].create_index([('match_id', 1)], unique=True)
db['live'].create_index([('match_id', 1)], unique=True)
db['all_played'].create_index([('match_id', 1)], unique=True)


async def htlv_actual_news_update(result: dict):
    current_time = str(datetime.utcnow())
    async with await client.start_session() as session:
        for item in result:
            for data in result[item]:
                await db['actual_news'].find_one_and_update(
                    {'source_link': data['source_link']},
                    {'$set': {
                        'title': data['title'],
                        'time': data['time'],
                        'title_time': data['title_time'],
                        'current_time': current_time,
                        'type': item
                    }},
                    upsert=True,
                    session=session
                )
        await db['actual_news'].delete_many({'current_time': {'$ne': current_time}},
                                            {},
                                            session=session)

async def hltv_all_news_update(result: dict, year: str, month: str):
    date = f'{year}-{month}'
    if not result[date]:
        return
    async with await client.start_session() as session:
        await db['history_news'].find_one_and_update(
            {'date': date},
            {'$set': {'date': date, 'year': year, 'month': month,'data': result[date]}},
            upsert=True,
            session=session
        )

async def htlv_all_players_update(team_data: dict):
    team_data['maps'] = int(team_data['maps'])
    team_data['kd_diff'] = int(team_data['kd_diff'])
    team_data['kd'] = float(team_data['kd'])
    team_data['rating'] = float(team_data['rating'])
    team_data['total_kills'] = int(team_data['total_kills'])
    team_data['total_deaths'] = int(team_data['total_deaths'])
    team_data['rounds_played'] = int(team_data['rounds_played'])
    async with await client.start_session() as session:
        await db['all_teams'].find_one_and_update(
            {'team_id': team_data['team_id']},
            {'$set': team_data},
            upsert=True,
            session=session
        )

async def htlv_all_players_delete(current_time: str):
    async with await client.start_session() as session:
        items = await db['all_teams'].delete_many(
            {'current_time': {'$ne': current_time}},
            {},
            session=session
        )
    return items.deleted_count

async def hltv_get_teammates():
    async with await client.start_session() as session:
        teammates = await db['all_teams'].find(
            {'teammates': {'$ne': {}}},
            projection={'_id': 0, 'teammates': 1},
            session=session
        ).to_list(length=None)
    return teammates

async def hltv_get_teams():
    async with await client.start_session() as session:
        teams = await db['all_teams'].find(
            {},
            projection={'_id': 0, 'team_id': 1, 'team': 1},
            session=session
        ).to_list(length=None)
    return teams

async def hltv_get_team(team_id: str):
    async with await client.start_session() as session:
        team = await db['all_teams'].find_one(
            {'team_id': team_id},
            projection={'_id': 0},
            session=session
        )
    return team

async def hltv_players_update(overview: dict, graph_data: dict):
    async with await client.start_session() as session:
        await db['all_players'].find_one_and_update(
            {'player_id': overview['player_id']},
            {'$set': overview},
            upsert=True,
            session=session
        )
        await db['overview_data'].find_one_and_update(
            {'player_id': graph_data['player_id']},
            {'$set': graph_data},
            upsert=True,
            session=session
        )

async def hltv_update_matches(result: dict):
    async with await client.start_session() as session:
        await db['matches'].find_one_and_update(
            {'team_id': result['team_id']},
            {'$set': result},
            upsert=True,
            session=session
        )

async def hltv_update_live(result: dict):
    async with await client.start_session() as session:
        await db['live'].find_one_and_update(
            {'match_id': result['match_id']},
            {'$set': result},
            upsert=True,
            session=session
        )

async def hltv_update_upcoming(result: dict):
    async with await client.start_session() as session:
        await db['upcoming'].find_one_and_update(
            {'match_id': result['match_id']},
            {'$set': result},
            upsert=True,
            session=session
        )

async def hltv_get_upcoming():
    async with await client.start_session() as session:
        result = await db['upcoming'].find(
            {},
            {
                '_id': 0,
            },
            session=session
        ).to_list(length=None)
    return result

async def hltv_delete_upcoming(current_time):
    async with await client.start_session() as session:
        deleted_upcoming = await db['upcoming'].find(
            {'current_time': {'$ne': current_time}},
            {'_id': 0, 'current_time': 0},
            session=session
        ).to_list(length=None)
        await db['upcoming'].delete_many(
            {'current_time': {'$ne': current_time}},
            {},
            session=session
        )
        for deleted in deleted_upcoming:
            await db['all_played'].find_one_and_update(
                {'match_id': deleted['match_id']},
                {'$set': deleted},
                upsert=True,
                session=session
            )

async def hltv_delete_live(current_time):
    async with await client.start_session() as session:
        deleted_live = await db['live'].find(
            {'current_time': {'$ne': current_time}},
            {'_id': 0, 'current_time': 0},
            session=session
        ).to_list(length=None)
        await db['live'].delete_many(
            {'current_time': {'$ne': current_time}},
            {},
            session=session
        )
        for deleted in deleted_live:
            await db['all_played'].find_one_and_update(
                {'match_id': deleted['match_id']},
                {'$set': deleted},
                upsert=True,
                session=session
            )

async def hltv_get_all_played():
    async with await client.start_session() as session:
        all_played = await db['all_played'].find(
            {'total_score': {'$eq': None}},
            {'_id': 0},
            session=session
        ).to_list(length=None)
    if not all_played:
        return
    return all_played

async def hltv_update_all_played(match_id: int, data: dict):
    async with await client.start_session() as session:
        await db['all_played'].find_one_and_update(
            {'match_id': match_id},
            {'$set': data},
            upsert=True,
            session=session
        )
