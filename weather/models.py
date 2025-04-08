from django.db import models

# Create your models here.    
class Weather(models.Model):
    forecast = models.CharField(max_length = 20)
    advice = models.CharField(max_length = 128)

    def __str__(self):
        return f"Weather Forecast: {self.forecast}\nAdvices: {self.advice}"