from urllib import request
from location.models import Location, Location_List, TripPath, TripList
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from location.coordinate import coordinate_dict
from django.contrib.auth.models import User
import itertools, requests, geocoder, json

# Create your views here.
def weather():
    location = "10.762,106.6601"

    api_key = "5f170779de5e4c22b5542528252504"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

    response = requests.get(url)
    data = response.json()

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

def locations(request):
    all_of_locations = Location.objects.all()

    location_list = Location_List.objects.filter(user=request.user).first()
    
    # Kiểm tra nếu location_list là None, trả về list rỗng
    locations = location_list.location_set.all() if location_list else []
    
    processed_locations = []
    for loc in all_of_locations:
        full_stars = int(loc.rating)
        has_half = (loc.rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars
        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'
        
        # Kiểm tra xem location có trong location_list không
        if location_list and loc in location_list.location_set.all():
            favourite_symbol = '<i class="fa-solid fa-heart"></i>'
        else:
            favourite_symbol = '<i class="fa-regular fa-heart"></i>'

        processed_locations.append({
            'code': loc.code,
            'location': loc.location,
            'description': loc.description,
            'image_path': loc.image_path,
            'rating': loc.rating,
            'star_html': star_html,
            'favourite_symbol': favourite_symbol,
        })

    return render(request, "locations/locations.html", {
        'locations': processed_locations
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

@login_required
def favourite(request):
    if request.method == "POST":
        code = request.POST.get('value')  # an toàn hơn
        if not code:
            return redirect('favourite')  # hoặc báo lỗi hợp lý hơn
        
        selected = Location.objects.get(code=code)

        user = request.user  
        location_list = user.location_list.first()  
        if not location_list:
            location_list = Location_List.objects.create(user=user, name="Favourite Locations")

        if selected in location_list.location_set.all():
            location_list.location_set.remove(selected)
        else:
            location_list.location_set.add(selected)

        return redirect('favourite')

    else:    
        location_list = Location_List.objects.filter(user = request.user).first()        
        locations = location_list.location_set.all() if location_list else []

        return render(request, "favourite/favourite.html",{
            'locations': locations
        })

# @login_required
# def my_trip(request):
#     if request.method == 'POST':
#         path_name = request.POST['path_name']
#         trip_list_id = request.POST['trip_list_id']
#         locations = request.POST.getlist('locations')

#         # Kiểm tra nếu trip_list_id là hợp lệ
#         if not trip_list_id.isdigit():  # Nếu trip_list_id không phải số
#             return render(request, 'my_trip/my_trip.html', {
#                 'error': 'Vui lòng chọn một Trip List hợp lệ.',
#                 'trip_lists': TripList.objects.filter(user=request.user),
#                 'locations': Location.objects.all()
#             })

#         trip_list_id = int(trip_list_id)  # Chuyển trip_list_id thành số nguyên
#         try:
#             trip_list = TripList.objects.get(id=trip_list_id)
#         except TripList.DoesNotExist:
#             return render(request, 'my_trip.html', {
#                 'error': 'Không tìm thấy Trip List.',
#                 'trip_lists': TripList.objects.filter(user=request.user),
#                 'locations': Location.objects.all()
#             })

#         trip_path = TripPath.objects.create(
#             path_name=path_name,
#             trip_list=trip_list,
#         )

#         # Tiếp tục xử lý các thông tin khác như locations, pinned, precedence...

#         return redirect('my_trip/my_trip')

#     # GET method: hiển thị trip lists và locations
#     trip_lists = TripList.objects.filter(user=request.user)
#     locations = Location.objects.all()

#     return render(request, 'my_trip/my_trip.html', {
#         'trip_lists': trip_lists,
#         'locations': locations
#     })
