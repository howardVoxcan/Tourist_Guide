from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from location.coordinate import coordinate_dict
from location.models import Location, Location_List, TripPath, TripList, Comment, TemporaryTripCart, TemporaryUser
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from urllib import request
from datetime import datetime
from annotated_types import Len
from shapely import length
from .TSP import Graph, distance
import requests, joblib, os, spacy, json, traceback, logging
from django.conf import settings
from urllib.parse import urlencode

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
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'unauthenticated'}, status=401)

        code = request.POST.get('value')
        if not code:
            return redirect('favourite')

        try:
            selected = Location.objects.get(code=code)
        except Location.DoesNotExist:
            return JsonResponse({'error': 'Location not found'}, status=404)

        user = request.user

        # Thêm/xóa user vào favourited_by của Location
        if user in selected.favourited_by.all():
            selected.favourited_by.remove(user)
        else:
            selected.favourited_by.add(user)

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
                Q(address__icontains=search_query) |
                Q(tags__icontains=search_query)
            )

        all_of_locations = all_of_locations.order_by('open_time')

        user = request.user if request.user.is_authenticated else None

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
                if user and loc.favourited_by.filter(id=user.id).exists()
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

@login_required
def display_location(request, location_code): 
    location = get_object_or_404(Location, code=location_code)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        rating = request.POST.get('rating')

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
            try:
                rating = int(rating)
            except ValueError:
                rating = 3  # default rating if invalid

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
        # Lấy comment gốc (parent=None) và replies prefetch
        comments = Comment.objects.filter(location=location, parent=None).prefetch_related('replies').order_by('-created_at')

        # Tính sao hiển thị
        rating = round(location.rating * 2) / 2 if location.rating else 0
        full_stars = int(rating)
        has_half = (rating - full_stars) >= 0.5
        star_html = '<i class="fas fa-star"></i>' * full_stars
        if has_half:
            star_html += '<i class="fas fa-star-half-alt"></i>'
            empty_stars = 5 - full_stars - 1
        else:
            empty_stars = 5 - full_stars
        star_html += '<i class="far fa-star"></i>' * empty_stars

        # Biểu tượng yêu thích (dựa trên nhiều trường hợp, ví dụ bạn lưu favourite ở Location.favourited_by M2M)
        if request.user.is_authenticated and location.favourited_by.filter(id=request.user.id).exists():
            favourite_symbol = '<i class="fa-solid fa-heart"></i>'
        else:
            favourite_symbol = '<i class="fa-regular fa-heart"></i>'

        # Xử lý thời gian mở cửa
        lat, long = location.coordinate.split(", ")
        open_time = location.open_time.strftime("%H:%M") if location.open_time else "N/A"
        close_time = location.close_time.strftime("%H:%M") if location.close_time else "N/A"

        if open_time == "00:00" and close_time == "23:59":
            open_time_str = "All day"
        elif location.close_time and location.open_time and location.close_time < location.open_time:
            open_time_str = f"{open_time} - {close_time} (The next day)"
        else:
            open_time_str = f"{open_time} - {close_time}"

        return render(request, "display_location/display.html", {
            "code": location.code,
            "location_name": location.location,
            "type": location.type,
            "open_time": open_time_str,
            "ticket_info": location.ticket_info,
            "address": location.address,
            "image_path": location.image_path,
            "long_description": location.long_description,
            "favourite_symbol": favourite_symbol,
            "lat": lat,
            "long": long,
            "star_html": star_html,
            "comments": comments,
            "location_obj": location  # dùng cho form POST
        })

@login_required
def favourite(request):
    # Xử lý POST request để xóa địa điểm yêu thích
    if request.method == 'POST' and 'location_code' in request.POST:
        location_code = request.POST.get('location_code')

        if location_code:
            location = Location.objects.filter(code=location_code).first()
            if location and request.user in location.favourited_by.all():
                location.favourited_by.remove(request.user)
                messages.success(request, "Đã xoá địa điểm khỏi danh sách yêu thích.")
                
        return redirect('favourite')

    # Lấy danh sách địa điểm yêu thích của người dùng
    locations = Location.objects.filter(favourited_by=request.user)

    return render(request, "favourite/favourite.html", {
        'locations': locations
    })

@login_required
def my_trip(request):
    user = request.user
    trip_list_id = f"{user.username}-favourite"

    trip_list, _ = TripList.objects.get_or_create(id=trip_list_id, defaults={
        'user': user,
        'name': f"{user.username}'s Favourite Trip"
    })

    if request.method == 'POST':
        path_name = request.POST.get('path_name')
        if not path_name:
            return redirect('my_trip')

        selected_ids = request.POST.getlist('locations')
        if not selected_ids:
            messages.error(request, "Vui lòng chọn ít nhất một địa điểm.")
            return redirect('favourite')

        locations = list(Location.objects.filter(id__in=selected_ids, favourited_by=user))
        if not locations:
            messages.error(request, "Không tìm thấy các địa điểm đã chọn.")
            return redirect('favourite')

        id_to_index = {loc.id: idx for idx, loc in enumerate(locations)}
        index_to_id = {idx: loc.id for idx, loc in enumerate(locations)}
        coordinates = [loc.coordinate for loc in locations]

        pinned_positions = [None] * len(locations)
        fixed_position_flags = [False] * len(locations)
        precedence_constraints = []

        start_id_str = request.POST.get('start_point')
        end_id_str = request.POST.get('end_point')
        start_id = int(start_id_str) if start_id_str and start_id_str.isdigit() else None
        end_id = int(end_id_str) if end_id_str and end_id_str.isdigit() else None

        for loc in locations:
            loc_id = loc.id
            loc_id_str = str(loc_id)
            index = id_to_index[loc_id]

            pinned_str = request.POST.get(f'pinned_order_{loc_id_str}')
            if pinned_str and pinned_str.isdigit():
                pinned_index = int(pinned_str) - 1
                if 0 <= pinned_index < len(locations):
                    pinned_positions[pinned_index] = index
                    fixed_position_flags[pinned_index] = True

            after_id_str = request.POST.get(f'precedence_after_{loc_id_str}')
            if after_id_str and after_id_str.isdigit():
                after_id = int(after_id_str)
                if after_id in id_to_index:
                    precedence_constraints.append((id_to_index[after_id], index))

        # Calculate distances and durations
        distances = []
        durations_map = {}

        for i in range(len(coordinates)):
            for j in range(len(coordinates)):
                if i != j:
                    dist, duration = distance(coordinates[i], coordinates[j])
                    distances.append((i, j, dist))
                    durations_map[(i, j)] = duration

        graph = Graph(len(locations))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        start_index = id_to_index.get(start_id) if start_id in id_to_index else None
        end_index = id_to_index.get(end_id) if end_id in id_to_index else None

        path, cost = graph.find_hamiltonian_path(
            fixed_position=fixed_position_flags,
            precedence_constraints=precedence_constraints,
            start=start_index,
            end=end_index
        )

        if path is None:
            messages.error(request, "Không thể tạo lịch trình hợp lệ với các ràng buộc đã chọn.")
            return redirect('favourite')

        total_duration = sum(
            durations_map.get((path[i], path[i+1]), 0) for i in range(len(path) - 1)
        )

        ordered_location_ids = [index_to_id[i] for i in path]

        # Determine actual start and end Location objects
        start_point_obj = next((loc for loc in locations if loc.id == start_id), None)
        end_point_obj = next((loc for loc in locations if loc.id == end_id), None)

        TripPath.objects.create(
            trip_list=trip_list,
            path_name=path_name,
            locations_ordered=json.dumps(ordered_location_ids),
            total_distance=cost,
            total_duration=total_duration,
            start_point=start_point_obj,
            end_point=end_point_obj
        )

        # Unfavorite the locations that were just used
        for loc in locations:
            loc.favourited_by.remove(user)

        return redirect('my_trip')

    trip_paths = TripPath.objects.filter(trip_list=trip_list).order_by('-created_at')
    all_ids = []
    parsed_trip_paths = []

    for path in trip_paths:
        try:
            loc_ids = json.loads(path.locations_ordered)
        except json.JSONDecodeError:
            loc_ids = []

        all_ids.extend(loc_ids)

        parsed_trip_paths.append({
            'id': path.id,
            'path_name': path.path_name,
            'locations': loc_ids,
            'start_point': path.start_point.location if path.start_point else None,
            'end_point': path.end_point.location if path.end_point else None,
            'total_distance': round(path.total_distance / 1000, 1) if path.total_distance is not None else None,
            'total_duration': round(path.total_duration / 60, 1) if path.total_duration is not None else None,
            'created_at': path.created_at,
        })

    location_qs = Location.objects.filter(id__in=all_ids)
    location_map = {loc.id: loc.location for loc in location_qs}

    return render(request, 'my_trip/my_trip.html', {
        'trip_paths': parsed_trip_paths,
        'location_map': location_map
    })

@require_POST
@login_required
def delete_tripPath(request, path_id):
    if request.method != 'POST' or request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return HttpResponseForbidden()
    trip_path = get_object_or_404(TripPath, pk=path_id)
    if trip_path.trip_list.user != request.user:
        return HttpResponseForbidden()
    trip_path.delete()
    return JsonResponse({'status': 'deleted'})

@require_POST
@login_required
def submit_comment_ajax(request, location_code):
    content = request.POST.get('content', '').strip()
    rating = request.POST.get('rating')
    location = get_object_or_404(Location, code=location_code)

    if not content:
        return JsonResponse({'error': 'Empty content'}, status=400)

    bot_reply = "Thanks for your comment!"  # Fallback reply

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

    comment = Comment.objects.create(
        location=location,
        user=request.user,
        content=content,
        rating=rating,
        bot_reply=bot_reply
    )

    return JsonResponse({
        'username': request.user.username,
        'content': comment.content,
        'bot_reply': comment.bot_reply
    })

logger = logging.getLogger(__name__)

def extract_session_id(data, parameters):
    session_full = data.get('session', '')
    session_id = session_full.split('/')[-1] if session_full else None

    if not session_id and 'originalDetectIntentRequest' in data:
        session_id = data['originalDetectIntentRequest'].get('payload', {}).get('sessionId')

    if not session_id:
        session_id = parameters.get('session_id')

    return session_id

def normalize_locations(loc):
    if loc is None:
        return []
    if isinstance(loc, str):
        return [loc]
    if isinstance(loc, list):
        return loc
    return [str(loc)]

def get_or_create_temp_user(session_id):
    temp_user, _ = TemporaryUser.objects.get_or_create(session_id=session_id)
    return temp_user

def get_or_create_temp_cart(session_id, user=None):
    cart, created = TemporaryTripCart.objects.get_or_create(session_id=session_id, defaults={"user": user})
    if not created and cart.user is None and user is not None:
        cart.user = user
        cart.save()
    return cart

@csrf_exempt
def dialogflow_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        print(request.body)
        data = json.loads(request.body.decode("utf-8"))
        intent_name = data['queryResult']['intent']['displayName']
        parameters  = data['queryResult'].get('parameters', {})

        # Extract session and user
        session_id = extract_session_id(data, parameters)
        user_id    = data.get('originalDetectIntentRequest', {}) \
                         .get('payload', {}) \
                         .get('userId') or parameters.get('user_id')

        user = None
        if user_id:
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

        result = handle_intent(request, intent_name, parameters, user, session_id)

        if result is True:
            return JsonResponse({"fulfillmentText": data['queryResult'].get('fulfillmentText', "Done.")})
        elif isinstance(result, str):
            return JsonResponse({"fulfillmentText": result})
        else:
            return JsonResponse({"fulfillmentText": "Unhandled case."})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "fulfillmentText": "An error occurred while processing your request.",
            "debug": str(e)
        })

def handle_intent(request, intent_name, parameters, user=None, session_id=None):
    if not session_id:
        try:
            data = json.loads(request.body.decode("utf-8"))
            session_id = extract_session_id(data, parameters)
        except:
            pass
    if not session_id:
        return "Missing session ID."

    if user is None:
        user = get_or_create_temp_user(session_id)

    try:
        trip_cart_obj = get_or_create_temp_cart(session_id, user)
    except Exception as e:
        return "Could not create or access your trip session."

    locations_list = normalize_locations(parameters.get("locations") or [])

    if intent_name in ["Default Welcome Intent", "Default Fallback Intent", "discovering.ability"]:
        return True

    elif intent_name == "favourite.add.location":
        if not user or isinstance(user, TemporaryUser):
            return "Please log in to add favourites."
        if not locations_list:
            return "Please specify a location to add."
        for loc in locations_list:
            try:
                location_obj = Location.objects.get(location__iexact=loc)
                location_obj.favourited_by.add(user)
            except Location.DoesNotExist:
                return f"Location '{loc}' does not exist."
        return True

    elif intent_name == "favourite.remove.location":
        if not user or isinstance(user, TemporaryUser):
            return "Please log in to remove favourites."
        if not locations_list:
            return "Please specify a location to remove."
        for loc in locations_list:
            try:
                location_obj = Location.objects.get(location__iexact=loc)
                location_obj.favourited_by.remove(user)
            except Location.DoesNotExist:
                return f"Location '{loc}' does not exist."
        return True

    elif intent_name == "find.location.particular":
        if not locations_list:
            return "Please specify the location you're looking for."
        for loc in locations_list:
            try:
                location_obj = Location.objects.get(location__iexact=loc)
                location_url = reverse('display_location', args=[location_obj.code])
                return f"Here is the path: {location_url}"
            except Location.DoesNotExist:
                return f"Sorry, I couldn't find a location named '{loc}'."

    elif intent_name == "find.location.tags":
        tag = parameters.get("tags")
        if not tag:
            return "Please provide a tag to search for."
        if isinstance(tag, list):
            tag = tag[0]
        base_url = reverse('locations')
        query_string = urlencode({'search': tag})
        return f"Here's a location search result for tag '{tag}': {base_url}?{query_string}"

    elif intent_name == "start.trip":
        trip_cart_obj.locations = []
        trip_cart_obj.start_location = None
        trip_cart_obj.end_location = None
        trip_cart_obj.save()
        return True

    elif intent_name == "set.start.location":
        if locations_list:
            trip_cart_obj.start_location = locations_list[0]
            trip_cart_obj.save()
            return True
        return "Please tell me which location to set as the starting point."

    elif intent_name == "set.end.location":
        if locations_list:
            trip_cart_obj.end_location = locations_list[0]
            trip_cart_obj.save()
            return True 
        return "Please tell me which location to set as the ending point."

    elif intent_name == "trip.create.add.location":
        updated = False
        for loc in locations_list:
            if loc not in trip_cart_obj.locations:
                trip_cart_obj.locations.append(loc)
                updated = True
        if updated:
            trip_cart_obj.save()
            return True
        return "Those locations are already in your trip."

    elif intent_name == "trip.create.remove.location":
        removed, not_found = [], []
        for loc in locations_list:
            if loc in trip_cart_obj.locations:
                trip_cart_obj.locations.remove(loc)
                removed.append(loc)
            else:
                not_found.append(loc)
        trip_cart_obj.save()
        if removed and not not_found:
            return f"Removed {', '.join(removed)} from your trip."
        if removed and not_found:
            return f"Removed {', '.join(removed)}. However, {', '.join(not_found)} were not in your trip list."
        return f"{', '.join(not_found)} is/are not in your trip list."

    elif intent_name == "trip.create.complete":
        locations = trip_cart_obj.locations or []
        start_name = trip_cart_obj.start_location
        end_name = trip_cart_obj.end_location

        if not locations and not (start_name and end_name):
            return "Your trip has no locations. Please add some before finishing."

        # Normalize existing location names (lowercase) for comparison
        existing = [loc.lower() for loc in locations]

        updated = False
        # Force inclusion of start location at the beginning if missing
        if start_name and start_name.lower() not in existing:
            locations.insert(0, start_name)
            updated = True

        # Update existing after possible start insertion
        existing = [loc.lower() for loc in locations]

        # Force inclusion of end location at the end if missing
        if end_name and end_name.lower() not in existing:
            locations.append(end_name)
            updated = True

        # Save updated locations back to trip_cart_obj if changed
        if updated:
            trip_cart_obj.locations = locations
            trip_cart_obj.save()

        locations = trip_cart_obj.locations

        middles = [loc for loc in locations if loc not in (start_name, end_name)]

        ordered_names = []
        if start_name:
            ordered_names.append(start_name)
        ordered_names.extend(middles)
        if end_name:
            ordered_names.append(end_name)

        loc_objs = list(Location.objects.filter(location__in=ordered_names))
        found = {l.location for l in loc_objs}
        missing = [n for n in ordered_names if n not in found]
        if missing:
            logger.warning(f"[DEBUG] Missing from DB: {missing}")
        else:
            logger.debug("[DEBUG] All names found in DB.")

        name2obj = {l.location: l for l in loc_objs}
        location_list = [name2obj[n] for n in ordered_names if n in name2obj]
        final_names = [loc.location for loc in location_list]
        logger.debug(f"[DEBUG] location_list used: {final_names}")

        coords = [loc.coordinate for loc in location_list]
        index_to_id = {i: location_list[i].id for i in range(len(location_list))}
        distances, durations = [], {}
        for i in range(len(coords)):
            for j in range(len(coords)):
                if i == j: continue
                d, t = distance(coords[i], coords[j])
                distances.append((i, j, d))
                durations[(i, j)] = t

        graph = Graph(len(location_list))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        start_idx = 0
        end_idx = (len(ordered_names) - 1) if end_name else start_idx
        logger.debug(f"[DEBUG] start_idx={start_idx}, end_idx={end_idx}")

        best_path, total_dist = graph.find_hamiltonian_path(
            fixed_position=None,
            precedence_constraints=None,
            start=start_idx,
            end=end_idx
        )
        if not best_path:
            logger.error("[DEBUG] No valid path found.")
            return "Unable to generate a valid trip with the selected start/end points."

        if best_path[0] == best_path[-1]:
            best_path = best_path[:-1]
        logger.debug(f"[DEBUG] best_path indices: {best_path}")

        total_time = sum(
            durations.get((best_path[i], best_path[i+1]), 0)
            for i in range(len(best_path)-1)
        )

        itinerary_names = [location_list[i].location for i in best_path]
        logger.debug(f"[DEBUG] itinerary: {itinerary_names}")

        header = [
            f"Total distance: {total_dist:.1f} km",
            f"Total duration: {total_time:.1f} minutes",
            ""
        ]
        reply = "\n".join(header + itinerary_names)

        trip_list, _ = TripList.objects.get_or_create(user=user)
        trip_path = TripPath.objects.create(
            trip_list=trip_list,
            total_duration=total_time,
            total_distance=total_dist,
            locations_ordered=json.dumps([index_to_id[i] for i in best_path]),
            path_name=f"{user.username} chatbot TripPath"
        )
        trip_path.locations.add(*[location_list[i] for i in best_path])
        trip_path.save()

        url = reverse('my_trip') + "?" + urlencode({'id': trip_list.id})
        return f"{reply}\n\nView it here: {url}"

    return False
