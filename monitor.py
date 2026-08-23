import urllib.request
import urllib.parse
import json
import os
import smtplib
import html
import uuid
from email.message import EmailMessage
from datetime import datetime


# ========================================
# PERSÖNLICHE EINSTELLUNGEN
# ========================================

MIN_DURATION = 70
MAX_DURATION = 180
MAX_RESULTS = 1000


# ========================================
# TMDB FILTER
# ========================================

# Mindestbewertung bei TMDB
MIN_TMDB_RATING = 6.5

# Mindestanzahl Bewertungen bei TMDB
MIN_TMDB_VOTES = 30


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

TMDB_SEARCH_URL = (
    "https://api.themoviedb.org/3/search/movie"
)

TMDB_MOVIE_URL = (
    "https://api.themoviedb.org/3/movie"
)

TMDB_IMAGE_URL = (
    "https://image.tmdb.org/t/p/w342"
)

TMDB_POSTER_URL = (
    "https://image.tmdb.org/t/p/w300"
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
    "size": MAX_RESULTS,
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
# YOUTUBE SUCHLINK
# ========================================

def create_youtube_search_url(title):

    """
    Erstellt einen YouTube-Suchlink für
    einen deutschen Trailer.
    """

    query = (
        f"{title} deutscher Trailer"
    )

    encoded_query = urllib.parse.quote_plus(
        query
    )

    return (
        "https://www.youtube.com/results?"
        f"search_query={encoded_query}"
    )


# ========================================
# TRAILER AUS TMDB AUSWÄHLEN
# ========================================

def find_best_trailer(videos):

    """
    Sucht den bestmöglichen Trailer.

    Priorität:

    1. Deutscher Trailer
    2. Deutscher Teaser
    3. Englischer Trailer
    4. Englischer Teaser
    5. Sonstiger Trailer
    6. Sonstiges YouTube-Video
    """

    if not videos:

        return None


    youtube_videos = []


    for video in videos:

        if video.get("site") != "YouTube":

            continue


        key = video.get("key")


        if not key:

            continue


        youtube_videos.append(
            video
        )


    if not youtube_videos:

        return None


    def youtube_url(video):

        return (
            "https://www.youtube.com/watch?v="
            + video.get("key")
        )


    # ------------------------------------
    # 1. Deutscher offizieller Trailer
    # ------------------------------------

    german_trailers = [

        video

        for video in youtube_videos

        if (
            video.get("iso_639_1") == "de"
            and video.get("type") == "Trailer"
        )

    ]


    if german_trailers:

        video = german_trailers[0]

        return {

            "url":
                youtube_url(video),

            "name":
                video.get(
                    "name",
                    "Deutscher Trailer"
                ),

            "language":
                "de"

        }


    # ------------------------------------
    # 2. Deutscher Teaser
    # ------------------------------------

    german_teasers = [

        video

        for video in youtube_videos

        if (
            video.get("iso_639_1") == "de"
            and video.get("type") == "Teaser"
        )

    ]


    if german_teasers:

        video = german_teasers[0]

        return {

            "url":
                youtube_url(video),

            "name":
                video.get(
                    "name",
                    "Deutscher Teaser"
                ),

            "language":
                "de"

        }


    # ------------------------------------
    # 3. Englischer Trailer
    # ------------------------------------

    english_trailers = [

        video

        for video in youtube_videos

        if (
            video.get("iso_639_1") == "en"
            and video.get("type") == "Trailer"
        )

    ]


    if english_trailers:

        video = english_trailers[0]

        return {

            "url":
                youtube_url(video),

            "name":
                video.get(
                    "name",
                    "Trailer"
                ),

            "language":
                "en"

        }


    # ------------------------------------
    # 4. Englischer Teaser
    # ------------------------------------

    english_teasers = [

        video

        for video in youtube_videos

        if (
            video.get("iso_639_1") == "en"
            and video.get("type") == "Teaser"
        )

    ]


    if english_teasers:

        video = english_teasers[0]

        return {

            "url":
                youtube_url(video),

            "name":
                video.get(
                    "name",
                    "Teaser"
                ),

            "language":
                "en"

        }


    # ------------------------------------
    # 5. Irgendein Trailer
    # ------------------------------------

    trailers = [

        video

        for video in youtube_videos

        if video.get("type") == "Trailer"

    ]


    if trailers:

        video = trailers[0]

        return {

            "url":
                youtube_url(video),

            "name":
                video.get(
                    "name",
                    "Trailer"
                ),

            "language":
                video.get(
                    "iso_639_1",
                    ""
                )

        }


    # ------------------------------------
    # 6. Irgendein YouTube-Video
    # ------------------------------------

    video = youtube_videos[0]

    return {

        "url":
            youtube_url(video),

        "name":
            video.get(
                "name",
                "Video"
            ),

        "language":
            video.get(
                "iso_639_1",
                ""
            )

    }


# ========================================
# TMDB-FUNKTION
# ========================================

def search_tmdb(title):

    """
    Sucht einen Film bei TMDB und lädt
    zusätzlich:

    - TMDB-ID
    - TMDB-Titel
    - TMDB-Originaltitel
    - Jahr
    - Bewertung
    - Anzahl Bewertungen
    - Poster
    - IMDb-ID
    - IMDb-Link
    - Trailer
    - YouTube-Suchlink
    """

    if not TMDB_API_TOKEN:

        return None


    try:

        # --------------------------------
        # TMDB FILM SUCHEN
        # --------------------------------

        params = urllib.parse.urlencode({

            "query":
                title,

            "language":
                "de-DE",

            "include_adult":
                "false",

            "page":
                1

        })


        request_url = (
            TMDB_SEARCH_URL
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


        # --------------------------------
        # ERSTEN FILM AUSWÄHLEN
        # --------------------------------

        movie = results[0]


        movie_id = movie.get(
            "id"
        )


        if not movie_id:

            return None


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


        # --------------------------------
        # DETAILDATEN LADEN
        # --------------------------------

        detail_url = (
            f"{TMDB_MOVIE_URL}/{movie_id}"
        )


        detail_params = urllib.parse.urlencode({

            "language":
                "de-DE",

            "append_to_response":
                "videos,external_ids"

        })


        detail_request_url = (
            detail_url
            + "?"
            + detail_params
        )


        detail_request = urllib.request.Request(

            detail_request_url,

            headers={

                "Authorization":
                    f"Bearer {TMDB_API_TOKEN}",

                "Accept":
                    "application/json"

            },

            method="GET"

        )


        with urllib.request.urlopen(
            detail_request,
            timeout=20
        ) as response:

            details = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )


        # --------------------------------
        # IMDb-ID
        # --------------------------------

        external_ids = details.get(
            "external_ids",
            {}
        )


        imdb_id = external_ids.get(
            "imdb_id"
        )


        imdb_url = ""


        if imdb_id:

            imdb_url = (
                "https://www.imdb.com/title/"
                + imdb_id
                + "/"
            )


        # --------------------------------
        # TRAILER
        # --------------------------------

        videos = details.get(
            "videos",
            {}
        ).get(
            "results",
            []
        )


        trailer = find_best_trailer(
            videos
        )


        trailer_url = ""
        trailer_name = ""
        trailer_language = ""


        if trailer:

            trailer_url = trailer.get(
                "url",
                ""
            )

            trailer_name = trailer.get(
                "name",
                ""
            )

            trailer_language = trailer.get(
                "language",
                ""
            )


        # --------------------------------
        # YOUTUBE SUCHLINK
        # --------------------------------

        youtube_search_url = (
            create_youtube_search_url(
                title
            )
        )


        # --------------------------------
        # TMDB URL
        # --------------------------------

        tmdb_url = (
            "https://www.themoviedb.org/movie/"
            + str(movie_id)
        )


        # --------------------------------
        # ERGEBNIS
        # --------------------------------

        return {

            "id":
                movie_id,

            "tmdb_url":
                tmdb_url,

            "title":
                movie.get(
                    "title",
                    ""
                ),

            "original_title":
                movie.get(
                    "original_title",
                    ""
                ),

            "year":
                year,

            "rating":
                rating,

            "votes":
                votes,

            "poster_path":
                movie.get(
                    "poster_path"
                ),

            "imdb_id":
                imdb_id,

            "imdb_url":
                imdb_url,

            "trailer_url":
                trailer_url,

            "trailer_name":
                trailer_name,

            "trailer_language":
                trailer_language,

            "youtube_search_url":
                youtube_search_url

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

    Zusätzlich werden angezeigt:

    - Mediathek-Titel
    - TMDB-Titel
    - TMDB-Originaltitel
    - TMDB-ID
    - Link zu TMDB
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
            "MyMediathek Monitor – "
            "1 neuer Film"
        )

    else:

        subject = (
            "MyMediathek Monitor – "
            f"{len(films)} neue Filme"
        )


    msg["Subject"] = subject
    msg["From"] = f"Info MyMediathek Monitor <{MAIL_USERNAME}>"
    msg["To"] = MAIL_TO


    # ====================================
    # TEXT-VERSION
    # ====================================

    text_lines = [

        "MyMediathek Monitor",
        "",
        f"{len(films)} interessante "
        "Film(e) gefunden:",
        ""

    ]


    for number, film in enumerate(
        films,
        start=1
    ):

        # --------------------------------
        # MEDIATHEK-DATEN
        # --------------------------------

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


        # --------------------------------
        # TMDB-DATEN
        # --------------------------------

        tmdb = film.get(
            "_tmdb",
            {}
        )


        tmdb_id = tmdb.get(
            "id"
        )


        tmdb_title = tmdb.get(
            "title",
            ""
        )


        tmdb_original_title = tmdb.get(
            "original_title",
            ""
        )


        tmdb_url = tmdb.get(
            "tmdb_url",
            ""
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


        imdb_url = tmdb.get(
            "imdb_url",
            ""
        )


        trailer_url = tmdb.get(
            "trailer_url",
            ""
        )


        trailer_name = tmdb.get(
            "trailer_name",
            ""
        )


        youtube_search_url = tmdb.get(
            "youtube_search_url",
            ""
        )


        # --------------------------------
        # TEXT AUSGEBEN
        # --------------------------------

        text_lines.append(
            f"{number}. {title}"
        )


        text_lines.append(
            f"   Mediathek-Titel: {title}"
        )


        text_lines.append(
            f"   Sender: {channel}"
        )


        text_lines.append(
            f"   Dauer: {duration} Minuten"
        )


        if tmdb_title:

            text_lines.append(
                f"   TMDB-Titel: {tmdb_title}"
            )


        if tmdb_original_title:

            text_lines.append(
                "   Originaltitel aus TMDB: "
                f"{tmdb_original_title}"
            )


        if tmdb_id:

            text_lines.append(
                f"   TMDB-ID: {tmdb_id}"
            )


        if tmdb_url:

            text_lines.append(
                f"   TMDB: {tmdb_url}"
            )


        if year:

            text_lines.append(
                f"   Jahr: {year}"
            )


        if rating is not None:

            text_lines.append(
                f"   TMDB-Bewertung: "
                f"{rating:.1f}/10"
            )


        text_lines.append(
            f"   Bewertungen: {votes}"
        )


        if imdb_url:

            text_lines.append(
                f"   IMDb: {imdb_url}"
            )


        if trailer_url:

            if trailer_name:

                text_lines.append(
                    f"   Trailer: "
                    f"{trailer_name}"
                )

            else:

                text_lines.append(
                    "   Trailer:"
                )


            text_lines.append(
                f"   {trailer_url}"
            )


        if youtube_search_url:

            text_lines.append(
                "   YouTube-Trailersuche:"
            )


            text_lines.append(
                f"   {youtube_search_url}"
            )


        if website:

            text_lines.append(
                f"   Mediathek: {website}"
            )


        text_lines.append("")


    text_lines.append(
        "MyMediathek Monitor"
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
            font-family:Arial,Helvetica,sans-serif;
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
            MyMediathek Monitor
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

        # --------------------------------
        # MEDIATHEK-DATEN
        # --------------------------------

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


        # --------------------------------
        # TMDB-DATEN
        # --------------------------------

        tmdb = film.get(
            "_tmdb",
            {}
        )


        tmdb_id = tmdb.get(
            "id"
        )


        tmdb_title = tmdb.get(
            "title",
            ""
        )


        tmdb_original_title = tmdb.get(
            "original_title",
            ""
        )


        tmdb_url = tmdb.get(
            "tmdb_url",
            ""
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


        imdb_url = tmdb.get(
            "imdb_url",
            ""
        )


        trailer_url = tmdb.get(
            "trailer_url",
            ""
        )


        trailer_name = tmdb.get(
            "trailer_name",
            ""
        )


        trailer_language = tmdb.get(
            "trailer_language",
            ""
        )


        youtube_search_url = tmdb.get(
            "youtube_search_url",
            ""
        )


        # --------------------------------
        # COVER
        # --------------------------------

        image_cid = None


        if poster_path:

            poster_url = (
                TMDB_POSTER_URL
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
                    "   Cover konnte nicht "
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
                        width="{POSTER_WIDTH}"
                        style="
                            width:{POSTER_WIDTH}px;
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
        # SICHERE HTML-WERTE
        # --------------------------------

        safe_title = html.escape(
            str(title)
        )


        safe_channel = html.escape(
            str(channel)
        )


        safe_website = html.escape(
            str(website),
            quote=True
        )


        safe_tmdb_title = html.escape(
            str(tmdb_title)
        )


        safe_original_title = html.escape(
            str(tmdb_original_title)
        )


        # --------------------------------
        # INFORMATIONEN
        # --------------------------------

        html_parts.append(

            f"""
            <div style="flex:1;">

                <h3 style="
                    margin:0 0 8px 0;
                    font-size:18px;
                ">
                    {safe_title}
                </h3>

                <div style="
                    color:#555;
                    font-size:14px;
                    line-height:1.6;
                ">

                    <div>
                        <strong>
                            Mediathek-Titel:
                        </strong>
                        {safe_title}
                    </div>

                    <div>
                        <strong>Sender:</strong>
                        {safe_channel}
                    </div>

                    <div>
                        <strong>Dauer:</strong>
                        {duration} Minuten
                    </div>
            """

        )


        # --------------------------------
        # TMDB TITEL
        # --------------------------------

        if tmdb_title:

            html_parts.append(

                f"""
                    <div>
                        <strong>
                            TMDB-Titel:
                        </strong>
                        {safe_tmdb_title}
                    </div>
                """

            )


        # --------------------------------
        # ORIGINALTITEL
        # --------------------------------

        if tmdb_original_title:

            html_parts.append(

                f"""
                    <div>
                        <strong>
                            Originaltitel aus TMDB:
                        </strong>
                        {safe_original_title}
                    </div>
                """

            )


        # --------------------------------
        # TMDB-ID + LINK
        # --------------------------------

        if tmdb_id:

            safe_tmdb_url = html.escape(
                tmdb_url,
                quote=True
            )


            html_parts.append(

                f"""
                    <div style="
                        margin-top:6px;
                    ">

                        <strong>
                            TMDB-ID:
                        </strong>

                        {html.escape(str(tmdb_id))}

                        &nbsp;

                        <a
                            href="{safe_tmdb_url}"
                            style="
                                color:#0066cc;
                                text-decoration:none;
                            "
                        >
                            TMDB öffnen
                        </a>

                    </div>
                """

            )


        # --------------------------------
        # JAHR
        # --------------------------------

        if year:

            html_parts.append(

                f"""
                    <div>
                        <strong>Jahr:</strong>
                        {html.escape(str(year))}
                    </div>
                """

            )


        # --------------------------------
        # TMDB BEWERTUNG
        # --------------------------------

        if rating is not None:

            formatted_votes = (
                f"{votes:,}"
                .replace(",", ".")
            )


            html_parts.append(

                f"""
                    <div>
                        <strong>
                            TMDB-Bewertung:
                        </strong>

                        {rating:.1f}/10

                        &nbsp;

                        ({formatted_votes}
                        Bewertungen)
                    </div>
                """

            )


        # --------------------------------
        # IMDb LINK
        # --------------------------------

        if imdb_url:

            safe_imdb_url = html.escape(
                imdb_url,
                quote=True
            )


            html_parts.append(

                f"""
                    <div style="
                        margin-top:6px;
                    ">

                        <a
                            href="{safe_imdb_url}"
                            style="
                                color:#0066cc;
                                text-decoration:none;
                            "
                        >
                            ⭐ IMDb öffnen
                        </a>

                    </div>
                """

            )


        # --------------------------------
        # TRAILER
        # --------------------------------

        if trailer_url:

            safe_trailer_url = html.escape(
                trailer_url,
                quote=True
            )


            if (
                trailer_language
                == "de"
            ):

                trailer_label = (
                    "🎬 Deutscher Trailer"
                )

            else:

                trailer_label = (
                    "🎬 Trailer"
                )


            html_parts.append(

                f"""
                    <div style="
                        margin-top:8px;
                    ">

                        <a
                            href="{safe_trailer_url}"
                            style="
                                color:#cc0000;
                                text-decoration:none;
                            "
                        >
                            {trailer_label}
                        </a>

                    </div>
                """

            )


        # --------------------------------
        # YOUTUBE SUCHLINK
        # --------------------------------

        if youtube_search_url:

            safe_youtube_search_url = (
                html.escape(
                    youtube_search_url,
                    quote=True
                )
            )


            html_parts.append(

                f"""
                    <div style="
                        margin-top:5px;
                    ">

                        <a
                            href="{safe_youtube_search_url}"
                            style="
                                color:#0066cc;
                                text-decoration:none;
                            "
                        >
                            🔎 Weitere Trailer auf YouTube
                        </a>

                    </div>
                """

            )


        # --------------------------------
        # MEDIATHEK
        # --------------------------------

        if website:

            html_parts.append(

                f"""
                    <div style="
                        margin-top:10px;
                    ">

                        <a
                            href="{safe_website}"
                            style="
                                color:#0066cc;
                                text-decoration:none;
                                font-weight:bold;
                            "
                        >
                            ▶ Film in der Mediathek öffnen
                        </a>

                    </div>
                """

            )


        # --------------------------------
        # FILM-BLOCK SCHLIESSEN
        # --------------------------------

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

            Automatisch erstellt von
            MyMediathek Monitor.

        </div>

        </div>

        </body>
        </html>
        """

    )


    html_body = "".join(
        html_parts
    )


    # ====================================
    # HTML ZUR MAIL HINZUFÜGEN
    # ====================================

    msg.add_alternative(
        html_body,
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

    print(
        "========================================"
    )


# ========================================
# HAUPTPROGRAMM
# ========================================

try:

    # ====================================
    # MEDIATHEKVIEWWEB ABFRAGEN
    # ====================================

    data = json.dumps(
        query
    ).encode(
        "utf-8"
    )


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

            # --------------------------------
            # WICHTIG:
            # Dieser Titel stammt direkt
            # aus der Mediathek-Abfrage.
            # --------------------------------

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


            tmdb_id = tmdb.get(
                "id"
            )


            tmdb_title = tmdb.get(
                "title",
                ""
            )


            original_title = tmdb.get(
                "original_title",
                ""
            )


            year = tmdb.get(
                "year",
                ""
            )


            imdb_id = tmdb.get(
                "imdb_id"
            )


            trailer_url = tmdb.get(
                "trailer_url",
                ""
            )


            trailer_name = tmdb.get(
                "trailer_name",
                ""
            )


            trailer_language = tmdb.get(
                "trailer_language",
                ""
            )


            # --------------------------------
            # TMDB INFORMATIONEN AUSGEBEN
            # --------------------------------

            print(
                f"   Mediathek-Titel: {title}"
            )


            print(
                f"   TMDB: {tmdb_title}"
            )


            if original_title:

                print(
                    f"   TMDB-Originaltitel: "
                    f"{original_title}"
                )


            if tmdb_id:

                print(
                    f"   TMDB-ID: {tmdb_id}"
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


            if imdb_id:

                print(
                    f"   IMDb: {imdb_id}"
                )

            else:

                print(
                    "   IMDb: keine ID"
                )


            if trailer_url:

                print(
                    f"   Trailer: "
                    f"{trailer_name}"
                )


                print(
                    f"   Trailer URL: "
                    f"{trailer_url}"
                )


                if trailer_language == "de":

                    print(
                        "   Trailer-Sprache: "
                        "Deutsch"
                    )

            else:

                print(
                    "   TMDB: kein Trailer"
                )


            print()


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


            # --------------------------------
            # TMDB-DATEN AM FILM SPEICHERN
            # --------------------------------

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
                f"   Mediathek-Titel: "
                f"{title}"
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


            if tmdb.get("title"):

                print(
                    f"   TMDB-Titel: "
                    f"{tmdb.get('title')}"
                )


            if tmdb.get("original_title"):

                print(
                    f"   Originaltitel: "
                    f"{tmdb.get('original_title')}"
                )


            if tmdb.get("id"):

                print(
                    f"   TMDB-ID: "
                    f"{tmdb.get('id')}"
                )


            if tmdb.get("tmdb_url"):

                print(
                    f"   TMDB-Link: "
                    f"{tmdb.get('tmdb_url')}"
                )


            print(
                f"   TMDB: "
                f"{tmdb.get('rating', 0):.1f}"
            )


            print(
                f"   Bewertungen: "
                f"{tmdb.get('votes', 0)}"
            )


            if tmdb.get("imdb_id"):

                print(
                    f"   IMDb: "
                    f"{tmdb.get('imdb_id')}"
                )


            if tmdb.get("trailer_url"):

                print(
                    f"   Trailer: "
                    f"{tmdb.get('trailer_url')}"
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

            "title":
                film.get(
                    "title",
                    ""
                ),

            "channel":
                film.get(
                    "channel",
                    ""
                ),

            "first_seen":
                today

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


    print(
        "----------------------------------------"
    )


    print(
        f"Gespeicherte Filme insgesamt: "
        f"{len(seen)}"
    )


    print(
        "----------------------------------------"
    )


except Exception as e:

    print(
        "FEHLER:"
    )


    print(
        e
    )


print(
    "========================================"
)
