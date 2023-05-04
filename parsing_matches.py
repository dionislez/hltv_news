import asyncio
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from database import hltv_get_teams, hltv_update_matches
from hltv_org import hltv_team_matches


async def limit_matches(teams: list, length_: int, elements: int):

    for index in range(0, length_, elements):
        yield teams[index:index + elements]

    # for team in range(0, length_ + 1, 100):
    #     print(team)
        # logger.info(f'{team["team_id"]} - {team["team"]}')
        # result = {'current_time': current_time, 'team_id': team['team_id'], 'team': team['team']}
        # matches = await hltv_team_matches(team['team_id'], team['team'].lower().replace(' ', '-'))
        # result['matches'] = matches
        # await hltv_update_matches(result)
    # logger.info('Parsed all data from all_teams collection')

async def get_matches():
    teams = await hltv_get_teams()
    if not teams:
        logger.info('No teams')
        return
    
    current_time = str(datetime.utcnow())
    length_ = len(teams)
    
    async for chuncked_teams in limit_matches(teams, length_, 100):
        coroutines = [hltv_team_matches(team['team_id'], team['team'].lower().replace(' ', '-')) for team in chuncked_teams]
        results = await asyncio.gather(*coroutines)
    
    logger.info('Parsed all data from all_teams collection')

if __name__ == '__main__':
    try:
        asyncio.run(get_matches())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')
