import urllib.request
import json
from datetime import datetime


print("========================================")
print("Mediathek Monitor")
print("========================================")
print("Lade aktuelle Mediathek-Daten...")


url = "https://mediathekviewweb.de/api/query"

query = {
    "queries": [],
    "sortBy": "timestamp",
    "sortOrder": "desc",
    "future": False,
    "offset": 0,
    "size": 100,
    "duration_min": 70 * 60
}


try:
    data = json.dumps(query).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    results = result["result"]["results"]

    print("Verbindung erfolgreich!")
    print()
    print(f"Gefundene Kandidaten: {len(results)}")
    print()

    for number, film in enumerate(results, start=1):

        title = film.get("title", "Unbekannt")
        channel = film.get("channel", "Unbekannt")
        duration = film.get("duration", 0)
        timestamp = film.get("timestamp")
        website = film.get("url_website", "")
        film_id = film.get("id", "")

        minutes = round(duration / 60)

        if timestamp:
            date = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y")
        else:
            date = "Unbekannt"

        print(f"{number}. {title}")
        print(f"   Sender: {channel}")
        print(f"   Dauer: {minutes} Minuten")
        print(f"   Datum: {date}")
        print(f"   ID: {film_id}")
        print(f"   Link: {website}")
        print()

except Exception as e:
    print("FEHLER:")
    print(e)


print("========================================")
