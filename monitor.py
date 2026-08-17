import urllib.request
import urllib.parse
import json
import os
import smtplib
import html
import uuid
from email.message import EmailMessage
from email.utils import make_msgid
from datetime import datetime


# ========================================
# PERSÖNLICHE EINSTELLUNGEN
# ========================================

MIN_DURATION = 70
MAX_DURATION = 180


# ========================================
# TMDB FILTER
# ========================================

# Mindestbewertung bei TMDB
MIN_TMDB_RATING = 6.5

# Mindestanzahl Bewertungen bei TMDB
MIN_TMDB_VOTES = 1000


# ========================================
# E-MAIL
# ========================================

# E-Mail nur versenden, wenn mindestens
# ein interessanter Film gefunden wurde.
SEND_EMAIL_ONLY_IF_FILMS_FOUND = True

# Breite der Filmcover in der E-Mail
POSTER_WIDTH = 120


# ========================================
# ERLAUBTE SENDER
# ========================================

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

    # Sport
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
# TMDB
# ========================================

TMDB_API_TOKEN = os.environ.get(
    "TMDB_API_TOKEN"
)

TMDB_API_URL = (
    "https://api.themoviedb.org/3/search/multi"
)

TMDB_IMAGE_URL = (
    "https://image.tmdb.org/t/p/w342"
)


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
# E-MAIL STATUS
# ========================================

MAIL_USERNAME = os.environ.get(
    "MAIL_USERNAME"
)

MAIL_PASSWORD = os.environ.get(
    "MAIL_PASSWORD"
)

MAIL_TO = os.environ.get(
    "MAIL_TO"
)


if (
    MAIL_USERNAME
    and MAIL_PASSWORD
    and MAIL_TO
):

    print("E-Mail: Zugangsdaten vorhanden")

else:

    print(
        "E-Mail: Zugangsdaten nicht vollständig"
    )

print()


# ========================================
# MEDIATHEKVIEWWEB API
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
        "original_title": ...,
        "year": ...,
        "rating": ...,
        "votes": ...,
        "poster_path": ...
    }

    oder None.
    """

    if not TMDB_API_TOKEN:

        return None


    try:

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


        # Nur Filme berücksichtigen
        movie_results = [

            item

            for item in results

            if item.get(
                "media_type"
            ) == "movie"

        ]


        if not movie_results:

            return None


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

            "poster_path":
                movie.get(
                    "poster_path"
                )

        }


    except Exception as e:

        print(
            f"   TMDB Fehler: {e}"
        )

        return None


# ========================================
# POSTER HERUNTERLADEN
# ========================================

def download_poster(poster_path):

    """
    Lädt ein TMDB-Poster herunter.

    Rückgabe:
        bytes oder None
    """

    if not poster_path:

        return None


    try:

        poster_url = (
            TMDB_IMAGE_URL
            + poster_path
        )


        request = urllib.request.Request(

            poster_url,

            headers={
                "User-Agent":
                    "Mediathek-Monitor/1.0"
            }

        )


        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            return response.read()


    except Exception as e:

        print(
            f"   Poster-Fehler: {e}"
        )

        return None


# ========================================
# E-MAIL ERSTELLEN
# ========================================

def send_movie_email(films):

    """
    Erstellt und versendet die HTML-Mail
    mit eingebetteten TMDB-Covern.
    """

    if not films:

        return


    if not (
        MAIL_USERNAME
        and MAIL_PASSWORD
        and MAIL_TO
    ):

        print(
            "E-Mail nicht versendet:"
        )

        print(
            "E-Mail-Zugangsdaten fehlen."
        )

        return


    print()
    print("========================================")
    print("E-MAIL")
    print("========================================")
    print()

    print(
        f"Bereite E-Mail mit "
        f"{len(films)} Film(en) vor..."
    )


    msg = EmailMessage()


    if len(films) == 1:

        subject = (
            "Mediathek Monitor – "
            "1 neuer Film"
        )

    else:

        subject = (
            "Mediathek Monitor – "
            f"{len(films)} neue Filme"
        )


    msg["Subject"] = subject
    msg["From"] = MAIL_USERNAME
    msg["To"] = MAIL_TO


    # ====================================
    # TEXT-VERSION
    # ====================================

    text_lines = [

        "Mediathek Monitor",
        "",
        f"{len(films)} interessante "
        "Film(e) gefunden:",
        ""

    ]


    for number, film in enumerate(
        films,
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

        duration = round(
            film.get(
                "duration",
                0
            ) / 60
        )

        website = film.get(
            "url_website",
            ""
        )

        tmdb = film.get(
            "_tmdb",
            {}
        )

        rating = tmdb.get(
            "rating"
        )

        votes = tmdb.get(
            "votes",
            0
        )

        year = tmdb.get(
            "year",
            ""
        )


        text_lines.append(
            f"{number}. {title}"
        )

        text_lines.append(
            f"   Sender: {channel}"
        )

        text_lines.append(
            f"   Dauer: {duration} Minuten"
        )


        if year:

            text_lines.append(
                f"   Jahr: {year}"
            )


        if rating is not None:

            text_lines.append(
                f"   TMDB: {rating:.1f}"
            )


        text_lines.append(
            f"   Bewertungen: {votes}"
        )

        text_lines.append(
            f"   Link: {website}"
        )

        text_lines.append("")


    text_lines.append(
        "Mediathek Monitor"
    )


    msg.set_content(
        "\n".join(
            text_lines
        )
    )


    # ====================================
    # HTML MAIL
    # ====================================

    html_parts = [

        """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        </head>

        <body style="
            font-family: Arial, Helvetica, sans-serif;
            background:#f4f4f4;
            margin:0;
            padding:20px;
        ">

        <div style="
            max-width:700px;
            margin:auto;
            background:white;
            padding:24px;
            border-radius:8px;
        ">

        <h2 style="
            margin-top:0;
        ">
            Mediathek Monitor
        </h2>

        <p>
            Es wurden
            <strong>
        """

    ]


    if len(films) == 1:

        html_parts.append(
            "1 interessanter Film"
        )

    else:

        html_parts.append(
            f"{len(films)} interessante Filme"
        )


    html_parts.extend([

        """
            </strong>
            gefunden:
        </p>
        """

    ])


    # ====================================
    # FILME
    # ====================================

    embedded_images = []


    for number, film in enumerate(
        films,
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

        duration = round(
            film.get(
                "duration",
                0
            ) / 60
        )

        website = film.get(
            "url_website",
            ""
        )

        tmdb = film.get(
            "_tmdb",
            {}
        )

        rating = tmdb.get(
            "rating"
        )

        votes = tmdb.get(
            "votes",
            0
        )

        year = tmdb.get(
            "year",
            ""
        )

        poster_path = tmdb.get(
            "poster_path"
        )


        # --------------------------------
        # COVER
        # --------------------------------

        image_cid = None


        if poster_path:

            poster_url = (
                "https://image.tmdb.org/t/p/w300"
                + poster_path
            )


            try:

                print(
                    f"   Lade Cover: {title}"
                )


                with urllib.request.urlopen(
                    poster_url,
                    timeout=20
                ) as response:

                    image_data = response.read()


                image_cid = (
                    f"poster{number}-"
                    f"{uuid.uuid4().hex}"
                )


                embedded_images.append({

                    "data":
                        image_data,

                    "cid":
                        image_cid,

                    "filename":
                        f"poster_{number}.jpg"

                })


                print(
                    "   Cover erfolgreich geladen."
                )


            except Exception as e:

                print(
                    f"   Cover konnte nicht "
                    f"geladen werden: {e}"
                )


        # --------------------------------
        # FILM-BLOCK
        # --------------------------------

        html_parts.append(

            """
            <div style="
                border-top:1px solid #ddd;
                padding:20px 0;
                display:flex;
            ">
            """
        )


        # --------------------------------
        # COVER HTML
        # --------------------------------

        if image_cid:

            html_parts.append(

                f"""
                <div style="
                    width:110px;
                    min-width:110px;
                    margin-right:18px;
                ">
                    <img
                        src="cid:{image_cid}"
                        width="100"
                        style="
                            width:100px;
                            height:auto;
                            display:block;
                            border-radius:5px;
                        "
                    >
                </div>
                """

            )

        else:

            html_parts.append(

                """
                <div style="
                    width:110px;
                    min-width:110px;
                    margin-right:18px;
                ">
                </div>
                """

            )


        # --------------------------------
        # INFORMATIONEN
        # --------------------------------

        html_parts.append(

            f"""
            <div>

                <h3 style="
                    margin:0 0 8px 0;
                    font-size:18px;
                ">
                    {title}
                </h3>

                <div style="
                    color:#555;
                    font-size:14px;
                    line-height:1.6;
                ">

                    <div>
                        <strong>Sender:</strong>
                        {channel}
                    </div>

                    <div>
                        <strong>Dauer:</strong>
                        {duration} Minuten
                    </div>
            """

        )


        if year:

            html_parts.append(

                f"""
                    <div>
                        <strong>Jahr:</strong>
                        {year}
                    </div>
                """

            )


        if rating is not None:

            html_parts.append(

                f"""
                    <div>
                        <strong>TMDB:</strong>
                        {rating:.1f}/10
                        &nbsp; ({votes:,} Bewertungen)
                    </div>
                """.replace(
                    ",",
                    "."
                )

            )


        if website:

            html_parts.append(

                f"""
                    <div style="
                        margin-top:10px;
                    ">
                        <a
                            href="{website}"
                            style="
                                color:#0066cc;
                                text-decoration:none;
                            "
                        >
                            ▶ Film in der Mediathek öffnen
                        </a>
                    </div>
                """

            )


        html_parts.append(

            """
                </div>
            </div>
            </div>
            """

        )


    # ====================================
    # HTML ABSCHLIESSEN
    # ====================================

    html_parts.append(

        """
        <div style="
            border-top:1px solid #ddd;
            margin-top:10px;
            padding-top:15px;
            color:#888;
            font-size:12px;
        ">
            Automatisch erstellt vom
            Mediathek Monitor.
        </div>

        </div>

        </body>
        </html>
        """

    )


    html = "".join(
        html_parts
    )


    # ====================================
    # HTML ZUR MAIL HINZUFÜGEN
    # ====================================

    msg.add_alternative(
        html,
        subtype="html"
    )


    # ====================================
    # COVERS ALS INLINE-BILDER EINBETTEN
    # ====================================

    for image in embedded_images:

        msg.get_payload()[1].add_related(

            image["data"],

            maintype="image",

            subtype="jpeg",

            cid=f"<{image['cid']}>",

            filename=image["filename"]

        )


    # ====================================
    # SMTP
    # ====================================

    print()
    print(
        "Verbinde mit iCloud Mail..."
    )


    with smtplib.SMTP(
        "smtp.mail.me.com",
        587,
        timeout=30
    ) as smtp:

        print(
            "SMTP-Verbindung erfolgreich!"
        )


        smtp.starttls()


        print(
            "TLS-Verschlüsselung aktiviert."
        )


        smtp.login(
            MAIL_USERNAME,
            MAIL_PASSWORD
        )


        print(
            "Anmeldung erfolgreich."
        )


        smtp.send_message(
            msg
        )


        print(
            "E-Mail erfolgreich versendet!"
        )


    print()
    print(
        f"{len(embedded_images)} Cover "
        "eingebettet."
    )

    print("========================================")


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
    # MEDIATHEK-FILTER
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
        f"NEUE Filme vor TMDB-Filter: "
        f"{len(new_films)}"
    )

    print()


    # ====================================
    # TMDB FILTER
    # ====================================

    interesting_films = []


    tmdb_stats = {

        "kein_treffer": 0,

        "bewertung_zu_niedrig": 0,

        "zu_wenig_stimmen": 0,

        "erfüllt_beide_kriterien": 0

    }


    if new_films and TMDB_API_TOKEN:

        print(
            "========================================"
        )

        print(
            "TMDB-PRÜFUNG"
        )

        print(
            "========================================"
        )

        print()

        print(
            f"Mindestbewertung: "
            f"{MIN_TMDB_RATING:.1f}"
        )

        print(
            f"Mindestanzahl Bewertungen: "
            f"{MIN_TMDB_VOTES}"
        )

        print()


        for film in new_films:

            title = film.get(
                "title",
                "Unbekannt"
            )


            print(
                f"Prüfe: {title}"
            )


            tmdb = search_tmdb(
                title
            )


            if not tmdb:

                print(
                    "   TMDB: kein Film gefunden"
                )

                tmdb_stats[
                    "kein_treffer"
                ] += 1

                print()

                continue


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


            print(
                f"   TMDB: {tmdb_title}"
            )


            if year:

                print(
                    f"   Jahr: {year}"
                )


            if rating is not None:

                print(
                    f"   Bewertung: "
                    f"{rating:.1f}"
                )

            else:

                print(
                    "   Bewertung: unbekannt"
                )


            print(
                f"   Bewertungen: "
                f"{votes}"
            )


            # ----------------------------
            # BEWERTUNG PRÜFEN
            # ----------------------------

            if (
                rating is None
                or rating < MIN_TMDB_RATING
            ):

                print(
                    "   -> Bewertung zu niedrig"
                )

                tmdb_stats[
                    "bewertung_zu_niedrig"
                ] += 1

                print()

                continue


            # ----------------------------
            # ANZAHL BEWERTUNGEN PRÜFEN
            # ----------------------------

            if votes < MIN_TMDB_VOTES:

                print(
                    "   -> Zu wenige Bewertungen"
                )

                tmdb_stats[
                    "zu_wenig_stimmen"
                ] += 1

                print()

                continue


            # ----------------------------
            # BEIDE KRITERIEN ERFÜLLT
            # ----------------------------

            print(
                "   -> *** INTERESSANT ***"
            )


            tmdb_stats[
                "erfüllt_beide_kriterien"
            ] += 1


            # TMDB-Daten temporär
            # am Film speichern

            film["_tmdb"] = tmdb


            interesting_films.append(
                film
            )


            print()


    elif new_films:

        print(
            "TMDB-Prüfung übersprungen:"
        )

        print(
            "Kein TMDB API Token vorhanden."
        )

        print()


    # ====================================
    # TMDB STATISTIK
    # ====================================

    print(
        "========================================"
    )

    print(
        "TMDB-STATISTIK"
    )

    print(
        "========================================"
    )

    print()

    print(
        f"Neue Filme: "
        f"{len(new_films)}"
    )

    print(
        f"Kein TMDB-Treffer: "
        f"{tmdb_stats['kein_treffer']}"
    )

    print(
        f"Bewertung zu niedrig: "
        f"{tmdb_stats['bewertung_zu_niedrig']}"
    )

    print(
        f"Zu wenige Bewertungen: "
        f"{tmdb_stats['zu_wenig_stimmen']}"
    )

    print(
        f"Beide Kriterien erfüllt: "
        f"{tmdb_stats['erfüllt_beide_kriterien']}"
    )

    print()


    # ====================================
    # INTERESSANTE FILME
    # ====================================

    print(
        "========================================"
    )

    print(
        "INTERESSANTE FILME"
    )

    print(
        "========================================"
    )

    print()


    if interesting_films:

        for number, film in enumerate(
            interesting_films,
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


            tmdb = film.get(
                "_tmdb",
                {}
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
                f"   TMDB: "
                f"{tmdb.get('rating', 0):.1f}"
            )

            print(
                f"   Bewertungen: "
                f"{tmdb.get('votes', 0)}"
            )

            print(
                f"   Link: {website}"
            )

            print()


    else:

        print(
            "Keine Filme erfüllen aktuell "
            "beide TMDB-Kriterien."
        )

        print()


    # ====================================
    # E-MAIL VERSENDEN
    # ====================================

    if interesting_films:

        send_movie_email(
            interesting_films
        )

    else:

        print(
            "Keine E-Mail versendet, "
            "da keine interessanten Filme "
            "gefunden wurden."
        )


    # ====================================
    # ALLE NEUEN FILME SPEICHERN
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
    # seen.json SCHREIBEN
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
