import re
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
        
        if events.get('prediction') and events['prediction']:
            for id_ in events['teams']:
                events['teams'][id_]['pred'] = events['prediction'][events['teams'][id_]['team']]
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
        
        if events.get('prediction') and events['prediction']:
            for id_ in events['teams']:
                events['teams'][id_]['pred'] = events['prediction'][events['teams'][id_]['team']]
    return all_events

def get_played_events():
    all_events = list(connect('parsed_data', 'all_played').find({'total_score': {'$ne': None}}).sort('timestamp', DESCENDING))
    if not all_events:
        return
    for index, events in enumerate(all_events):
        events['start_time'] = events['start_time'][:-3]
        if events['teams']:
            for index, item in enumerate(events['teams']):
                team_ = events['teams'][item]['team']
                current_ = events['teams_current'][str(index)]
                team_name = events['teams_current'][str(index)]
                if isinstance(current_, dict):
                    team_name = events['teams_current'][str(index)]['team']
                    current_ = current_['team']
                if team_.find(current_) != -1 or current_.find(team_):
                    events['teams_current'][str(index)] = {
                        'source': events['teams'][item]['source'],
                        'flag': events['teams'][item]['flag'],
                        'team': team_name
                    }
        for item in events['teams_current']:
            if events['teams_current'][item]['source'] == '/img/static/team/placeholder.svg':
                events['teams_current'][item]['source'] = ''
        event_checker_all_played(events)
    return all_events

def event_checker_all_played(events: dict):
    if events.get('prediction') and events['prediction']:
            for id_ in events['teams']:
                events['teams'][id_]['pred'] = events['prediction'][events['teams'][id_]['team']]

    if events.get('total_score'):
        if (not events['total_score'].get('score') or
            events['total_score']['score'][0] == events['total_score']['score'][1]
        ):
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

        if not events.get('total_score'):
            continue

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

def check_favourites(username: str, email: str, category: str):
    connect_ = connect('django_data', 'auth_user')
    favourites = connect_.find_one(
        {'username': username, 'email': email},
        {'_id': 0, 'favourites': 1}
    )
    if not favourites or not favourites['favourites'].get(category) or not favourites['favourites'][category]:
        return
    return favourites

def get_user_favourites_players(username: str, email: str, category: str):
    favourites = check_favourites(username, email, category)
    if not favourites:
        return

    favourites_str = list(map(str, favourites['favourites'][category]))
    players = list(connect('parsed_data', 'all_players').find(
        {'player_id': {'$in': favourites_str}}, {'_id': 0}
    ))

    found_ids = []
    connect_ = connect('parsed_data', 'all_teams')
    for player in players:
        nickname = connect_.find_one(
            {f'teammates.{player["player_id"]}': {'$ne': None}}
        )['teammates'][player["player_id"]]['nikname']
        player['nickname'] = nickname
        found_ids.append(int(player["player_id"]))

    not_found_ids = set(favourites['favourites'][category]) - set(found_ids)
    if not_found_ids:
        for id_ in not_found_ids:
            favourites['favourites'][category].remove(id_)
        connect('django_data', 'auth_user').find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        logger.info('Not found and deleted '
                    f'{len(not_found_ids)} - '
                    f'{category} ({username}, {email})')
    return players

def get_user_favourites_teams(username: str, email: str, category: str):
    favourites = check_favourites(username, email, category)
    if not favourites:
        return

    favourites_str = list(map(str, favourites['favourites'][category]))
    teams = list(connect('parsed_data', 'all_teams').find(
        {'team_id': {'$in': favourites_str}}, {'_id': 0}
    ))

    found_ids = []
    for team in teams:
        found_ids.append(int(team['team_id']))

    not_found_ids = set(favourites['favourites'][category]) - set(found_ids)
    if not_found_ids:
        for id_ in not_found_ids:
            favourites['favourites'][category].remove(id_)
        connect('django_data', 'auth_user').find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        logger.info('Not found and deleted '
                    f'{len(not_found_ids)} - '
                    f'{category} ({username}, {email})')
    return teams

def get_user_favourites_upcoming(username: str, email: str, category: str):
    favourites = check_favourites(username, email, category)
    if not favourites:
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

    for event in results:
        if event.get('prediction') and event['prediction']:
            for id_ in event['teams']:
                event['teams'][id_]['pred'] = event['prediction'][event['teams'][id_]['team']]

    results = sorted(results, key=lambda x: x['timestamp'])
    not_found_ids = set(favourites['favourites'][category]) - found_ids
    if not_found_ids:
        for id_ in not_found_ids:
            favourites['favourites'][category].remove(id_)
        connect('django_data', 'auth_user').find_one_and_update(
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
    data = {'bo': match_stats['bo'], 'overview_data' : {}, 'match_id': match_stats['match_id']}
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
        return True, f'Added {match_id}'

    if not favourites['favourites'].get(category):
        favourites['favourites'][category] = [match_id]
        connect_.find_one_and_update(
            {'username': username, 'email': email},
            {'$set': favourites},
            upsert=True,
        )
        return True, f'Added {match_id}'
    
    if match_id in favourites['favourites'][category]:
        return False, 'Already Added'
    
    if len(favourites['favourites'][category]) >= 30:
        return False, f'Limit 30 For {category.capitalize()}'

    favourites['favourites'][category].insert(0, match_id)
    connect_.find_one_and_update(
        {'username': username, 'email': email},
        {'$set': favourites},
        upsert=True,
    )
    return True, f'Added {match_id}'

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

def get_all_players():
    all_players = list(connect('parsed_data', 'all_players').find({}, {'_id': 0}))
    connect_ = connect('parsed_data', 'all_teams')
    for player in all_players:
        player['nickname'] = connect_.find_one(
            {f'teammates.{player["player_id"]}': {'$ne': None}}
        )['teammates'][player["player_id"]]['nikname']
    return all_players

def get_all_player(player_id: int):
    player = connect('parsed_data', 'all_players').find_one({'player_id': player_id}, {'_id': 0})
    if not player:
        return {}

    team = connect('parsed_data', 'all_teams').find_one(
        {f'teammates.{player["player_id"]}': {'$ne': None}}
    )
    player['nickname'] = team['teammates'][player["player_id"]]['nikname']
    player['team_id'] = team['team_id']
    player['team'] = team['team']
    return player

def get_player_query(query: str):
    regex = re.compile(query, re.IGNORECASE)
    pipeline = [
        {
            "$addFields": {
                "teammatesArray": {"$objectToArray": "$teammates"}
            }
        },
        {
            "$match": {
                "$or": [
                    {"teammatesArray.k": {"$eq": query}},
                    {"teammatesArray.v.nikname": {"$regex": regex}}
                ]
            }
        },
        {
            "$project": {
                "_id": 0,
                "teammatesArray": 1
            }
        }
    ]
    player = list(connect('parsed_data', 'all_teams').aggregate(pipeline))
    if player:
        id_ = player[0]['teammatesArray'][0]['k']
        nikname = player[0]['teammatesArray'][0]['v']['nikname']
        for info in player[0]['teammatesArray']:
            if query == info['k']:
                id_ = info['k']
                nikname = info['v']['nikname']
                break
            if info['v']['nikname'].lower().find(query) != -1:
                id_ = info['k']
                nikname = info['v']['nikname']
                break
        all_data = connect('parsed_data', 'all_players').find_one(
            {'player_id': id_}
        )
        all_data['nickname'] = nikname
        return [all_data]
    return []

def get_teams():
    all_teams = list(connect('parsed_data', 'all_teams').find({}, {'_id': 0}))
    return all_teams

def get_team_query(query: str):
    regex = re.compile(query, re.IGNORECASE)
    pipeline = [
        {
            "$addFields": {
                "teammatesArray": {"$objectToArray": "$teammates"}
            }
        },
        {
            "$match": {
                "$or": [
                    {"team": {"$regex": regex}},
                    {"teammatesArray.v.nikname": {"$regex": regex}}
                ]
            }
        },
        {
            "$project": {
                "_id": 0,
                "team": 1,
                "team_id": 1
            }
        }
    ]
    team = list(connect('parsed_data', 'all_teams').aggregate(pipeline))
    if team:
        return [team[0]]
    return []

def get_all_team(team_id: str):
    team = connect('parsed_data', 'all_teams').find_one({'team_id': team_id}, {'_id': 0})
    if not team:
        return {}
    return team
