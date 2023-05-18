from app_news.views import news_page_actual
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app_register.urls')),
    path('', include('app_upcoming.urls')),
    path('', include('app_news.urls')),
    path('', include('app_favourites.urls')),
]
