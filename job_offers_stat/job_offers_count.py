import requests
import csv
from datetime import date

cities = ["Poznań", "Wrocław", "Kraków", "Warszawa", "Gdańsk", "Łódź"]
categories = {"Testing": 11, "Python": 5}
url = "https://api.justjoin.it/v2/user-panel/offers/count?&cityRadiusKm=30&" \
      "remoteWorkOptions[]=hybrid&remoteWorkOptions[]=office"

results = []

today = date.today().isoformat()  # np. 2025-12-08

for city in cities:
    row = {"Date": today, "City": city}

    for category_name, category_id in categories.items():
        params = {
            "city": city,
            "cityRadiusKm": 30,
            "remoteWorkOptions[]": ["hybrid", "office"],
            "technologies[]": category_id
        }

        r = requests.get(f"{url}&city={city}&categories[]={category_id}")
        data = r.json()
        row[category_name] = data.get("count", 0)

    results.append(row)

# zapis – dopisujemy, jeśli plik istnieje
filename = "offers_history.csv"
file_exists = False
try:
    with open(filename, "r", encoding="utf-8"):
        file_exists = True
except FileNotFoundError:
    pass

with open(filename, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Date", "City", "Testing", "Python"])
    if not file_exists:
        writer.writeheader()
    writer.writerows(results)
