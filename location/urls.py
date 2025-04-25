from django.urls import path
from . import views

urlpatterns = [
    path('', views.overall_homepage, name='overall'),
    path('my_trip/', views.my_trip, name = 'selected_locations'),
    path('favourite/',views.favourite, name = 'favourite'),
    path('<str:location_code>',views.location_display, name='display_location'),
]