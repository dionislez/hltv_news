from typing import Optional

from decouple import config
from loguru import logger
from pymongo import ASCENDING, DESCENDING, MongoClient


def connect(client: str, collection: str) -> MongoClient:
    clients = {
        'django_data': config('DB_NAME_DJ'),
        'parsed_data': config('DB_NAME')
    }
    return MongoClient(config('URI'))[clients[client]][collection]

def get_news(type: str) -> Optional[list]:
    all_news = list(connect('parsed_data', 'actual_news').find(
        filter={'type': type},
        projection={'_id': 0}).sort('title_time', DESCENDING))
    if not all_news:
        return
    return all_news

def get_news_archive(date: str) -> Optional[list]:
    all_news = connect('parsed_data', 'history_news').find_one(
        {f'data.{date}': {'$exists': True}},
        {'_id': 0})
    if not all_news:
        return
    return all_news['data'][str(date)]

def get_upcoming_events():
    all_events = list(connect('parsed_data', 'upcoming').find().sort('timestamp', ASCENDING))
    if not all_events:
        return
    for events in all_events:
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''
    return all_events

def get_live_events():
    all_events = list(connect('parsed_data', 'live').find().sort('timestamp', ASCENDING))
    if not all_events:
        return
    for events in all_events:
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''
    return all_events

def get_user_favourites(username: str, email: str, category: str):
    connect_ = connect('django_data', 'auth_user')
    favourites = connect_.find_one(
        {'username': username, 'email': email},
        {'_id': 0, 'favourites': 1}
    )
    if not favourites or not favourites['favourites'].get(category) or not favourites['favourites'][category]:
        return

    results, found_ids = [], set()
    for collection in ['upcoming', 'live', 'all_played']:
        found = connect('parsed_data', collection).aggregate(
            [{'$match': {'match_id': {'$in': favourites['favourites'][category]}}}]
        )
        results.extend(found)
        found_ids.update(match['match_id'] for match in results)

    results = sorted(results, key=lambda x: x['timestamp'])
    not_found_ids = set(favourites['favourites'][category]) - found_ids
    if not_found_ids:
        for id_ in not_found_ids:
            favourites['favourites'][category].remove(id_)
        connect_.find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        logger.info('Not found and deleted '
                    f'{len(not_found_ids)} - '
                    f'{category} ({username}, {email})')

    for events in results:
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''

    return results

def updating_favourites(username: str, email: str, category: str, match_id: int):
    connect_ = connect('django_data', 'auth_user')
    favourites = connect_.find_one(
        {'username': username, 'email': email},
        {'_id': 0, 'favourites': 1}
    )
    if not favourites:
        favourites = {'favourites': {category: [match_id]}}
        connect_.find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        return True, f'Added {match_id} Match'

    if not favourites['favourites'].get(category):
        favourites['favourites'][category] = [match_id]
        connect_.find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        return True, f'Added {match_id} Match'
    
    if match_id in favourites['favourites'][category]:
        return False, 'Already Added'
    
    if len(favourites['favourites'][category]) > 30:
        return False, f'Limit 30 For {category.capitalize()} Matches'

    favourites['favourites'][category].insert(0, match_id)
    connect_.find_one_and_update(
        {'username': username, 'email': email},
        {'$set': favourites},
        upsert=True,
    )
    return True, f'Added {match_id} Match'

def deleting_favourites_upcoming(username: str, email: str, category: str, match_id: int):
    connect_ = connect('django_data', 'auth_user')
    favourites = connect_.find_one(
        {'username': username, 'email': email},
        {'_id': 0, 'favourites': 1}
    )

    if not favourites or not favourites['favourites'].get(category):
        return

    if match_id not in favourites['favourites'][category]:
        return

    favourites['favourites'][category].remove(match_id)
    connect_.find_one_and_update(
        {'username': username, 'email': email},
        {'$set': favourites},
        upsert=True,
    )
    return
