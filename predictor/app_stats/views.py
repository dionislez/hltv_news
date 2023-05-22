import json
from datetime import datetime

from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from utils import get_match_stats


def stats_players(request: HttpRequest, match_id: int):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    collections = {
        'stats_players_upcomig': 'upcoming',
        'stats_players_live': 'live'
    }
    match_teams = get_match_stats(match_id, collections[request.resolver_match.url_name])
    if not match_teams:
        no_pictures = {'0': {'playerPictureUrl': '',
                             'rating': '-',
                             'kpr': '-',
                             'dpr': '-',
                             'kast': '-',
                             'impact': '-'},
                       '1': {'playerPictureUrl': '',
                             'rating': '-',
                             'kpr': '-',
                             'dpr': '-',
                             'kast': '-',
                             'impact': '-'},
                       '2': {'playerPictureUrl': '',
                             'rating': '-',
                             'kpr': '-',
                             'dpr': '-',
                             'kast': '-',
                             'impact': '-'},
                       '3': {'playerPictureUrl': '',
                             'rating': '-',
                             'kpr': '-',
                             'dpr': '-',
                             'kast': '-',
                             'impact': '-'},
                       '4': {'playerPictureUrl': '',
                             'rating': '-',
                             'kpr': '-',
                             'dpr': '-',
                             'kast': '-',
                             'impact': '-'}}
        if match_teams is None:
            match_teams = {}
        match_teams['team_0'] = {'players': no_pictures}
        match_teams['team_1'] = {'players': no_pictures}
    context = {'items': match_teams, 'date': datetime.utcnow().date}
    context['overview_data'] = json.dumps(match_teams['overview_data'])
    return render(request, 'stats_players.html', context)
