from datetime import datetime

from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import render
from utils import get_live_events, get_upcoming_events


def upcoming(request: HttpRequest):
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
    current_date = datetime.utcnow()
    events = get_live_events()
    return render(request, 'live.html', {'items': events, 'date': current_date.date})
