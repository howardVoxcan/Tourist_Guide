from urllib import request
from location.models import Location
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from location.coordinate import coordinate_dict
import itertools
import requests
import geocoder

# Create your views here.
def weather():
    g = geocoder.ip('me')
    location = f"{g.latlng[0]},{g.latlng[1]}"

    # print("Latitude:", data["lat"])
    # print("Longitude:", data["lon"])
    # print("City:", data["city"])
    # print("Country:", data["country"])

    api_key = "cef48da67bcd47dd8d165800250804"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

    response = requests.get(url)
    data = response.json()

    # print(f"Location: {data['location']['name']}")
    # print(f"Temperature: {data['current']['temp_c']}°C")
    # print(f"Condition: {data['current']['condition']['text']}")
    location_name = data['location']['name']
    celsius_degree = data['current']['temp_c']
    fahrenheit_degree = data['current']['temp_f']
    condition = data['current']['condition']['text'].lower()

    return location_name, celsius_degree, fahrenheit_degree, condition

class Graph:
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.edges = [[0] * num_vertices for _ in range(num_vertices)]  # Ma trận kề

    def add_edge(self, u, v, weight):
        self.edges[u][v] = weight

    def find_hamiltonian_cycle(self):
        vertices = list(range(self.num_vertices))
        min_path = None
        min_cost = float("inf")

        # Tạo tất cả hoán vị bắt đầu từ đỉnh 0
        for perm in itertools.permutations(vertices[1:]):  
            path = [0] + list(perm) + [0]
            cost = sum(self.edges[path[i]][path[i+1]] for i in range(len(path) - 1))

            if cost < min_cost:
                min_cost = cost
                min_path = path

        return min_path, min_cost

def distance(origins, destinations):
    api_key = "nV8MX9Jxszg9MyjUJv5yfTUK4OzKhTGtG0z2E779ZGtdhd2TenzBA1QgOzOf6H2T"
    url = "https://api-v2.distancematrix.ai/maps/api/distancematrix/json"

    params = {
        "origins": origins,
        "destinations": destinations,
        "key": api_key
    }

    response = requests.get(url, params=params)
    
    result = response.json()
    distance = result["rows"][0]["elements"][0]["distance"]["value"]
    duration = result["rows"][0]["elements"][0]["duration"]["value"]
    return distance, duration

def overall_homepage(request):
    location, celsius_degree, fahrenheit_degree, condition = weather()
    return render(request, "homepage/homepage.html", {
        "location": location,
        "celsius_degree":celsius_degree,
        "fahrenheit_degree": fahrenheit_degree,
        "condition": condition.lower()
    })

def location_display(request, location_code):
    look_up = Location.objects.get(code = location_code)
    if look_up:
        return render(request, "display_location/display.html",{
            "location": look_up.location,
            "city": look_up.city,
            "rating": look_up.rating,
            "image": look_up.image_path,
            "description": look_up.description
        })
    else:
        pass

def selection(request):
    pass
# def index(request):
#     if not request.user.is_authenticated:
#         return HttpResponseRedirect(reverse("login"))
#     return render(request, "location/user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "users/login.html", {
                "message": "Invalid credentials."
            })
    else:
        return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    return render(request, "location/login.html", {
        "message": "Logged out."
    })