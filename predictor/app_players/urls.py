from django.urls import path
from . import views


urlpatterns = [
    path('players/all', views.all_players, name='all_players'),
    path('players/all?page=<int:page>', views.all_players, name='all_players_by_page'),
    path('players/all/query', views.player_query, name='player_query'),
    path('players/all/<str:player_id>', views.player_stats, name='player_stats'),
    path('favorites/players/<int:match_id>', views.favorites, name='favorites_players'),
]