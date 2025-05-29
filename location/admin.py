from django.contrib import admin
from .models import Location, Location_List, TripList, TripPath, Comment, BusRoute, BusStop, RouteStop

# Register your models here.
admin.site.register(Location)
admin.site.register(Location_List)
admin.site.register(TripPath)
admin.site.register(TripList)
admin.site.register(Comment)
admin.site.register(BusRoute)
admin.site.register(BusStop)
admin.site.register(RouteStop)