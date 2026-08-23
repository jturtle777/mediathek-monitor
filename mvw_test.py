import urllib.request
import json
from datetime import datetime


# ========================================
# EINSTELLUNGEN
# ========================================

SIZE = 1000

MIN_DURATION = 70

URL = "https://mediathekviewweb.de/api/query"


# ========================================
# MEDIATHEKVIEWWEB ABFRAGE
# ========================================

query = {
    "queries": [],
    "sortBy": "timestamp",
    "sortOrder": "desc",
    "future": False,
    "offset": 0,
    "size": SIZE,
    "duration_min": MIN_DURATION * 60
}


print("=" * 80)
print("MEDIATHEKVIEWWEB TEST")
print("=" * 80)
print()

print(f"Angeforderte Treffer: {SIZE}")
print(f"Mindestdauer:         {MIN_DURATION} Minuten")
print(f"Sortierung:           timestamp absteigend")
print()

print("Starte Abfrage...")
print()


# ========================================
# API ABFRAGEN
# ========================================

try:

    data = json.dumps(
        query
    ).encode("utf-8")


    request = urllib.request.Request(

        URL,

        data=data,

        headers={
            "Content-Type": "application/json",
            "User-Agent": "MediathekViewWeb-Test/1.0"
        },

        method="POST"
    )


    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )


except Exception as e:

    print("FEHLER BEI DER API-ABFRAGE:")
    print()
    print(e)
    print()

    raise SystemExit(1)


# ========================================
# ERGEBNISSE AUSLESEN
# ========================================

try:

    results = result["result"]["results"]

except (KeyError, TypeError):

    print("Unerwartete Antwort der MediathekViewWeb-API:")
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    raise SystemExit(1)


print("Abfrage erfolgreich!")
print()

print("=" * 80)
print("ERGEBNISSE")
print("=" * 80)
print()

print(f"Angeforderte Größe: {SIZE}")
print(f"Tatsächlich erhalten: {len(results)}")
print()


# ========================================
# EINZELNE ERGEBNISSE
# ========================================

timestamps = []


for number, film in enumerate(
    results,
    start=1
):

    title = film.get(
        "title",
        ""
    )

    channel = film.get(
        "channel",
        ""
    )

    duration = film.get(
        "duration",
        0
    )

    timestamp = film.get(
        "timestamp"
    )

    website = film.get(
        "url_website",
        ""
    )

    size = film.get(
        "size"
    )


    # ------------------------------------
    # TIMESTAMP UMWANDELN
    # ------------------------------------

    if timestamp is not None:

        try:

            date_string = datetime.fromtimestamp(
                timestamp
            ).strftime(
                "%d.%m.%Y %H:%M:%S"
            )

            timestamps.append(
                timestamp
            )

        except Exception:

            date_string = "ungültiger Timestamp"

    else:

        date_string = "kein Timestamp"


    # ------------------------------------
    # DAUER
    # ------------------------------------

    if duration:

        duration_minutes = round(
            duration / 60
        )

    else:

        duration_minutes = 0


    # ------------------------------------
    # AUSGABE
    # ------------------------------------

    print("-" * 80)

    print(
        f"#{number}"
    )

    print(
        f"Titel:       {title}"
    )

    print(
        f"Sender:      {channel}"
    )

    print(
        f"Dauer:       {duration_minutes} Minuten"
    )

    print(
        f"Timestamp:   {timestamp}"
    )

    print(
        f"Datum/Zeit:  {date_string}"
    )

    print(
        f"Size:        {size}"
    )

    print(
        f"URL:         {website}"
    )


print("-" * 80)
print()


# ========================================
# ZEITRAUM DER 1000 TREFFER
# ========================================

print("=" * 80)
print("ZEITRAUM DER ABFRAGE")
print("=" * 80)
print()


if timestamps:

    newest_timestamp = max(
        timestamps
    )

    oldest_timestamp = min(
        timestamps
    )


    newest_date = datetime.fromtimestamp(
        newest_timestamp
    ).strftime(
        "%d.%m.%Y %H:%M:%S"
    )


    oldest_date = datetime.fromtimestamp(
        oldest_timestamp
    ).strftime(
        "%d.%m.%Y %H:%M:%S"
    )


    time_difference = (
        newest_timestamp
        - oldest_timestamp
    )


    hours = time_difference / 3600


    print(
        f"NEUESTER Treffer:"
    )

    print(
        f"   Timestamp: {newest_timestamp}"
    )

    print(
        f"   Datum:     {newest_date}"
    )

    print()


    print(
        f"ÄLTESTER Treffer:"
    )

    print(
        f"   Timestamp: {oldest_timestamp}"
    )

    print(
        f"   Datum:     {oldest_date}"
    )

    print()


    print(
        f"Zeitspanne der {len(results)} Treffer:"
    )

    print(
        f"   {hours:.2f} Stunden"
    )

    print(
        f"   {hours / 24:.2f} Tage"
    )

else:

    print(
        "Keine Ergebnisse mit Timestamp gefunden."
    )


# ========================================
# WICHTIG FÜR 12-STUNDEN-INTERVALL
# ========================================

print()

print("=" * 80)
print("BEURTEILUNG FÜR 12-STUNDEN-INTERVALL")
print("=" * 80)
print()


if timestamps:

    if hours >= 12:

        print(
            "OK: Die 1000 Treffer decken mindestens "
            "12 Stunden ab."
        )

        print()

        print(
            "Damit reicht die aktuelle Treffergröße "
            "grundsätzlich über ein 12-Stunden-Intervall."
        )

    else:

        print(
            "ACHTUNG: Die 1000 Treffer decken "
            "weniger als 12 Stunden ab!"
        )

        print()

        print(
            "Es besteht die Gefahr, dass zwischen zwei "
            "Ausführungen Filme aus dem Abfragefenster "
            "herausfallen."
        )


print()

print("=" * 80)
print("TEST BEENDET")
print("=" * 80)
