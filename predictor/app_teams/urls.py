from django.urls import path
from . import views

urlpatterns = [
    path('teams/all', views.all_teams, name='all_teams'),
    path('teams/all?page=<int:page>', views.all_teams, name='all_teams_by_page'),
    path('teams/all/query', views.teams_query, name='teams_query'),
    path('teams/all/<str:team_id>', views.team_stats, name='team_stats'),
    path('favorites/teams/<int:match_id>', views.favorites, name='favorites_teams'),
]