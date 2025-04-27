from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Location_List(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE,related_name = "location_list")
    name = models.CharField(max_length = 50, default = "")

    def __str__(self):
        return self.name

class Location(models.Model):
    loc = models.ForeignKey(Location_List, on_delete = models.CASCADE, null = True, blank = True)
    code = models.CharField(max_length=10, unique=True)
    location = models.CharField(max_length = 64)
    type = models.CharField(max_length=13, default = "")
    rating = models.FloatField(default = 5)
    open_hours = models.CharField(max_length=128, blank=True)
    ticket_info = models.CharField(max_length = 100, default = "")
    address = models.CharField(max_length = 100, default = "")
    image_path = models.CharField(max_length=255, default='')
    description = models.TextField(default="")
    long_description = models.TextField(default="")
    coordinate = models.CharField(max_length = 40, default = "")

    def __str__(self):
        return f"{self.code} {self.location} : {self.description} "