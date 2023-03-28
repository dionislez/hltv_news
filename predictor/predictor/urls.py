from app_news.views import news_page_actual
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('news/', news_page_actual, name='actual_news'),
    path('news/today', news_page_actual, name='actual_news'),
    path('news/yesterday', news_page_actual, name='yesterday_news'),
    path('news/previous', news_page_actual, name='previous_news'),
]
