from typing import Optional

from decouple import config
from pymongo import MongoClient, DESCENDING


def connect(collection: str) -> MongoClient:
    return MongoClient(config('URI'))[config('DB_NAME')][collection]

def get_news(type: str) -> Optional[list]:
    all_news = list(connect('actual_news').find(
        filter={'type': type},
        projection={'_id': 0}).sort('title_time', DESCENDING))
    if not all_news:
        return
    return all_news

def get_news_archive(date: str) -> Optional[list]:
    all_news = connect('history_news').find_one(
        {f'data.{date}': {'$exists': True}},
        {'_id': 0})
    if not all_news:
        return
    return all_news['data'][str(date)]