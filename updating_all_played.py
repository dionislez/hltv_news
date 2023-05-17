import asyncio

from loguru import logger
from tqdm import tqdm

from database import hltv_get_all_played, hltv_update_all_played
from hltv_org import hltv_match_score_total


async def updating_all_played():
    all_played = await hltv_get_all_played()
    if not all_played:
        logger.info('No matches to update total score')
        return
    for match in tqdm(all_played):
        logger.info(match['match_link'])
        data = await hltv_match_score_total(match['match_link'])
        if not data:
            logger.info(f'No data - {match["match_link"]}')
            continue
        await hltv_update_all_played(match['match_id'], data)
    logger.info(f'Updated stats in for {len(all_played)} matches')

if __name__ == '__main__':
    try:
        asyncio.run(updating_all_played())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')