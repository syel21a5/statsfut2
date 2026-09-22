
from django.urls import path
from . import views

urlpatterns = [
    path('stats/<str:country_name>/<str:league_name>/', views.league_stats, name='country_league_stats'),
    path('stats/<str:country_name>/<str:league_name>/cornerpro/', views.cornerpro_league_stats, name='cornerpro_league_stats'),
    path('cornerpro/', views.cornerpro_home, name='cornerpro_home'),
]
