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


allowed_channels = {
    "ARD",
    "BR",
    "HR",
    "MDR",
    "NDR",
    "RB",
    "RBB",
    "SWR",
    "WDR",
    "SR",
    "ONE",
    "ZDF",
    "ZDFneo",
    "ZDFinfo",
    "3sat"
}


try:

    # ----------------------------------------
    # Daten von MediathekViewWeb holen
    # ----------------------------------------

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


    # ----------------------------------------
    # Erste Filterung
    # ----------------------------------------

    candidates = []

    for film in results:

        title = film.get("title", "")
        channel = film.get("channel", "")

        # Nur gewünschte Sender
        if channel not in allowed_channels:
            continue

        # Audiodeskription entfernen
        if "audiodeskription" in title.lower():
            continue

        candidates.append(film)


    print(f"API-Ergebnisse: {len(results)}")
    print(f"Film-Kandidaten nach Filter: {len(candidates)}")
    print()


    # ----------------------------------------
    # Dubletten anhand des Mediathek-Links
    # ----------------------------------------

    unique_films = {}

    for film in candidates:

        website = film.get("url_website", "")

        # Falls kein Link vorhanden ist,
        # benutzen wir zur Sicherheit die ID
        if not website:
            website = film.get("id", "")

        if website not in unique_films:
            unique_films[website] = film


    unique_films = list(unique_films.values())


    print(f"Nach Entfernen von Dubletten: {len(unique_films)}")
    print()


    # ----------------------------------------
    # Ergebnisse anzeigen
    # ----------------------------------------

    for number, film in enumerate(unique_films, start=1):

        title = film.get("title", "Unbekannt")
        channel = film.get("channel", "Unbekannt")
        duration = film.get("duration", 0)
        timestamp = film.get("timestamp")
        website = film.get("url_website", "")
        film_id = film.get("id", "")

        minutes = round(duration / 60)

        if timestamp:
            date = datetime.fromtimestamp(
                timestamp
            ).strftime("%d.%m.%Y")
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
