from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from utils import get_news

NAMES = {
    "actual_news": "Today's news",
    "yesterday_news": "Yesterday's news",
    "previous_news": "Previous news"
}


def news_page_actual(request: HttpRequest) -> HttpResponse:
    context = {
        'date': datetime.utcnow().date,
        'items': get_news(NAMES[request.resolver_match.url_name])
    }
    return render(request, 'news.html', context)