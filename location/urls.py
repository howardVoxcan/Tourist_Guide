from django.urls import path
from . import views

urlpatterns = [
    path('', views.overall_homepage, name='overall'),
    path('selected_locations/', views.selected_locations, name = 'selected_locations'),
    path('<str:location_code>',views.location_display, name='display_location'),
]