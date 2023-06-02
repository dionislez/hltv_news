from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from utils import (get_all_player, get_all_players, get_player_query,
                   updating_favourites)


def all_players(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    all_players = get_all_players()
    paginator = Paginator(all_players, 30)
    page = request.GET.get('page')

    if not page:
        page = 1
    if int(page) > paginator.num_pages:
        page = paginator.num_pages

    page_obj = paginator.get_page(page)
    start_index = (page_obj.number - 1) * paginator.per_page
    end_index = start_index + paginator.per_page
    all_players = all_players[start_index:end_index]

    context = {'page_obj': page_obj, 'items': all_players, 'date': current_date.date}
    return render(request, 'players.html', context)

def player_query(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    query = request.GET.get('query')
    player = []
    if not query:
        return redirect(reverse('all_players'))
    else:
        player = get_player_query(query)

    current_date = datetime.utcnow()
    context = {'items': player, 'date': current_date.date}
    return render(request, 'players.html', context)

def player_stats(request: HttpRequest, player_id: str):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    items = get_all_player(player_id)
    if items:
        items['openk_opend_diff'] = items['open_k'] - items['open_d']
    context = {'date': current_date.date, 'items': items}
    return render(request, 'player.html', context)

def favorites(request: HttpRequest, match_id: int):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    updated, message = updating_favourites(request.user.username,
                                           request.user.email,
                                           'players',
                                           match_id)
    if updated:
        messages.success(request, message)
    else:
        messages.success(request, message)

    if not request.META.get('HTTP_REFERER'):
        return redirect(reverse('home'))
    return redirect(request.META.get('HTTP_REFERER'))