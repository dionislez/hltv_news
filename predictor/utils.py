from pprint import pprint
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
        events['start_time'] = events['start_time'][:-3]
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
        events['start_time'] = events['start_time'][:-3]
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''
    return all_events

def get_played_events():
    all_events = list(connect('parsed_data', 'all_played').find({'total_score': {'$ne': None}}).sort('timestamp', DESCENDING))
    if not all_events:
        return
    for index, events in enumerate(all_events):
        events['start_time'] = events['start_time'][:-3]
        if events['teams']:
            for index, item in enumerate(events['teams']):
                if events['teams'][item]['team'] == events['teams_current'][str(index)]:
                    events['teams_current'][str(index)] = {
                        'source': events['teams'][item]['source'],
                        'flag': events['teams'][item]['flag'],
                        'team': events['teams_current'][str(index)]
                    }
        for item in events['teams_current']:
            if events['teams_current'][item]['source'] == '/img/static/team/placeholder.svg':
                events['teams_current'][item]['source'] = ''
        event_checker_all_played(events)
    return all_events

def event_checker_all_played(events: dict):
    if not events['total_score'].get('score'):
        events['total_score']['score'] = [0, 0]
        events['total_score']['score'][events['total_score']['winner']] = 1

    if not events['teams']:
        for index, score in enumerate(events['total_score']['score']):
            events[f'team_{index}'] = {'color': 'red', 'score': score}
            if events['total_score']['winner'] == index:
                events[f'team_{index}']['color'] = 'green'
        return

    for index, event in enumerate(events['teams']):
        events[f'team_{index}'] = events['teams'][event]
        if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
            events[f'team_{index}']['source'] = ''

        if not events['total_score'].get('score'):
            events[f'team_{index}'] = {'score': 0, 'color': 'red'}
            if events['total_score']['winner'] == index:
                events[f'team_{index}']['score'] = 1
                events[f'team_{index}']['color'] = 'green'
            continue

        events[f'team_{index}']['score'] = events['total_score']['score'][index]
        if events['total_score']['winner'] == index:
            events[f'team_{index}']['color'] = 'green'
        else:
            events[f'team_{index}']['color'] = 'red'

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
        if collection == 'all_played':
            found = list(found)
            for event in found:
                event_checker_all_played(event)
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
        events['start_time'] = events['start_time'][:-3]
        for index, event in enumerate(events['teams']):
            events[f'team_{index}'] = events['teams'][event]
            if events[f'team_{index}']['source'] == '/img/static/team/placeholder.svg':
                events[f'team_{index}']['source'] = ''

    return results

def get_match_stats(match_id: int, collection: str):
    if collection == 'all':
        match_stats = None
        for collection in ['all_played', 'upcoming', 'live']:
            match_stats = connect('parsed_data', collection).find_one({'match_id': match_id}, {'_id': 0})
            if match_stats:
                break
    else:
        match_stats = connect('parsed_data', collection).find_one({'match_id': match_id}, {'_id': 0})
    if not match_stats:
        return
    data = {'bo': match_stats['bo'], 'overview_data' : {}}
    for index, team in enumerate(match_stats['teams']):
        data[f'team_{index}'] = {'team_id': team,
                                 'team': match_stats['teams'][team]['team'],
                                 'flag': match_stats['teams'][team]['flag'],
                                 'source': match_stats['teams'][team]['source'],
                                 'players': match_stats['teams'][team]['players'],
                                 'past_matches': match_stats['teams'][team]['past_matches']}
        if match_stats['teams'][team]['source'] == '/img/static/team/placeholder.svg':
            data[f'team_{index}']['source'] = ''
        if not data[f'team_{index}']['players']:
            continue
        for player in data[f'team_{index}']['players']:
            overview_data = get_overview_data(player)
            overview_data.update(get_career_data(player))
            data['overview_data'][player] = overview_data

    if not match_stats['teams'] and match_stats.get('teams_current'):
        for item in match_stats['teams_current']:
            data[f'team_{item}'] = match_stats['teams_current'][item]
    return data

def get_overview_data(player_id: str):
    graph_data = connect('parsed_data', 'overview_data').find_one(
        {'player_id': player_id},
        {'_id': 0, 'data': 1}
    )
    labels, ratings = [], []
    if not graph_data:
        return {'labels': labels, 'data': ratings}
    for element in graph_data['data']:
        if element['label'] not in labels and element['value']:
            labels.append(element['label'])
            ratings.append(float(element['value']))
    return {'labels': labels, 'data': ratings}

def get_career_data(player_id: str):
    graph_data = connect('parsed_data', 'all_players').find_one(
        {'player_id': player_id},
        {'_id': 0, 'career': 1}
    )
    labels, career = [], []
    if not graph_data:
        return {'labels_2': labels, 'data_2': career}
    for element in graph_data['career']:
        for type in graph_data['career'][element]:
            labels.append(f'{element} {type.upper()}')
            career.append(graph_data['career'][element][type])
    return {'labels_2': labels, 'data_2': career}

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
    
    if len(favourites['favourites'][category]) >= 30:
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
