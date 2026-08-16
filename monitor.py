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


# ----------------------------------------
# Gespeicherte Filme laden
# ----------------------------------------

try:

    with open("seen.json", "r", encoding="utf-8") as file:
        seen = json.load(file)

except FileNotFoundError:

    seen = {}


print(f"Bereits bekannte Filme: {len(seen)}")
print()


try:

    # ----------------------------------------
    # MediathekViewWeb abfragen
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

        if channel not in allowed_channels:
            continue

        if "audiodeskription" in title.lower():
            continue

        candidates.append(film)


    print(f"API-Ergebnisse: {len(results)}")
    print(f"Film-Kandidaten nach Filter: {len(candidates)}")


    # ----------------------------------------
    # Dubletten entfernen
    # ----------------------------------------

    unique_films = {}

    for film in candidates:

        website = film.get("url_website", "")

        if not website:
            website = film.get("id", "")

        if website not in unique_films:
            unique_films[website] = film


    unique_films = list(unique_films.values())

    print(f"Nach Entfernen von Dubletten: {len(unique_films)}")
    print()


    # ----------------------------------------
    # Neue Filme erkennen
    # ----------------------------------------

    new_films = []

    for film in unique_films:

        website = film.get("url_website", "")

        if not website:
            website = film.get("id", "")

        if website not in seen:

            new_films.append(film)


    print(f"NEUE Filme: {len(new_films)}")
    print()


    # ----------------------------------------
    # Neue Filme anzeigen
    # ----------------------------------------

    if new_films:

        for number, film in enumerate(new_films, start=1):

            title = film.get("title", "Unbekannt")
            channel = film.get("channel", "Unbekannt")
            duration = film.get("duration", 0)
            timestamp = film.get("timestamp")
            website = film.get("url_website", "")

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
            print(f"   Link: {website}")
            print()


    else:

        print("Keine neuen Filme gefunden.")


    # ----------------------------------------
    # Neue Filme speichern
    # ----------------------------------------

    today = datetime.now().strftime("%Y-%m-%d")

    for film in new_films:

        website = film.get("url_website", "")

        if not website:
            website = film.get("id", "")

        seen[website] = {
            "title": film.get("title", ""),
            "channel": film.get("channel", ""),
            "first_seen": today
        }


    # ----------------------------------------
    # seen.json speichern
    # ----------------------------------------

    with open(
        "seen.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            seen,
            file,
            indent=2,
            ensure_ascii=False
        )


    print("----------------------------------------")
    print(f"Gespeicherte Filme insgesamt: {len(seen)}")
    print("----------------------------------------")


except Exception as e:

    print("FEHLER:")
    print(e)


print("========================================")
