from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from utils import get_news, get_news_archive
from django.urls import reverse

from forms import DateForm


NAMES = {
    "actual_news": "Today's news",
    "yesterday_news": "Yesterday's news",
    "previous_news": "Previous news",
    "archive_news": "Yesterday's news"
}


def news_page_actual(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(reverse('home'))

    form = DateForm()
    current_date = datetime.utcnow()
    url_name = request.resolver_match.url_name
    context = {
        'date': current_date.date,
        'items': [
            {'title': 'News were not found',
             'source_link': 'https://www.hltv.org/',
             'time': str(current_date.strftime('%Y-%m-%d'))}
        ],
        'time': str(current_date.strftime('%Y-%m-%d')),
        'form': form
    }

    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            context['time'] = str(form.cleaned_data['date'])
            archive = get_news_archive(form.cleaned_data['date'])
            context['items'] = archive if archive else context['items']

    if url_name == 'archive_news':
        return render(request, 'news_archive.html', context)

    news = get_news(NAMES[url_name])
    context['items'] = news if news else context['items']
    return render(request, 'news.html', context)
