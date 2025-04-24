from urllib import request
from location.models import Location, Location_List
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from location.coordinate import coordinate_dict
from django.contrib.auth.models import User
import itertools, requests, geocoder

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

import itertools

import itertools

class Graph:
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.edges = [[0] * num_vertices for _ in range(num_vertices)]  # Ma trận kề

    def add_edge(self, u, v, weight):
        self.edges[u][v] = weight

    def find_hamiltonian_cycle(self, fixed_position=None, precedence_constraints=None):
        vertices = list(range(self.num_vertices))
        min_path = None
        min_cost = float("inf")

        if fixed_position is None:
            fixed_position = [False] * (self.num_vertices + 1)  # +1 cho điểm quay về
        if precedence_constraints is None:
            precedence_constraints = []

        fixed_position_map = {}  # map: index -> node cố định ở vị trí đó
        for i, fixed in enumerate(fixed_position):
            if fixed:
                fixed_position_map[i] = None  # sẽ được gán ở phần sinh perm

        # Duyệt tất cả hoán vị các đỉnh chưa cố định
        for perm in itertools.permutations(vertices[1:]):  
            path = [0] + list(perm) + [0]

            valid = True

            # Kiểm tra fixed_position
            for idx, node in fixed_position_map.items():
                if idx < len(path):
                    if node is not None and path[idx] != node:
                        valid = False
                        break
                    fixed_position_map[idx] = path[idx]

            # Kiểm tra precedence_constraints: u phải đứng trước v
            for u, v in precedence_constraints:
                try:
                    if path.index(u) >= path.index(v):
                        valid = False
                        break
                except ValueError:
                    valid = False
                    break

            if not valid:
                continue

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
    look_up = Location.objects.get(code=location_code)

    return render(request, "display_location/display.html", {
        "code": look_up.code,
        "location_name": look_up.location,
        "city": look_up.city,
        "type": look_up.type,
        "open_hours": look_up.open_hours,
        "rating": look_up.rating,
        "ticket_info": look_up.ticket_info,
        "address": look_up.address,
        "image_path": look_up.image_path,
        "description": look_up.description,
        "coordinate": look_up.coordinate
    })

def selected_locations(request):
    trip_list = Location_List.objects.filter(user=request.user, name='My Trip').first()
    locations = trip_list.location_set.all() if trip_list else []
    return render(request, 'my_trip/my_trip.html', {
        'locations': locations
    })