import asyncio
import os
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from database import hltv_get_teammates, hltv_players_update
from hltv_org import hltv_stats_player

LIMIT_PARSER = 3


async def chunk_players(teammates: list, length_: int, elements: int):
    for index in tqdm(range(23, length_, elements), desc='all players'):
        yield teammates[index:index + elements]

async def parsing_teammates():
    teammates_group = await hltv_get_teammates()

    if not teammates_group:
        logger.info('No teammates')
        return

    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    
    if not os.path.exists('./logs/logs_players.txt'):
        with open('./logs/logs_players.txt', 'w') as _:
            pass

    length_ = len(teammates_group)
    current_time = str(datetime.utcnow())

    async for chunck in chunk_players(teammates_group, length_, LIMIT_PARSER):
        coroutines = [
            hltv_stats_player(
                player_id,
                group['teammates'][player_id]['nikname'].lower().replace(' ', '-')
            ) for group in chunck for player_id in group['teammates']
        ]

        tasks = []
        for coro in coroutines:
            task = asyncio.create_task(coro)
            tasks.append(task)
        
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            player_stats = await future
            if not player_stats:
                continue
            if not player_stats[1]:
                player_stats[1] = {'data': []}
            player_stats[0]['player_id'] = player_stats[2]
            player_stats[0]['current_time'] = current_time
            player_stats[1]['player_id'] = player_stats[2]
            player_stats[1]['current_time'] = current_time
            await hltv_players_update(player_stats[0], player_stats[1])
    await check_logs(current_time)

async def check_logs(current_time: str):
    with open('./logs/logs_players.txt', 'r') as file:
        players = file.readlines()

    error_parsed = []
    for player in tqdm(players, desc='updatind logs_players'):
        arguments = player.replace('\n', '').split(',')
        result = await hltv_stats_player(arguments[0], arguments[1])

        if not result:
            error_parsed.append(player)
            continue

        if not result[1]:
            result[1] = {'data': []}
        
        result[0]['player_id'] = result[2]
        result[0]['current_time'] = current_time
        result[1]['player_id'] = result[2]
        result[1]['current_time'] = current_time
        await hltv_players_update(result[0], result[1])

    with open('./logs/logs_matches.txt', 'w') as file:
        file.writelines(error_parsed)

if __name__ == '__main__':
    try:
        asyncio.run(parsing_teammates())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')