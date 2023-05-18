from datetime import datetime

from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from utils import deleting_favourites_upcoming, get_user_favourites


CATEGORIES = {
    'user_fav_upcoming': ('upcoming', 'Upcoming'),
    'user_fav_matches': ('matches', 'Matches'),
    'user_fav_players': ('players', 'Players'),
    'upcoming_del': 'upcoming',
    'matches_del': 'matches',
    'players_del': 'players'
}

def user_fav(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    url_ = request.resolver_match.url_name
    current_date = datetime.utcnow()
    context = {'date': current_date.date, 'items': []}
    messages.success(request, CATEGORIES[url_][1])
    items = get_user_favourites(request.user.username,
                                request.user.email,
                                CATEGORIES[url_][0])
    if items:
        context['items'] = items
    return render(request, 'favourites.html', context)

def remove(request: HttpRequest, match_id: int):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))
    url_ = request.resolver_match.url_name
    deleting_favourites_upcoming(request.user.username,
                                 request.user.email,
                                 CATEGORIES[url_],
                                 match_id)

    if not request.META.get('HTTP_REFERER'):
        return redirect(reverse('home'))
    return redirect(request.META.get('HTTP_REFERER'))
