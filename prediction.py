import asyncio
from database import hltv_get_upcoming, check_win_perc


async def main():
    matches = await hltv_get_upcoming()
    for match in matches:
        if not match['teams']:
            continue

        filter_ = {}
        for team in match['teams']:
            past_matches = []
            filter_[match['teams'][team]['team']] = {}

            for past in match['teams'][team]['past_matches']:
                score = past['bo'].split(' - ') if not past.get('score') else past['score'].split(' - ')
                score = [int(x) for x in score]
                if sum(score) > 5:
                    score = [1, 0] if past['result'] == 'win' else [0, 1]
                past_matches.append(score)
            
            filter_[match['teams'][team]['team']]['players'] = {}
            for player in match['teams'][team]['players']:
                filter_[
                    match['teams'][team]['team']
                ][
                    'players'
                ][
                    match['teams'][team]['players'][player]['nickname']
                ] = [
                    match['teams'][team]['players'][player]['numericAdr'],
                    match['teams'][team]['players'][player]['numericDpr'],
                    match['teams'][team]['players'][player]['numericImpact'],
                    match['teams'][team]['players'][player]['numericKast'],
                    match['teams'][team]['players'][player]['numericKpr'],
                    match['teams'][team]['players'][player]['numericRating']
                ]

            filter_[match['teams'][team]['team']]['scores'] = past_matches
        await data_check(filter_)
        return

async def data_check(data: dict):
    result = {}
    for team in data:
        result[team] = {}
        sum_ = 0
        for score in data[team]['scores']:
            if score[0] > score[1]:
                sum_ += 1
        result[team]['%_wins'] = (sum_ / len(data[team]['scores'])) * 100
    print(result)

async def win_perc():
    played = await check_win_perc()
    matches, wins, losses, draws = 0, 0, 0, 0
    for match in played:
        if not match['prediction'] or not 'total_score' in match or not match['total_score']:
            continue

        team_names = []
        for _, team in match['teams'].items():
            team_names.append(team['team'])

        winner = team_names[match['total_score']['winner']]
        if match['prediction'][winner] > 50:
            wins += 1
        elif match['prediction'][winner] == 50:
            draws += 1
        else:
            losses += 1
        matches += 1

    win_percentage = (wins / (wins + losses + draws)) * 100
    print(f'Total prognosed matches: {matches}\n'
          f'Total wins: {wins}\n'
          f'Total losses: {losses}\n'
          f'Total draws: {draws}\n'
          f'Accuracy: {round(win_percentage)}%')

if __name__ == '__main__':
    asyncio.run(win_perc())