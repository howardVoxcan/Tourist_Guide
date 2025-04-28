from urllib import request
from location.models import Location, Location_List
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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

    api_key = "5f170779de5e4c22b5542528252504"
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
    all_of_locations = Location.objects.all()
    all_of_locations = all_of_locations[:6] 
    # Build danh sách location + HTML rating
    processed_locations = []
    for loc in all_of_locations:
        full_stars = int(loc.rating)
        has_half = (loc.rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars
        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'

        processed_locations.append({
            'code': loc.code,
            'location': loc.location,
            'description': loc.description,
            'image_path': loc.image_path,
            'rating': loc.rating,
            'star_html': star_html,
        })

    location, celsius_degree, fahrenheit_degree, condition = weather()

    return render(request, "homepage/homepage.html", {
        "location": location,
        "celsius_degree": celsius_degree,
        "fahrenheit_degree": fahrenheit_degree,
        "condition": condition.lower(),
        # "locations": locations,
        "all_of_locations": processed_locations,  # Đã xử lý sao
    })

def location_display(request, location_code):
    look_up = Location.objects.get(code = location_code)

    return render(request, "display_location/display.html", {
        "code": look_up.code,
        "location_name": look_up.location,
        "type": look_up.type,
        "open_hours": look_up.open_hours,
        "rating": look_up.rating,
        "rating_half": look_up.rating,
        "ticket_info": look_up.ticket_info,
        "address": look_up.address,
        "image_path": look_up.image_path,
        "description": look_up.description,
        "long_description": look_up.long_description,
        "coordinate": look_up.coordinate
    })

def my_trip(request):
    if User.is_authenticated:
        trip_list = Location_List.objects.filter(user=request.user, name='My Trip').first()
        locations = trip_list.location_set.all() if trip_list else []
        return render(request, 'my_trip/my_trip.html', {
            'locations': locations
        })
    else:
        return redirect('/login')

def favourite(request):
    location_list = Location_List.objects.filter(user = request.user).first()
    
    locations = location_list.location_set.all() if location_list else []

    return render(request, "favourite/favourite.html",{
        'locations': locations
    })

def locations(request):
    all_of_locations = Location.objects.all()
    
    processed_locations = []
    for loc in all_of_locations:
        full_stars = int(loc.rating)
        has_half = (loc.rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars
        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'

        processed_locations.append({
            'code': loc.code,
            'location': loc.location,
            'description': loc.description,
            'image_path': loc.image_path,
            'rating': loc.rating,
            'star_html': star_html,
        })

    return render(request, "locations/locations.html",{
        'locations': processed_locations
    })