from django.db import models

# Create your models here.
class location(models.Model):
    id = models.AutoField(primary_key = True)
    location = models.CharField(max_length = 64)
    city = models.CharField(max_length = 30)
    address = models.CharField(max_length = 50)
    type = models.CharField(max_length = 10)
    description = models.TextField()

    def __str__(self):
        return f"{self.location} at {self.address} in {self.city} and {self.address} in {self.city}, here are some descriptions of this location:\n {self.description}"
    
class Distance(models.Model):
    origin = models.ForeignKey(location, on_delete = models.CASCADE, related_name = "Start Location")
    destination = models.ForeignKey(location, on_delete = models.CASCADE, related_name = "End point/ Destination")
    distance_car = models.FloatField(min_value = 0)
    distance_bike = models.FloatField(min_value = 0)

    def __str__(self):
        return f"{self.origin} to {self.destination} is {self.distance} km"