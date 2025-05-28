import requests
from bs4 import BeautifulSoup
import csv

URL = "https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_tuy%E1%BA%BFn_xe_bu%C3%BDt_Th%C3%A0nh_ph%E1%BB%91_H%E1%BB%93_Ch%C3%AD_Minh"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

tables = soup.find_all("table", class_="wikitable")

with open("bus_route.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Số tuyến", "Lộ trình đi", "Lộ trình về", "Khoảng cách", "Giờ hoạt động", "Thời gian chuyến", "Giãn cách", "Loại xe", "Đơn vị vận hành"])

    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 9:
                # Xử lý cột đầu tiên (Số tuyến)
                first_td = cols[0]
                img = first_td.find("img")
                if img and img.has_attr("alt"):
                    so_tuyen = img["alt"].strip()
                else:
                    so_tuyen = first_td.get_text(strip=True)

                # Các cột còn lại
                data = [so_tuyen] + [col.get_text(strip=True).replace('\n', ' ') for col in cols[1:9]]
                writer.writerow(data)

print("Bus route csv has been created")