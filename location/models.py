from django.db import models
from django.contrib.auth.models import User
from datetime import time
from django.contrib.auth import get_user_model
from sympy import true 
import uuid

# Create your models here.
User = get_user_model()
class LocationQuerySet(models.QuerySet):
    def open_at(self, desired_time):
        return self.filter(
            models.Q(open_time__lte=desired_time, close_time__gte=desired_time) |
            models.Q(open_time__gt=models.F('close_time')) & (
                models.Q(open_time__lte=desired_time) | models.Q(close_time__gte=desired_time)
            )
        )
    
class Location_List(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE,related_name = "location_list")
    name = models.CharField(max_length = 50, default = "")

    def __str__(self):
        return self.name

class Location(models.Model):
    favourited_by = models.ManyToManyField(User, related_name="favourite_locations", blank=True)
    code = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length = 64)
    type = models.CharField(max_length=18, default = "")
    tags = models.TextField(default = "")
    rating = models.FloatField(default = 5)
    open_time = models.TimeField(default = time(0,0))
    close_time = models.TimeField(default = time(23,59))
    ticket_info = models.CharField(max_length = 100, default = "")
    address = models.CharField(max_length = 100, default = "")
    image_path = models.CharField(max_length=255, default='')
    description = models.TextField(default="")
    long_description = models.TextField(default="")
    coordinate = models.CharField(max_length = 40, default = "")

    def __str__(self):
        return f"{self.code} {self.location} : {self.description} "

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments') 
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='comments')  
    content = models.TextField() 
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    bot_reply = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']  # Show newest comments first

    def __str__(self):
        return f"Comment by {self.user.username} on {self.location.location}"

class TripList(models.Model):
    id = models.CharField(
        primary_key=True, max_length=255, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trip_lists")
    name = models.CharField(max_length=255, default="My trip list")

    def __str__(self):
        return self.name

class TripPath(models.Model):
    start_point = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="start_paths")
    end_point = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="end_paths")
    trip_list = models.ForeignKey(TripList, on_delete=models.CASCADE, related_name="trip_paths")
    path_name = models.CharField(max_length=255, default = "")
    locations_ordered = models.CharField(max_length = 255)
    total_distance = models.FloatField(null=True, blank=True)
    total_duration = models.FloatField(null=True, blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    locations = models.ManyToManyField(Location, related_name="trip_paths")

    def __str__(self):
        return self.path_name
    
class TemporaryTripCart(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    locations = models.JSONField(default=list)  # List of location names
    start_location = models.CharField(max_length=255, null=True, blank=True)
    end_location = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.session_id}"
    
class TemporaryUser(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session_id
    
class BusStop(models.Model):
    osm_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

class BusRoute(models.Model):
    osm_id = models.BigIntegerField(unique=True)
    ref = models.CharField(max_length=50)      # e.g. "01"
    name = models.CharField(max_length=200, blank=True)
    operator = models.CharField(max_length=200, blank=True)
    stops = models.ManyToManyField(
        BusStop,
        through='RouteStop',
        related_name='routes'
    )

    def __str__(self):
        return f"Route {self.ref}"

class RouteStop(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    stop = models.ForeignKey(BusStop, on_delete=models.CASCADE)
    sequence = models.PositiveIntegerField()     # order in route

    class Meta:
        unique_together = (('route', 'stop', 'sequence'),)
        ordering = ['route', 'sequence']