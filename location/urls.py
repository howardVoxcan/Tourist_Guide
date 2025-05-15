from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.overall_homepage, name='homepage'),
    path('my_trip/', views.my_trip, name = 'my_trip'),
    path('weather', views.weather, name = 'weather'),
    path('favourite/',views.favourite, name = 'favourite'),
    path('locations', views.locations, name = 'locations'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('webhook/', views.dialogflow_webhook, name='dialogflow_webhook'),
    path('<str:location_code>/',views.display_location, name='display_location'),
    path('<str:location_code>/submit_comment_ajax/', views.submit_comment_ajax, name='submit_comment_ajax'),
]