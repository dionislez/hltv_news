from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from utils import get_all_team, get_team_query, get_teams, updating_favourites


def all_teams(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    all_teams = get_teams()
    paginator = Paginator(all_teams, 30)
    page = request.GET.get('page')

    if not page:
        page = 1
    if int(page) > paginator.num_pages:
        page = paginator.num_pages

    page_obj = paginator.get_page(page)
    start_index = (page_obj.number - 1) * paginator.per_page
    end_index = start_index + paginator.per_page
    all_teams = all_teams[start_index:end_index]

    context = {'page_obj': page_obj, 'items': all_teams, 'date': current_date.date}
    return render(request, 'teams.html', context)

def teams_query(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    query = request.GET.get('query')
    team = []
    if not query:
        return redirect(reverse('all_teams'))
    else:
        team = get_team_query(query)

    current_date = datetime.utcnow()
    context = {'items': team, 'date': current_date.date}
    return render(request, 'teams.html', context)

def team_stats(request: HttpRequest, team_id: str):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    items = get_all_team(team_id)
    if items and items.get('maps_stats'):
        for key, value in items['maps_stats'].items():
            items['maps_stats'][key]['win_rate'] = int(items['maps_stats'][key]['win_rate'])

            stats = value['wins_draws_losses']
            win_perc = round((stats[0] / (stats[0] + stats[1] + stats[2])) * 100, 2)
            items['maps_stats'][key]['win_perc'] = win_perc
    context = {'date': current_date.date, 'items': items}
    return render(request, 'team.html', context)

def favorites(request: HttpRequest, match_id: int):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    updated, message = updating_favourites(request.user.username,
                                           request.user.email,
                                           'teams',
                                           match_id)
    if updated:
        messages.success(request, message)
    else:
        messages.success(request, message)

    if not request.META.get('HTTP_REFERER'):
        return redirect(reverse('home'))
    return redirect(request.META.get('HTTP_REFERER'))
