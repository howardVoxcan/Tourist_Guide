from django.contrib import admin
from .models import Location, Location_List, TripList, TripPath, Comment

# Register your models here.
admin.site.register(Location)
admin.site.register(Location_List)
admin.site.register(TripPath)
admin.site.register(TripList)
admin.site.register(Comment)