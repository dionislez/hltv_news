from django.urls import path
from . import views


urlpatterns = [
    path('news/', views.news_page_actual, name='actual_news'),
    path('news/today', views.news_page_actual, name='actual_news'),
    path('news/yesterday', views.news_page_actual, name='yesterday_news'),
    path('news/previous', views.news_page_actual, name='previous_news'),
    path('news/archive', views.news_page_actual, name='archive_news'),
]