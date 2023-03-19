import asyncio
from datetime import datetime

from loguru import logger

from database import htlv_all_players_delete
from htlv_org import hltv_stats_teams


async def parsing_teams():
    current_time = datetime.utcnow()
    found = await hltv_stats_teams(current_time)
    if not found:
        return
    deleted = await htlv_all_players_delete(str(current_time))
    logger.info(f'Added actual info of teams for {current_time.year}'
                f'\n{deleted} teams deleted')


if __name__ == '__main__':
    try:
        asyncio.run(parsing_teams())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')