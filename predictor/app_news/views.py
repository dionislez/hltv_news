from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from utils import get_news


def news_page(request: HttpRequest) -> HttpResponse:
    current_time = datetime.utcnow()
    today_news = get_news("Today's news")
    context = {'date': current_time.date, 'items': today_news}
    return render(request, 'news.html', context)