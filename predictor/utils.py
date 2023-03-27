from typing import Optional

from decouple import config
from pymongo import MongoClient


def connect(collection: str) -> MongoClient:
    return MongoClient(config('URI'))[config('DB_NAME')][collection]

def get_news(type: str) -> Optional[list]:
    all_news = list(connect('actual_news').find(
        {'type': type},
        {'_id': 0})
    )
    if not all_news:
        return
    return all_news