from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.overall_homepage, name='overall'),
    path('my_trip/', views.my_trip, name = 'selected_locations'),
    path('favourite/',views.favourite, name = 'favourite'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('<str:location_code>',views.location_display, name='display_location'),
]