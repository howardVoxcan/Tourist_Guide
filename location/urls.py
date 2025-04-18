from django.urls import path
from . import views

urlpatterns = [
    path('', views.overall_homepage, name='overall'),
    path('<str:location_code>',views.location_display, name="display_location"),
    # path('location_selection', views.selection, name='cart')
]