from django.db import models

# Create your models here.

class Location(models.Model):
    code = models.CharField(max_length=10, unique=False)
    location = models.CharField(max_length = 64)
    city = models.CharField(max_length = 30)   
    type = models.CharField(max_length = 10)
    open_hours = models.CharField(max_length=128, blank=True)
    rating = models.FloatField(default = 5)
    ticket_info = models.CharField(max_length = 30, default = "")
    address = models.CharField(max_length = 32, default = "")
    image_path = models.CharField(max_length=255, default='static/img/dinh-doc-lap.jpg')
    description = models.TextField(default="")

    def __str__(self):
        return f"{self.location} in {self.city}"
    
class User(models.Model):
    name = models.CharField(max_length=50, default="")
    gender = models.CharField(max_length=10, default="", blank=True)
    email = models.EmailField(max_length=100, blank=True)
    loclist = models.ManyToManyField(Location, blank=True, related_name="users", default = None)

    def __str__(self):
        return self.name