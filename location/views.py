from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from location.coordinate import coordinate_dict
from location.models import Location, Location_List, TripPath, TripList, Comment
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from urllib import request
from datetime import datetime
from annotated_types import Len
from shapely import length
import itertools, requests, geocoder, json
from .TSP import Graph, distance
import requests, joblib, os, spacy
from django.conf import settings

# Create your views here.
nlp = spacy.load("en_core_web_sm")

label_encoder_path = os.path.join(settings.BASE_DIR, 'location', 'label_encoder.pkl')
vectorizer_path = os.path.join(settings.BASE_DIR, 'location', 'tfidf_vectorizer.pkl')
model_path = os.path.join(settings.BASE_DIR, 'location', 'xgboost_model.pkl')

label_encoder = joblib.load(label_encoder_path)
vectorizer = joblib.load(vectorizer_path)
model = joblib.load(model_path)

def predict_sentiment(text):
    # Preprocessing
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
    cleaned_text = ' '.join(tokens)

    # Predictions
    X = vectorizer.transform([cleaned_text])
    pred_label = model.predict(X)[0]
    sentiment = label_encoder.inverse_transform([pred_label])[0]
    return sentiment

def weather(request):
    location = "10.762,106.6601"
    api_key = "5f170779de5e4c22b5542528252504"
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=3"

    response = requests.get(url)
    data = response.json()

    location_name = data['location']['name']
    forecast_data = []

    for day in data['forecast']['forecastday']:
        date = day['date']
        periods = []

        # Get 8 parts of the day (every 3 hours)
        for hour_data in day['hour'][::2]:  # Picks 0:00, 3:00, 6:00, ..., 21:00
            periods.append({
                'time': hour_data['time'][11:],  # Only show HH:MM
                'temp_c': hour_data['temp_c'],
                'condition': hour_data['condition']['text'],
                'icon': hour_data['condition']['icon']
            })

        forecast_data.append({
            'date': date,
            'periods': periods
        })

    context = {
        'location_name': location_name,
        'forecast': forecast_data
    }

    return render(request, 'weather/weather.html', context)

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

    return render(request, "homepage/homepage.html", {
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
        search_query = request.GET.get('search')

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

        if search_query:
            all_of_locations = all_of_locations.filter(
                Q(location__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(long_description__icontains=search_query) |
                Q(tags__icontains=search_query)
            )

        all_of_locations = all_of_locations.order_by('open_time')

        location_list = Location_List.objects.filter(user=request.user).first()
        locations = location_list.location_set.all() if location_list else []

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

            favourite_symbol = (
                '<i class="fa-solid fa-heart"></i>'
                if location_list and loc in location_list.location_set.all()
                else '<i class="fa-regular fa-heart"></i>'
            )

            processed_locations.append({
                'code': loc.code,
                'location': loc.location,
                'description': loc.description,
                'image_path': loc.image_path,
                'rating': loc.rating,
                'open_time': loc.open_time,
                'close_time': loc.close_time,
                'star_html': star_html,
                'favourite_symbol': favourite_symbol,
            })

        return render(request, "locations/locations.html", {
            'locations': processed_locations,
            'current_filters': {
                'type': type_filter or '',
                'rating': min_rating or '',
                'desired_time': desired_time or '',
                'search': search_query or '',
            }
        })

def display_location(request, location_code): 
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        rating = request.POST.get('rating')
        location = get_object_or_404(Location, code=location_code)

        if not content:
            return redirect('display_location', location_code=location_code)

        bot_reply = "Thanks for your comment!"  # Default fallback reply

        if not rating:
            sentiment = predict_sentiment(content)
            if sentiment == "positive":
                bot_reply = "We're thrilled you had a great time! Hope to see you again!"
                rating = 4
            elif sentiment == "negative":
                bot_reply = "We're sorry to hear that. Your feedback helps us get better."
                rating = 2
            else:
                bot_reply = "Thank you for sharing your thoughts. We appreciate your input!"
                rating = 3
        else:
            rating = int(rating)
            if rating == 5:
                bot_reply = "Awesome! We're thrilled you loved it!"
            elif rating == 4:
                bot_reply = "Great! Glad you had a good time."
            elif rating == 3:
                bot_reply = "Thanks! We'll try to make your next visit even better."
            elif rating == 2:
                bot_reply = "Sorry to hear that. We hope things improve."
            elif rating == 1:
                bot_reply = "We sincerely apologize. Your feedback is valuable to us."
            else:
                bot_reply = "Thanks for your feedback!"

        Comment.objects.create(
            location=location,
            user=request.user,
            content=content,
            rating=rating,
            bot_reply=bot_reply
        )
        return redirect('display_location', location_code=location_code)
    
    else:
        look_up = get_object_or_404(Location, code=location_code)

        comments = Comment.objects.filter(location=look_up).prefetch_related('replies')

        # Stars
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

        # Heart icon
        if request.user.is_authenticated and look_up.loc and look_up.loc.user == request.user:
            favourite_symbol = '<i class="fa-solid fa-heart"></i>'
        else:
            favourite_symbol = '<i class="fa-regular fa-heart"></i>'

        lat, long = look_up.coordinate.split(", ")
        open_time = look_up.open_time.strftime("%H:%M")
        close_time = look_up.close_time.strftime("%H:%M")
        if open_time == "00:00" and close_time == "23:59":
            open_time = "All day"
        elif look_up.close_time < look_up.open_time:
            open_time = f"{open_time} - {close_time} (The next day)"
        else:
            open_time = f"{open_time} - {close_time}"

        comments = Comment.objects.filter(location=look_up, parent=None).prefetch_related('replies').order_by('-created_at')

        return render(request, "display_location/display.html", {
            "code": look_up.code,
            "location_name": look_up.location,
            "type": look_up.type,
            "open_time": open_time,
            "ticket_info": look_up.ticket_info,
            "address": look_up.address,
            "image_path": look_up.image_path,
            "long_description": look_up.long_description,
            "favourite_symbol": favourite_symbol,
            "lat": lat,
            "long": long,
            "star_html": star_html,
            "comments": comments, 
            "location_obj": look_up  # needed for POST form
        })

@login_required
def favourite(request):
    # Xử lý POST request để xóa địa điểm yêu thích
    if request.method == 'POST' and 'location_code' in request.POST:
        location_code = request.POST.get('location_code')
        location_list = Location_List.objects.filter(user=request.user).first()
        
        if location_code and location_list:
            location = location_list.location_set.filter(code=location_code).first()
            if location:
                location_list.location_set.remove(location)
                messages.success(request, "Đã xoá địa điểm khỏi danh sách yêu thích.")
                
        return redirect('favourite')

    # Lấy danh sách địa điểm yêu thích của người dùng
    location_list = Location_List.objects.filter(user=request.user).first()        
    locations = location_list.location_set.all() if location_list else []

    return render(request, "favourite/favourite.html", {
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

        # Lấy các location_id đã được chọn (qua checkbox)
        selected_ids = request.POST.getlist('locations')
        if not selected_ids:
            messages.error(request, "Vui lòng chọn ít nhất một địa điểm.")
            return redirect('favourite')

        # Chỉ lấy các location được chọn
        locations = list(location_list.location_set.filter(id__in=selected_ids))
        if not locations:
            messages.error(request, "Không tìm thấy các địa điểm đã chọn.")
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
        # Chỉ xoá các địa điểm đã sử dụng trong chuyến đi
        location_list.location_set.remove(*locations)

        return redirect('my_trip')

    # GET: Lấy và hiển thị các TripPath
    trip_paths = TripPath.objects.filter(trip_list=trip_list).order_by('-created_at')

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

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import Comment, Location

# @login_required
# def post_comment(request, location_code):
#     if request.method == 'POST':
#         content = request.POST.get('content', '').strip()
#         rating = request.POST.get('rating')  # This comes as a string
#         location = get_object_or_404(Location, code=location_code)

#         if not content:
#             return redirect('location_display', location_code=location_code)

#         bot_reply = "Thanks for your comment!"  # Default fallback reply

#         if not rating:
#             sentiment = predict_sentiment(content)
#             if sentiment == "positive":
#                 bot_reply = "We're thrilled you had a great time! Hope to see you again!"
#             elif sentiment == "negative":
#                 bot_reply = "We're sorry to hear that. Your feedback helps us get better."
#             else:
#                 bot_reply = "Thank you for sharing your thoughts. We appreciate your input!"

#             rating = None  # Explicitly set to None if not rated
#         else:
#             rating = int(rating)  # Convert string to integer
#             if rating == 5:
#                 bot_reply = "Awesome! We're thrilled you loved it!"
#             elif rating == 4:
#                 bot_reply = "Great! Glad you had a good time."
#             elif rating == 3:
#                 bot_reply = "Thanks! We'll try to make your next visit even better."
#             elif rating == 2:
#                 bot_reply = "Sorry to hear that. We hope things improve."
#             elif rating == 1:
#                 bot_reply = "We sincerely apologize. Your feedback is valuable to us."
#             else:
#                 bot_reply = "Thanks for your feedback!"

#         Comment.objects.create(
#             location=location,
#             user=request.user,
#             content=content,
#             rating=rating,
#             bot_reply=bot_reply
#         )

#     return redirect('location_display', location_code=location_code)
