from django.db import models

# Create your models here.
class Location(models.Model):
    id = models.CharField(primary_key = True)
    location = models.CharField(max_length = 64)
    city = models.CharField(max_length = 30)
    type = models.CharField(max_length = 10)
    image_path = models.CharField(max_length=255, default='static/img/dinh-doc-lap.jpg')
    description = models.TextField(default="")

    def __str__(self):
        return f"{self.location} at {self.address} in {self.city} and {self.address} in {self.city}, here are some descriptions of this location:\n {self.description}"