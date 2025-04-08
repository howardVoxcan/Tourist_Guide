from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from coordinate_dict import *
from django.urls import reverse
import requests

# Create your views here.
def weather(request):
    api_key = "cef48da67bcd47dd8d165800250804"
    location = "10.772781373025383,106.69683415119852"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

    response = requests.get(url)
    data = response.json()

    # print(f"Location: {data['location']['name']}")
    # print(f"Temperature: {data['current']['temp_c']}°C")
    # print(f"Condition: {data['current']['condition']['text']}")

    return render(request, "location/location.html",{
        "Location": data['location']['name'],
        "Temperature": data['current']['temp_c'],
        "Condition": data['current']['condition']['text']
    })


