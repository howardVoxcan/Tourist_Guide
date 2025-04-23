from django.db import models

from location import coordinate

# Create your models here.

class Location(models.Model):
    code = models.CharField(max_length=10, unique=False)
    location = models.CharField(max_length = 64)
    city = models.CharField(max_length = 30)   
    type = models.CharField(max_length = 10)
    rating = models.FloatField(default = 5)
    open_hours = models.CharField(max_length=128, blank=True)
    ticket_info = models.CharField(max_length = 30, default = "")
    address = models.CharField(max_length = 32, default = "")
    image_path = models.CharField(max_length=255, default='static/img/dinh-doc-lap.jpg')
    description = models.TextField(default="")
    coordinate = models.CharField(max_length = 40, default = "")

    def __str__(self):
        return f"{self.code} {self.location} in {self.city}"