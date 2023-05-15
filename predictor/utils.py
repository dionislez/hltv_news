from typing import Optional

from decouple import config
from pymongo import MongoClient, DESCENDING, ASCENDING


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

def get_upcoming_events():
    all_events = list(connect('upcoming').find().sort('timestamp', ASCENDING))
    if not all_events:
        return
    for events in all_events:
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''
    return all_events

def get_live_events():
    all_events = list(connect('live').find().sort('timestamp', ASCENDING))
    if not all_events:
        return
    for events in all_events:
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''
    return all_events