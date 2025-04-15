from django.urls import path
from . import views

urlpatterns = [
    path('', views.overall, name='overall'),
    path('location_selection', views.selection, name='cart')
]