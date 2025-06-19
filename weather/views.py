from django.shortcuts import render
import requests

# Create your views here.
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

        for hour_data in day['hour'][::2]: 
            periods.append({
                'time': hour_data['time'][11:], 
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

    return render(request, 'weather.html', context)