from django.urls import path
from . import views


urlpatterns = [
    path('upcoming', views.upcoming, name='upcoming'),
    path('live', views.live, name='live'),
    path('upcoming?page=<int:page>', views.upcoming, name='upcoming_list_with_page')
]