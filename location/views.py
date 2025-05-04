from urllib import request
from datetime import datetime
from annotated_types import Len
from shapely import length
from location.models import Location, Location_List, TripPath, TripList
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from location.coordinate import coordinate_dict
from django.contrib.auth.models import User
import itertools, requests, geocoder, json
from django.contrib import messages

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

    def find_hamiltonian_cycle(self, fixed_position=None, precedence_constraints=None, start=None, end=None):
        import itertools
        vertices = list(range(self.num_vertices))
        min_path = None
        min_cost = float("inf")

        if fixed_position is None:
            fixed_position = [False] * (self.num_vertices + 1)
        if precedence_constraints is None:
            precedence_constraints = []

        fixed_position_map = {}
        for i, fixed in enumerate(fixed_position):
            if fixed:
                fixed_position_map[i] = None

        # Loại bỏ start và end ra khỏi hoán vị (nếu có)
        inner_vertices = vertices.copy()
        if start is not None:
            inner_vertices.remove(start)
        if end is not None and end in inner_vertices:
            inner_vertices.remove(end)

        for perm in itertools.permutations(inner_vertices):
            path = list(perm)
            if start is not None:
                path.insert(0, start)
            else:
                path.insert(0, 0)

            if end is not None:
                path.append(end)
            else:
                path.append(path[0])  # Quay về điểm xuất phát như TSP

            valid = True

            # Kiểm tra fixed_position
            for idx, node in fixed_position_map.items():
                if idx < len(path):
                    if node is not None and path[idx] != node:
                        valid = False
                        break
                    fixed_position_map[idx] = path[idx]

            # Kiểm tra precedence_constraints
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
        rating = (round(loc.rating*2))/2
        full_stars = int(rating)
        has_half = (rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars

        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'
            empty_stars = 5 - full_stars - 1
        else:
            empty_stars = 5 - full_stars

        star_html += '<i class="far fa-star"></i>' * empty_stars

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
    if request.method == "POST":
        code = request.POST.get('value')
        if not code:
            return redirect('favourite')

        selected = Location.objects.get(code=code)
        user = request.user
        location_list = user.location_list.first()
        if not location_list:
            location_list = Location_List.objects.create(user=user, name="Favourite Locations")

        if selected in location_list.location_set.all():
            location_list.location_set.remove(selected)
        else:
            location_list.location_set.add(selected)

        return redirect('locations')

    else:
        type_filter = request.GET.get('type')
        min_rating = request.GET.get('rating')
        desired_time = request.GET.get('desired_time')

        all_of_locations = Location.objects.all()

        if type_filter:
            all_of_locations = all_of_locations.filter(type__iexact=type_filter)

        if min_rating:
            try:
                min_rating = float(min_rating)
                all_of_locations = all_of_locations.filter(rating__gte=min_rating)
            except ValueError:
                pass

        if desired_time:
            try:
                desired_time_obj = datetime.strptime(desired_time, "%H:%M").time()
                all_of_locations = all_of_locations.filter(
                    open_time__lte=desired_time_obj,
                    close_time__gte=desired_time_obj
                )
            except ValueError:
                pass

        # Sắp xếp theo thời gian mở
        all_of_locations = all_of_locations.order_by('open_time')

        location_list = Location_List.objects.filter(user=request.user).first()
        locations = location_list.location_set.all() if location_list else []

        # Tiếp tục xử lý các location như bình thường
        processed_locations = []
        for loc in all_of_locations:
            rating = (round(loc.rating * 2)) / 2
            full_stars = int(rating)
            has_half = (rating - full_stars) >= 0.5
            star_html = '<i class="fas fa-star"></i>' * full_stars

            if has_half:
                star_html += '<i class="fas fa-star-half-alt"></i>'
                empty_stars = 5 - full_stars - 1
            else:
                empty_stars = 5 - full_stars

            star_html += '<i class="far fa-star"></i>' * empty_stars

            favourite_symbol = '<i class="fa-solid fa-heart"></i>' if location_list and loc in location_list.location_set.all() else '<i class="fa-regular fa-heart"></i>'

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
            'locations': processed_locations,
            'current_filters': {
                'type': type_filter or '',
                'rating': min_rating or '',
                'desired_time': desired_time or '',
            }
        })

def location_display(request, location_code):
    look_up = get_object_or_404(Location, code=location_code)

    # Calculate star HTML once
    rating = round(look_up.rating * 2) / 2
    full_stars = int(rating)
    has_half = (rating - full_stars) >= 0.5
    star_html = '<i class="fas fa-star"></i>' * full_stars

    if has_half:
        star_html += '<i class="fas fa-star-half-alt"></i>'
        empty_stars = 5 - full_stars - 1
    else:
        empty_stars = 5 - full_stars

    star_html += '<i class="far fa-star"></i>' * empty_stars

    # Determine heart icon
    if request.user.is_authenticated and look_up.loc and look_up.loc.user == request.user:
        favourite_symbol = '<i class="fa-solid fa-heart"></i>'
    else:
        favourite_symbol = '<i class="fa-regular fa-heart"></i>'      



    return render(request, "display_location/display.html", {
        "location_name": look_up.location,
        "type": look_up.type,
        "open_time" : look_up.open_time,   
        "close_time": look_up.close_time,
        "ticket_info": look_up.ticket_info,
        "address": look_up.address,
        "image_path": look_up.image_path,
        "long_description": look_up.long_description,
        "favourite_symbol": favourite_symbol,
        "star_html": star_html
    })

@login_required
def favourite(request):    
    location_list = Location_List.objects.filter(user = request.user).first()        
    locations = location_list.location_set.all() if location_list else []

    return render(request, "favourite/favourite.html",{
        'locations': locations
    })

@login_required
def my_trip(request):
    user = request.user
    trip_list_id = f"{user.username}-favourite"

    # Tạo TripList nếu chưa có
    trip_list, _ = TripList.objects.get_or_create(id=trip_list_id, defaults={
        'user': user,
        'name': f"{user.username}'s Favourite Trip"
    })

    if request.method == 'POST':
        path_name = request.POST.get('path_name')
        if not path_name:
            return redirect('my_trip')

        # Lấy Location_List đầu tiên của user
        location_list = Location_List.objects.filter(user=user).first()
        if not location_list:
            return redirect('favourite')

        # Lấy toàn bộ location từ danh sách trên
        locations = list(location_list.location_set.all())
        if not locations:
            return redirect('favourite')

        # Ánh xạ id <-> index trong danh sách để phục vụ TSP
        id_to_index = {loc.id: idx for idx, loc in enumerate(locations)}
        index_to_id = {idx: loc.id for idx, loc in enumerate(locations)}
        coordinates = [loc.coordinate for loc in locations]

        pinned_positions = [None] * len(locations)
        fixed_position_flags = [False] * len(locations)
        precedence_constraints = []

        # Lấy id của điểm bắt đầu và kết thúc từ form
        start_id_str = request.POST.get('start_point')
        end_id_str = request.POST.get('end_point')
        start_id = int(start_id_str) if start_id_str and start_id_str.isdigit() else None
        end_id = int(end_id_str) if end_id_str and end_id_str.isdigit() else None

        # Xử lý pinned/precedence (ràng buộc)
        for loc in locations:
            loc_id = loc.id
            loc_id_str = str(loc_id)
            index = id_to_index[loc_id]

            # Pinned
            pinned_str = request.POST.get(f'pinned_order_{loc_id_str}')
            if pinned_str and pinned_str.isdigit():
                pinned_index = int(pinned_str) - 1
                if 0 <= pinned_index < len(locations):
                    pinned_positions[pinned_index] = index
                    fixed_position_flags[pinned_index] = True

            # Ràng buộc đi sau
            after_id_str = request.POST.get(f'precedence_after_{loc_id_str}')
            if after_id_str and after_id_str.isdigit():
                after_id = int(after_id_str)
                if after_id in id_to_index:
                    precedence_constraints.append((id_to_index[after_id], index))

        # Tính khoảng cách
        distances = []
        for i in range(len(coordinates)):
            for j in range(i + 1, len(coordinates)):
                dist, _ = distance(coordinates[i], coordinates[j])
                distances.append((i, j, dist))
                distances.append((j, i, dist))

        # Tạo graph
        graph = Graph(len(locations))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        start_index = id_to_index.get(start_id) if start_id else None
        end_index = id_to_index.get(end_id) if end_id else None

        path, cost = graph.find_hamiltonian_cycle(
            fixed_position=fixed_position_flags,
            precedence_constraints=precedence_constraints,
            start=start_index,
            end=end_index
        )

        if path is None:
            messages.error(request, "Không thể tạo lịch trình hợp lệ với các ràng buộc đã chọn.")
            return redirect('favourite')

        ordered_location_ids = [index_to_id[i] for i in path]

        # Lưu TripPath mới (chuyển list -> JSON string)
        TripPath.objects.create(
            trip_list=trip_list,
            path_name=path_name,
            locations_ordered=json.dumps(ordered_location_ids),
            total_distance=cost
        )

        # Xoá danh sách đã chọn
        location_list.location_set.clear()
        return redirect('my_trip')

    # GET: Lấy và hiển thị các TripPath
    trip_paths = TripPath.objects.filter(trip_list=trip_list).order_by('created_at')

    # Parse từng path → list location ids → map sang tên
    all_ids = []
    parsed_trip_paths = []

    for path in trip_paths:
        try:
            loc_ids = json.loads(path.locations_ordered)
        except json.JSONDecodeError:
            loc_ids = []

        all_ids.extend(loc_ids)
        parsed_trip_paths.append({
            'path_name': path.path_name,
            'locations': loc_ids,
            'distance': round(path.total_distance / 1000, 1),
            'created_at': path.created_at
        })

    # Query tên các địa điểm
    location_qs = Location.objects.filter(id__in=all_ids)
    location_map = {loc.id: loc.location for loc in location_qs}

    return render(request, 'my_trip/my_trip.html', {
        'trip_paths': parsed_trip_paths,
        'location_map': location_map
    })