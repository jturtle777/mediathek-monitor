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
    "sortBy": "filmlisteTimestamp",
    "sortOrder": "desc",
    "size": 20
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
    print(f"Gefundene Einträge: {len(results)}")
    print()

    for number, film in enumerate(results, start=1):

        title = film.get("title", "Unbekannt")
        channel = film.get("channel", "Unbekannt")
        duration = film.get("duration", 0)
        timestamp = film.get("timestamp")
        film_timestamp = film.get("filmlisteTimestamp")

        minutes = round(duration / 60)

        if timestamp:
            date = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y")
        else:
            date = "Unbekannt"

        if film_timestamp:
            film_date = datetime.fromtimestamp(
                film_timestamp
            ).strftime("%d.%m.%Y %H:%M")
        else:
            film_date = "Unbekannt"

        print(f"{number}. {title}")
        print(f"   Sender: {channel}")
        print(f"   Dauer: {minutes} Minuten")
        print(f"   Inhaltsdatum: {date}")
        print(f"   Filmliste: {film_date}")
        print()

except Exception as e:
    print("FEHLER:")
    print(e)


print("========================================")
