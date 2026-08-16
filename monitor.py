import urllib.request
import json
from datetime import datetime


# ========================================
# PERSÖNLICHE EINSTELLUNGEN
# ========================================

# Mindest- und Maximaldauer in Minuten
MIN_DURATION = 70
MAX_DURATION = 180


# Sender, die wir berücksichtigen wollen
ALLOWED_CHANNELS = {
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
    "3sat",
    "ORF"
}


# Begriffe, bei denen ein Eintrag ausgeschlossen wird.
#
# Die Prüfung erfolgt gegen Titel und Beschreibung.
#
# Dokumentationen und Serien werden zusätzlich
# über eigene Regeln ausgeschlossen.
EXCLUDE_KEYWORDS = [
    "audiodeskription",
    "sport",
    "nachrichten",
    "nachricht",
    "wetter",
    "talk",
    "talkshow",
    "magazin",
    "quiz",
    "gameshow",
    "game show",
    "fernsehgarten",
    "pressekonferenz",
    "journal"
]


# Begriffe, die sehr stark auf eine Serie hinweisen
SERIES_KEYWORDS = [
    "folge ",
    "staffel ",
    "episode ",
    "(s01/",
    "(s02/",
    "(s03/",
    "(s04/",
    "(s05/",
    "(s06/",
    "(s07/",
    "(s08/",
    "(s09/",
    "(s10/",
    "serie"
]


# Begriffe, die stark auf eine Dokumentation hinweisen
DOCUMENTARY_KEYWORDS = [
    "dokumentation",
    "doku",
    "reportage",
    "dokureihe",
    "dokumentarfilm"
]


# ========================================
# PROGRAMMSTART
# ========================================

print("========================================")
print("Mediathek Monitor")
print("========================================")
print("Lade aktuelle Mediathek-Daten...")
print()


# ========================================
# MediathekViewWeb API
# ========================================

url = "https://mediathekviewweb.de/api/query"


query = {
    "queries": [],
    "sortBy": "timestamp",
    "sortOrder": "desc",
    "future": False,
    "offset": 0,
    "size": 100,
    "duration_min": MIN_DURATION * 60
}


# ========================================
# Gespeicherte Filme laden
# ========================================

try:

    with open("seen.json", "r", encoding="utf-8") as file:
        seen = json.load(file)

except FileNotFoundError:

    seen = {}


print(f"Bereits bekannte Filme: {len(seen)}")
print()


# ========================================
# Statistik für Filter
# ========================================

stats = {
    "zu_kurz": 0,
    "zu_lang": 0,
    "falscher_sender": 0,
    "ausschluss_keyword": 0,
    "serie": 0,
    "dokumentation": 0,
    "audiodeskription": 0
}


try:

    # ========================================
    # API abfragen
    # ========================================

    data = json.dumps(query).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )


    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )


    results = result["result"]["results"]


    print("Verbindung erfolgreich!")
    print()


    # ========================================
    # Persönlichen Filter anwenden
    # ========================================

    candidates = []


    for film in results:

        title = film.get("title", "")
        description = film.get("description", "")
        channel = film.get("channel", "")
        duration = film.get("duration", 0)


        # Alles in Kleinbuchstaben
        title_lower = title.lower()
        description_lower = description.lower()

        text = title_lower + " " + description_lower


        # ----------------------------------------
        # Sender prüfen
        # ----------------------------------------

        if channel not in ALLOWED_CHANNELS:

            stats["falscher_sender"] += 1
            continue


        # ----------------------------------------
        # Dauer prüfen
        # ----------------------------------------

        duration_minutes = duration / 60


        if duration_minutes < MIN_DURATION:

            stats["zu_kurz"] += 1
            continue


        if duration_minutes > MAX_DURATION:

            stats["zu_lang"] += 1
            continue


        # ----------------------------------------
        # Audiodeskription
        # ----------------------------------------

        if "audiodeskription" in text:

            stats["audiodeskription"] += 1
            continue


        # ----------------------------------------
        # Allgemeine Ausschlussbegriffe
        # ----------------------------------------

        excluded = False

        for keyword in EXCLUDE_KEYWORDS:

            if keyword in text:

                stats["ausschluss_keyword"] += 1
                excluded = True
                break


        if excluded:
            continue


        # ----------------------------------------
        # Serien erkennen
        # ----------------------------------------

        is_series = False

        for keyword in SERIES_KEYWORDS:

            if keyword in title_lower:

                stats["serie"] += 1
                is_series = True
                break


        if is_series:
            continue


        # ----------------------------------------
        # Dokumentationen erkennen
        # ----------------------------------------

        is_documentary = False

        for keyword in DOCUMENTARY_KEYWORDS:

            if keyword in text:

                stats["dokumentation"] += 1
                is_documentary = True
                break


        if is_documentary:
            continue


        # ----------------------------------------
        # Kandidat akzeptieren
        # ----------------------------------------

        candidates.append(film)


    # ========================================
    # Statistik
    # ========================================

    print(f"API-Ergebnisse: {len(results)}")
    print(f"Film-Kandidaten nach Filter: {len(candidates)}")
    print()

    print("Filter-Statistik:")
    print(f"   Zu kurz:              {stats['zu_kurz']}")
    print(f"   Zu lang:              {stats['zu_lang']}")
    print(f"   Falscher Sender:      {stats['falscher_sender']}")
    print(f"   Ausschluss-Keyword:   {stats['ausschluss_keyword']}")
    print(f"   Serien:               {stats['serie']}")
    print(f"   Dokumentationen:      {stats['dokumentation']}")
    print(f"   Audiodeskription:     {stats['audiodeskription']}")
    print()


    # ========================================
    # Dubletten entfernen
    # ========================================

    unique_films = {}


    for film in candidates:

        website = film.get(
            "url_website",
            ""
        )


        if not website:

            website = film.get(
                "id",
                ""
            )


        if website not in unique_films:

            unique_films[website] = film


    unique_films = list(
        unique_films.values()
    )


    print(
        f"Nach Entfernen von Dubletten: "
        f"{len(unique_films)}"
    )

    print()


    # ========================================
    # Neue Filme erkennen
    # ========================================

    new_films = []


    for film in unique_films:

        website = film.get(
            "url_website",
            ""
        )


        if not website:

            website = film.get(
                "id",
                ""
            )


        if website not in seen:

            new_films.append(film)


    print(
        f"NEUE Filme: {len(new_films)}"
    )

    print()


    # ========================================
    # Neue Filme anzeigen
    # ========================================

    if new_films:

        for number, film in enumerate(
            new_films,
            start=1
        ):

            title = film.get(
                "title",
                "Unbekannt"
            )

            channel = film.get(
                "channel",
                "Unbekannt"
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


            minutes = round(
                duration / 60
            )


            if timestamp:

                date = datetime.fromtimestamp(
                    timestamp
                ).strftime(
                    "%d.%m.%Y"
                )

            else:

                date = "Unbekannt"


            print(
                f"{number}. {title}"
            )

            print(
                f"   Sender: {channel}"
            )

            print(
                f"   Dauer: {minutes} Minuten"
            )

            print(
                f"   Datum: {date}"
            )

            print(
                f"   Link: {website}"
            )

            print()


    else:

        print(
            "Keine neuen Filme gefunden."
        )


    # ========================================
    # Neue Filme speichern
    # ========================================

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    for film in new_films:

        website = film.get(
            "url_website",
            ""
        )


        if not website:

            website = film.get(
                "id",
                ""
            )


        seen[website] = {

            "title": film.get(
                "title",
                ""
            ),

            "channel": film.get(
                "channel",
                ""
            ),

            "first_seen": today

        }


    # ========================================
    # seen.json speichern
    # ========================================

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

    print(
        f"Gespeicherte Filme insgesamt: "
        f"{len(seen)}"
    )

    print("----------------------------------------")


except Exception as e:

    print("FEHLER:")
    print(e)


print("========================================")
