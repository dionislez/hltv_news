import asyncio
import os
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from database import hltv_get_teams, hltv_update_matches
from hltv_org import hltv_team_matches

LIMIT_PARSER = 20


async def limit_matches(teams: list, length_: int, elements: int):
    for index in tqdm(range(0, length_, elements), desc='all items'):
        yield teams[index:index + elements]

async def get_matches():
    teams = await hltv_get_teams()
    if not teams:
        logger.info('No teams')
        return
    
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    
    if not os.path.exists('./logs/logs_matches.txt'):
        with open('./logs/logs_matches.txt', 'w') as _:
            pass

    current_time = str(datetime.utcnow())
    length_ = len(teams)
    
    async for chuncked_teams in limit_matches(teams, length_, LIMIT_PARSER):
        coroutines = [hltv_team_matches(
            team['team_id'], 
            team['team'].lower().replace(' ', '-')
        ) for team in chuncked_teams]

        tasks = []
        for coro in coroutines:
            task = asyncio.create_task(coro)
            tasks.append(task)

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            result = await future
            if not result:
                continue
            result['current_time'] = current_time
            await hltv_update_matches(result)
    
    await check_logs(current_time)
    logger.info('Parsed all data from all_teams collection')

async def check_logs(current_time: str):
    with open('./logs/logs_matches.txt', 'r') as file:
        teams = file.readlines()

    error_parsed = []
    for team in tqdm(teams, desc='updatind logs_matches'):
        arguments = team.replace('\n', '').split(',')
        result = await hltv_team_matches(arguments[0], arguments[1])

        if not result:
            error_parsed.append(team)
            continue

        result['current_time'] = current_time
        await hltv_update_matches(result)
    
    with open('./logs/logs_matches.txt', 'w') as file:
        file.writelines(error_parsed)

if __name__ == '__main__':
    try:
        asyncio.run(get_matches())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')
