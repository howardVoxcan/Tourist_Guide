from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from location.coordinate import coordinate_dict
from location.models import Location, Location_List, TripPath, TripList, Comment
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from urllib import request
from datetime import datetime
from annotated_types import Len
from shapely import length
from .TSP import Graph, distance
import requests, joblib, os, spacy, json
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
                Q(address__icontains=search_query) |
                Q(tags__icontains=search_query)
            )

        all_of_locations = all_of_locations.order_by('open_time')

        if request.user.is_authenticated:
            location_list = Location_List.objects.filter(user=request.user).first()
        else:
            location_list = None

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

    trip_list, _ = TripList.objects.get_or_create(id=trip_list_id, defaults={
        'user': user,
        'name': f"{user.username}'s Favourite Trip"
    })

    if request.method == 'POST':
        path_name = request.POST.get('path_name')
        if not path_name:
            return redirect('my_trip')

        location_list = Location_List.objects.filter(user=user).first()
        if not location_list:
            return redirect('favourite')

        selected_ids = request.POST.getlist('locations')
        if not selected_ids:
            messages.error(request, "Vui lòng chọn ít nhất một địa điểm.")
            return redirect('favourite')

        locations = list(location_list.location_set.filter(id__in=selected_ids))
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

        total_duration = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            total_duration += durations_map.get((u, v), 0)

        ordered_location_ids = [index_to_id[i] for i in path]

        TripPath.objects.create(
            trip_list=trip_list,
            path_name=path_name,
            locations_ordered=json.dumps(ordered_location_ids),
            total_distance=cost,
            total_duration=total_duration
        )

        location_list.location_set.remove(*locations)

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
            'path_name': path.path_name,
            'locations': loc_ids,
            'distance': round(path.total_distance / 1000, 1),
            'duration': round(path.total_duration/ 60, 1) if path.total_duration else None,
            'created_at': path.created_at
        })

    location_qs = Location.objects.filter(id__in=all_ids)
    location_map = {loc.id: loc.location for loc in location_qs}

    return render(request, 'my_trip/my_trip.html', {
        'trip_paths': parsed_trip_paths,
        'location_map': location_map
    })

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

@csrf_exempt
def dialogflow_webhook(request):
    if request.method == "POST":
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({"fulfillmentText": "Please log in to use the chatbot."}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            intent_name = data['queryResult']['intent']['displayName']
            parameters = data['queryResult'].get('parameters', {})

            result = handle_intent(request, intent_name, parameters, user)

            if result is True:
                # Use Dialogflow's own response
                fulfillment_text = data['queryResult'].get('fulfillmentText', "")
                return JsonResponse({"fulfillmentText": fulfillment_text})
            elif isinstance(result, str):
                # Custom error or other message
                return JsonResponse({"fulfillmentText": result})
            else:
                return JsonResponse({"fulfillmentText": "Unhandled case."})

        except Exception as e:
            return JsonResponse({
                "fulfillmentText": "An error occurred while processing your request.",
                "debug": str(e)
            })

    return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

def handle_intent(request, intent_name, parameters, user):
    session = request.session
    trip_cart = session.get("trip_cart", {
        "locations": [],
        "start_location": None,
        "end_location": None
    })

    if intent_name == "Default Welcome Intent":
        return True

    elif intent_name == "Default Fallback Intent":
        return True

    elif intent_name == "discovering.ability":
        return True

    elif intent_name == "favourite.add.location":
        locations = parameters.get("locations")
        if not locations:
            return "Please specify a location to add."

        if isinstance(locations, str):
            locations = [locations]

        for loc in locations:
            exists = Location_List.objects.filter(user=user, name=loc).exists()
            if exists:
                return f"The location '{loc}' is already in your favourite list."
            Location_List.objects.create(user=user, name=loc)

        return True

    elif intent_name == "favourite.remove.location":
        locations = parameters.get("locations")
        if not locations:
            return "Please specify a location to remove."

        if isinstance(locations, str):
            locations = [locations]

        for loc in locations:
            exists = Location_List.objects.filter(user=user, name=loc).exists()
            if not exists:
                return f"The location '{loc}' is not in your favourite list."
            Location_List.objects.filter(user=user, name=loc).delete()

        return True

    elif intent_name == "find.location.particular":
        locations = parameters.get("locations")
        if not locations:
            return "Please specify the location you're looking for."

        if isinstance(locations, str):
            locations = [locations]

        for loc in locations:
            try:
                location_obj = Location.objects.get(name__iexact=loc)
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
        full_url = f"{base_url}?{query_string}"

        return f"Here's a location search result for tag '{tag}': {full_url}"

    elif intent_name == "start.trip":
        trip_cart = {"locations": [], "start_location": None, "end_location": None}
        session["trip_cart"] = trip_cart
        return "Great! Let's start planning your trip. You can now add locations."

    elif intent_name == "set.start.location":
        location = parameters.get("locations")
        if location:
            trip_cart["start_location"] = location
            request.session.modified = True
            return f"Start location set to {location}."
        return "Please tell me which location to set as the starting point."

    elif intent_name == "set.end.location":
        location = parameters.get("locations")
        if location:
            trip_cart["end_location"] = location
            request.session.modified = True
            return f"End location set to {location}."
        return "Please tell me which location to set as the ending point."

    elif intent_name == "trip.create.add.location":
        location = parameters.get("locations")
        if location:
            trip_cart["locations"].append(location)
            request.session.modified = True
            return f"Added {location} to your trip."
        return "Please specify a location to add."

    elif intent_name == "trip.create.remove.location":
        location = parameters.get("locations")
        if location in trip_cart["locations"]:
            trip_cart["locations"].remove(location)
            request.session.modified = True
            return f"Removed {location} from your trip."
        return f"{location} is not in your trip list."

    elif intent_name == "trip.create.complete":
        locations = trip_cart.get("locations", [])
        start_name = trip_cart.get("start_location")
        end_name = trip_cart.get("end_location")

        if not locations:
            return "Your trip has no locations. Please add some before finishing."

        all_location_names = list(set(locations + ([start_name] if start_name else []) + ([end_name] if end_name else [])))

        location_objs = list(Location.objects.filter(name__in=all_location_names))
        if len(location_objs) < len(all_location_names):
            return "Some locations could not be found in the database."

        name_to_obj = {loc.name: loc for loc in location_objs}

        location_list = []
        if start_name:
            location_list.append(name_to_obj[start_name])
        location_list += [name_to_obj[name] for name in locations if name != start_name and name != end_name]
        if end_name:
            location_list.append(name_to_obj[end_name])

        coordinates = [loc.coordinate for loc in location_list]
        id_map = {i: location_list[i].id for i in range(len(location_list))}

        distances = []
        durations_map = {}

        for i in range(len(coordinates)):
            for j in range(len(coordinates)):
                if i != j:
                    dist, duration = distance(coordinates[i], coordinates[j])
                    distances.append((i, j, dist))
                    durations_map[(i, j)] = duration

        graph = Graph(len(location_list))
        for u, v, w in distances:
            graph.add_edge(u, v, w)

        path, total_distance = graph.find_hamiltonian_cycle(start=start_name, end=end_name)
        if not path:
            return "Could not generate an optimal path. Try modifying locations."

        ordered_location_ids = [id_map[i] for i in path]

        total_duration = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            duration = durations_map.get((u, v), 0)
            total_duration += duration

        trip_list_id = f"{user.username}-favourite"
        trip_list, _ = TripList.objects.get_or_create(
            id=trip_list_id,
            defaults={"user": user, "name": f"{user.username}'s Trip"}
        )

        TripPath.objects.create(
            trip_list=trip_list,
            path_name="Chatbot Trip",
            locations_ordered=json.dumps(ordered_location_ids),
            total_distance=total_distance,
            total_duration=total_duration
        )

        session["trip_cart"] = {
            "locations": [],
            "start_location": None,
            "end_location": None
        }

        return f"Trip created successfully with {len(path)} stops. Estimated duration: {round(total_duration, 2)} minutes."

    else:
        return "This intent is not currently handled."