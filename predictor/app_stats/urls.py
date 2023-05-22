from django.urls import path
from . import views


urlpatterns = [
    path('stats_upcoming/players/<int:match_id>', views.stats_players, name='stats_players_upcomig'),
    path('stats_live/players/<int:match_id>', views.stats_players, name='stats_players_live'),
    path('stats_played/players/<int:match_id>', views.stats_players, name='stats_players_played'),
    path('stats_fav/players/<int:match_id>', views.stats_players, name='stats_players_fav'),
]