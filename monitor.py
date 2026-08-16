import urllib.request
import json
from datetime import datetime


print("========================================")
print("Mediathek Monitor")
print("========================================")
print("Verbinde mit MediathekViewWeb...")


url = "https://mediathekviewweb.de/api/query"

query = {
    "queries": [
        {
            "fields": ["title"],
            "query": "Tatort"
        }
    ],
    "size": 5
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

    print("Verbindung erfolgreich!")
    print()

    results = result["result"]["results"]

    print(f"Gefundene Treffer: {len(results)}")
    print()

    for number, film in enumerate(results, start=1):

        title = film.get("title", "Unbekannt")
        channel = film.get("channel", "Unbekannt")
        duration = film.get("duration", 0)
        timestamp = film.get("timestamp")

        # Sekunden in Minuten umrechnen
        minutes = round(duration / 60)

        # Unix-Timestamp in ein lesbares Datum umwandeln
        if timestamp:
            date = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y")
        else:
            date = "Unbekannt"

        print(f"{number}. {title}")
        print(f"   Sender: {channel}")
        print(f"   Dauer: {minutes} Minuten")
        print(f"   Datum: {date}")
        print()


except Exception as e:
    print("FEHLER:")
    print(e)


print("========================================")
