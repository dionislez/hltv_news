import asyncio

from loguru import logger

from hltv_org import hltv_upcoming_events


if __name__ == '__main__':
    try:
        asyncio.run(hltv_upcoming_events())
    except KeyboardInterrupt:
        logger.info('[The script was interrupted by keyboard]')