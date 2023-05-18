from django.urls import path
from . import views


urlpatterns = [
    path('user_fav', views.user_fav, name='user_fav_upcoming'),
    path('user_fav/upcoming', views.user_fav, name='user_fav_upcoming'),
    path('user_fav/matches', views.user_fav, name='user_fav_matches'),
    path('user_fav/players', views.user_fav, name='user_fav_players'),
    path('user_fav/upcoming/del/<int:match_id>', views.remove, name='upcoming_del'),
    path('user_fav/matches/del/<int:match_id>', views.remove, name='matches_del'),
    path('user_fav/players/del/<int:match_id>', views.remove, name='players_del'),
]