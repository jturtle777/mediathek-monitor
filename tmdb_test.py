import os
import requests

print("=" * 40)
print("TMDB TEST")
print("=" * 40)

api_key = os.environ.get("TMDB_API_KEY")

if not api_key:
    print("FEHLER: TMDB_API_KEY wurde nicht gefunden!")
    exit(1)

print("TMDB API-Key gefunden.")
print("Suche nach: Challengers - Rivalen")
print()

url = "https://api.themoviedb.org/3/search/movie"

params = {
    "api_key": api_key,
    "query": "Challengers - Rivalen",
    "language": "de-DE",
    "include_adult": "false"
}

response = requests.get(url, params=params, timeout=30)

print("HTTP Status:", response.status_code)

if response.status_code != 200:
    print("FEHLER:")
    print(response.text)
    exit(1)

data = response.json()

print("Treffer:", data.get("total_results"))
print()

for movie in data.get("results", [])[:5]:
    print("Titel:", movie.get("title"))
    print("Originaltitel:", movie.get("original_title"))
    print("TMDB Bewertung:", movie.get("vote_average"))
    print("Erscheinungsdatum:", movie.get("release_date"))
    print("TMDB ID:", movie.get("id"))
    print("-" * 40)

print()
print("Test erfolgreich!")
