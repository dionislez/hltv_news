import asyncio
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from database import hltv_get_teammates, hltv_players_update
from hltv_org import hltv_stats_player


async def parsing_teammates():
    teammates_group = await hltv_get_teammates()
    if not teammates_group:
        logger.info('No teammates')
        return
    current_time = str(datetime.utcnow())
    for group in tqdm(teammates_group, desc='updating players info'):
        for player_id in group['teammates']:
            logger.info(f"{player_id}")
            player_stats = await hltv_stats_player(
                player_id,
                group['teammates'][player_id]['nikname'].lower().replace(' ', '-')
            )
            if not player_stats[1]:
                player_stats[1] = {'data': []}
            player_stats[0]['player_id'] = player_id
            player_stats[0]['current_time'] = current_time
            player_stats[1]['player_id'] = player_id
            player_stats[1]['current_time'] = current_time
            await hltv_players_update(player_stats[0], player_stats[1])

if __name__ == '__main__':
    try:
        asyncio.run(parsing_teammates())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')