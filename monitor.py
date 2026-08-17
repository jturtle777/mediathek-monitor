import urllib.request
import urllib.parse
import json
import os
from datetime import datetime


# ========================================
# PERSÖNLICHE EINSTELLUNGEN
# ========================================

MIN_DURATION = 70
MAX_DURATION = 180


# Nur Sender, deren Inhalte in Deutschland
# grundsätzlich verfügbar sein sollen.
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
    "3sat"
}


# ========================================
# TMDB
# ========================================

TMDB_API_TOKEN = os.environ.get(
    "TMDB_API_TOKEN"
)

TMDB_API_URL = (
    "https://api.themoviedb.org/3/search/multi"
)


# ========================================
# AUSZUSCHLIESSENDE BEGRIFFE
# ========================================

EXCLUDE_KEYWORDS = [

    # Audiodeskription
    "audiodeskription",

    # Nachrichten / Information
    "nachrichten",
    "nachricht",
    "wetter",
    "tagesschau",
    "heute journal",
    "heute-journal",
    "journal",

    # Magazine / Talk
    "magazin",
    "talk",
    "talkshow",
    "pressekonferenz",
    "matinee",

    # Shows
    "quiz",
    "gameshow",
    "game show",
    "fernsehgarten",
    "lieblingsstücke",

    # Sport allgemein
    "sport",
    "fußball",
    "fussball",
    "bundesliga",
    "champions league",
    "europa league",
    "leichtathletik",
    "schwimm-em",
    "schwimm em",
    "schwimmen",
    "beachvolleyball",
    "volleyball",
    "judo",
    "tennis",
    "handball",
    "basketball",
    "radrennen",
    "tour de france",
    "olympia",
    "olympische",
    "weltcup",
    "grand prix",
    "em 2026",
    "wm 2026",

    # Typische TV-Formate
    "nächster halt:",
    "bares für rares",
    "mediathek",
    "live nach",
    "aktuell",
    "aktueller bericht",
    "heute vom",
    "sendung vom"
]


# ========================================
# SERIEN-ERKENNUNG
# ========================================

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


# ========================================
# DOKUMENTATIONEN
# ========================================

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
# TMDB STATUS
# ========================================

if TMDB_API_TOKEN:

    print("TMDB API: Token vorhanden")

else:

    print("TMDB API: KEIN TOKEN GEFUNDEN")

    print(
        "Bitte das GitHub Secret "
        "'TMDB_API_TOKEN' einrichten."
    )

print()


# ========================================
# API MEDIATHEKVIEWWEB
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
# GESPEICHERTE FILME
# ========================================

try:

    with open(
        "seen.json",
        "r",
        encoding="utf-8"
    ) as file:

        seen = json.load(file)

except FileNotFoundError:

    seen = {}


print(
    f"Bereits bekannte Filme: {len(seen)}"
)

print()


# ========================================
# FILTER-STATISTIK
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


# ========================================
# TMDB-FUNKTION
# ========================================

def search_tmdb(title):

    """
    Sucht einen Titel bei TMDB.

    Rückgabe:

    {
        "title": ...,
        "year": ...,
        "rating": ...,
        "votes": ...,
        "media_type": ...
    }

    oder None, wenn nichts gefunden wurde.
    """

    if not TMDB_API_TOKEN:

        return None


    try:

        # TMDB kann mit deutschen Titeln
        # teilweise gut umgehen.
        params = urllib.parse.urlencode({

            "query": title,

            "language": "de-DE",

            "include_adult": "false",

            "page": 1

        })


        request_url = (
            TMDB_API_URL
            + "?"
            + params
        )


        request = urllib.request.Request(

            request_url,

            headers={

                "Authorization":
                    f"Bearer {TMDB_API_TOKEN}",

                "Accept":
                    "application/json"

            },

            method="GET"
        )


        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )


        results = data.get(
            "results",
            []
        )


        if not results:

            return None


        # Wir interessieren uns zunächst
        # hauptsächlich für Filme.
        #
        # TMDB liefert bei /search/multi
        # auch Serien und Personen.
        #
        # Deshalb suchen wir zuerst einen Film.

        movie_results = [

            item

            for item in results

            if item.get(
                "media_type"
            ) == "movie"

        ]


        if not movie_results:

            return None


        # Der erste Treffer ist zunächst
        # unser bester Treffer.
        movie = movie_results[0]


        release_date = movie.get(
            "release_date",
            ""
        )


        year = ""

        if release_date:

            year = release_date[:4]


        rating = movie.get(
            "vote_average"
        )


        votes = movie.get(
            "vote_count",
            0
        )


        return {

            "title": movie.get(
                "title",
                ""
            ),

            "original_title":
                movie.get(
                    "original_title",
                    ""
                ),

            "year": year,

            "rating": rating,

            "votes": votes,

            "media_type": "movie"

        }


    except Exception as e:

        print(
            f"   TMDB Fehler: {e}"
        )

        return None


# ========================================
# HAUPTPROGRAMM
# ========================================

try:

    # ====================================
    # MEDIATHEKVIEWWEB ABFRAGEN
    # ====================================

    data = json.dumps(
        query
    ).encode("utf-8")


    request = urllib.request.Request(

        url,

        data=data,

        headers={
            "Content-Type":
                "application/json"
        },

        method="POST"
    )


    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        result = json.loads(
            response.read().decode(
                "utf-8"
            )
        )


    results = result[
        "result"
    ][
        "results"
    ]


    print(
        "Verbindung erfolgreich!"
    )

    print()


    # ====================================
    # FILTER
    # ====================================

    candidates = []


    for film in results:

        title = film.get(
            "title",
            ""
        )

        description = film.get(
            "description",
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


        title_lower = title.lower()

        description_lower = (
            description.lower()
        )

        text = (
            title_lower
            + " "
            + description_lower
        )


        # --------------------------------
        # SENDER
        # --------------------------------

        if channel not in ALLOWED_CHANNELS:

            stats[
                "falscher_sender"
            ] += 1

            continue


        # --------------------------------
        # DAUER
        # --------------------------------

        duration_minutes = (
            duration / 60
        )


        if duration_minutes < MIN_DURATION:

            stats[
                "zu_kurz"
            ] += 1

            continue


        if duration_minutes > MAX_DURATION:

            stats[
                "zu_lang"
            ] += 1

            continue


        # --------------------------------
        # AUDIODESKRIPTION
        # --------------------------------

        if "audiodeskription" in text:

            stats[
                "audiodeskription"
            ] += 1

            continue


        # --------------------------------
        # AUSSCHLUSSWÖRTER
        # --------------------------------

        excluded = False


        for keyword in EXCLUDE_KEYWORDS:

            if keyword in text:

                stats[
                    "ausschluss_keyword"
                ] += 1

                excluded = True

                break


        if excluded:

            continue


        # --------------------------------
        # SERIEN
        # --------------------------------

        is_series = False


        for keyword in SERIES_KEYWORDS:

            if keyword in title_lower:

                stats[
                    "serie"
                ] += 1

                is_series = True

                break


        if is_series:

            continue


        # --------------------------------
        # DOKUMENTATION
        # --------------------------------

        is_documentary = False


        for keyword in DOCUMENTARY_KEYWORDS:

            if keyword in text:

                stats[
                    "dokumentation"
                ] += 1

                is_documentary = True

                break


        if is_documentary:

            continue


        # --------------------------------
        # FILM-KANDIDAT
        # --------------------------------

        candidates.append(
            film
        )


    # ====================================
    # STATISTIK
    # ====================================

    print(
        f"API-Ergebnisse: {len(results)}"
    )

    print(
        f"Film-Kandidaten nach Filter: "
        f"{len(candidates)}"
    )

    print()

    print("Filter-Statistik:")

    print(
        f"   Zu kurz:              "
        f"{stats['zu_kurz']}"
    )

    print(
        f"   Zu lang:              "
        f"{stats['zu_lang']}"
    )

    print(
        f"   Falscher Sender:      "
        f"{stats['falscher_sender']}"
    )

    print(
        f"   Ausschluss-Keyword:   "
        f"{stats['ausschluss_keyword']}"
    )

    print(
        f"   Serien:               "
        f"{stats['serie']}"
    )

    print(
        f"   Dokumentationen:      "
        f"{stats['dokumentation']}"
    )

    print(
        f"   Audiodeskription:     "
        f"{stats['audiodeskription']}"
    )

    print()


    # ====================================
    # DUBLETTEN
    # ====================================

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

            unique_films[
                website
            ] = film


    unique_films = list(
        unique_films.values()
    )


    print(
        f"Nach Entfernen von Dubletten: "
        f"{len(unique_films)}"
    )

    print()


    # ====================================
    # NEUE FILME
    # ====================================

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

            new_films.append(
                film
            )


    print(
        f"NEUE Filme: {len(new_films)}"
    )

    print()


    # ====================================
    # TMDB-BEWERTUNGEN
    # ====================================

    if new_films:

        print(
            "========================================"
        )

        print(
            "TMDB-BEWERTUNGEN"
        )

        print(
            "========================================"
        )

        print()


        if not TMDB_API_TOKEN:

            print(
                "TMDB wird übersprungen, "
                "da kein API Token vorhanden ist."
            )

            print()

        else:

            for number, film in enumerate(
                new_films,
                start=1
            ):

                title = film.get(
                    "title",
                    "Unbekannt"
                )


                print(
                    f"{number}. {title}"
                )

                print(
                    "   Suche bei TMDB..."
                )


                tmdb = search_tmdb(
                    title
                )


                if tmdb:

                    rating = tmdb.get(
                        "rating"
                    )

                    votes = tmdb.get(
                        "votes",
                        0
                    )

                    tmdb_title = tmdb.get(
                        "title",
                        ""
                    )

                    year = tmdb.get(
                        "year",
                        ""
                    )


                    if rating is not None:

                        rating_display = (
                            f"{rating:.1f}"
                        )

                    else:

                        rating_display = (
                            "keine Bewertung"
                        )


                    print(
                        f"   TMDB: "
                        f"{tmdb_title}"
                    )

                    if year:

                        print(
                            f"   Jahr: "
                            f"{year}"
                        )


                    print(
                        f"   Bewertung: "
                        f"{rating_display}"
                    )

                    print(
                        f"   Stimmen: "
                        f"{votes}"
                    )

                else:

                    print(
                        "   TMDB: "
                        "kein passender Film gefunden"
                    )


                print()


    else:

        print(
            "Keine neuen Filme gefunden."
        )

        print()


    # ====================================
    # FILME AUSGEBEN
    # ====================================

    if new_films:

        print(
            "========================================"
        )

        print(
            "NEUE FILME"
        )

        print(
            "========================================"
        )

        print()


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


    # ====================================
    # SPEICHERN
    # ====================================

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


        seen[
            website
        ] = {

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


    # ====================================
    # seen.json
    # ====================================

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


print(
    "========================================"
)
