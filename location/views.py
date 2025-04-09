from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from location.coordinate import coordinate_dict
import requests

# Create your views here.
# coordinate = {
#     "Phở 2000": "10.772781373025383,106.69683415119852",
#     "Nhà hàng Ngon": "10.777431597180907,106.69966496269389",
#     "Bánh mì Huỳnh Hoa": "10.771538258137092,106.69239630471262",
#     "The Workshop Coffee": "10.773492596028692,106.70560211593205",
#     "Café de Saigon1982": "10.789157041898187,106.72051729737827",
#     "Bún Riêu Gánh": "10.773954126653559,106.6989505018455",
#     "Bún Riêu Nguyễn Cảnh Chân": "10.757959270546952,106.68875996787892",
#     "Cháo Ếch Singapore Tân Định": "10.78957033538437,106.69003668478365",
#     "Bánh mì Bùi Thị Xuân": "10.76990234809769,106.68822340127019",
#     "The Hammock Hotel Fine Arts Museum": "10.769577718488765,106.70013936044538",
#     "New World Saigon Hotel": "10.770886322934372,106.69518896994596",
#     "Brand New Cozy Home at the heart of SG": "10.790981692967119,106.70539698240043",
#     "Loan Vo Hostel": "10.768376481937562,106.693279148739",
#     "Rex Hotel": "10.775882181316215,106.7012839915867",
#     "Bưu Điện": "10.779842659449939,106.69996820993975",
#     "Công Viên Tao Đàn": "10.774553608778882,106.69244078025946",
#     "Đường Sách": "10.780977944667105,106.70007230244788",
#     "Nhà Thờ Đức Bà": "10.779800051912392,106.69901831414568",
#     "Bến Nhà Rồng": "10.76818190356668,106.70686546017299",
#     "Dinh Độc Lập": "10.77700907919212,106.69530175013531",
#     "Thảo Cầm Viên": "10.787348494748628,106.70505598909709",
#     "Bảo Tàng Lịch Sử": "10.788089045344142,106.70472839931904",
#     "Địa Đạo Củ Chi": "11.141406968354879,106.46213251440814",
#     "Khu Du Lịch Suối Tiên": "10.866201554204098,106.80316714763133",
#     "Đầm Sen": "10.766112351874305,106.64189326571174",
#     "Amazing Bay": "10.877317901664275,106.87180222073606",
#     "Phố Đi Bộ Nguyễn Huệ": "10.774081444635982,106.70365374783108",
#     "Landmark 81": "10.795125935851562,106.72209500604045",
#     "Công Viên 23/9": "10.76872651216932,106.69233930003966",
#     "Tour Sông Sài Gòn": "10.775147854572639,106.7070956598377",
#     "Chợ Bến Thành": "10.772531992029178,106.69802077811163",
#     "Aeon Mall Tân Phú": "10.801511051610603,106.61742407858719"
# }

def weather(request):
    api_key = "cef48da67bcd47dd8d165800250804"
    location = coordinate_dict["Aeon Mall Tân Phú"]
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"

    response = requests.get(url)
    data = response.json()

    # print(f"Location: {data['location']['name']}")
    # print(f"Temperature: {data['current']['temp_c']}°C")
    # print(f"Condition: {data['current']['condition']['text']}")

    return render(request, "location/location.html",{
        "Location": data['location']['name'],
        "Temperature": f"{data['current']['temp_c']}°C or {data['current']['temp_f']}°F",
        "Condition": (data['current']['condition']['text']).lower()
    })


