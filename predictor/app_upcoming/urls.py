from django.urls import path
from . import views


urlpatterns = [
    path('upcoming', views.upcoming, name='upcoming'),
    path('live', views.live, name='live'),
    path('played', views.played, name='played'),
    path('upcoming?page=<int:page>', views.upcoming, name='upcoming_list_with_page'),
    path('favorites/upcoming/<int:match_id>', views.favorites, name='favorites'),
]