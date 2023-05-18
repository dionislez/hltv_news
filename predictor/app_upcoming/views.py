from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from utils import get_live_events, get_upcoming_events, updating_favourites


def upcoming(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    events = get_upcoming_events()

    paginator = Paginator(events, 10)
    page = request.GET.get('page')

    if not page:
        page = 1
    if int(page) > paginator.num_pages:
        page = paginator.num_pages

    page_obj = paginator.get_page(page)
    start_index = (page_obj.number - 1) * paginator.per_page
    end_index = start_index + paginator.per_page
    events = events[start_index:end_index]

    context = {'page_obj': page_obj}
    context['items'] = events
    context['date'] = current_date.date
    return render(request, 'upcoming.html', context)

def live(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    current_date = datetime.utcnow()
    events = get_live_events()
    return render(request, 'live.html', {'items': events, 'date': current_date.date})

def favorites(request: HttpRequest, match_id: int):
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    updated, message = updating_favourites(request.user.username,
                                           request.user.email,
                                           'upcoming',
                                           match_id)
    if updated:
        messages.success(request, message)
    else:
        messages.success(request, message)

    if not request.META.get('HTTP_REFERER'):
        return redirect(reverse('home'))
    return redirect(request.META.get('HTTP_REFERER'))
