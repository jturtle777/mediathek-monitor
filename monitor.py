import urllib.request
import json

print("========================================")
print("Mediathek Monitor")
print("========================================")
print("Verbinde mit MediathekViewWeb...")

url = "https://mediathekviewweb.de/api/query"

# Eine ganz einfache Suchanfrage:
# Wir suchen nach dem Begriff "Tatort".
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
    print("Antwort von MediathekViewWeb:")
    print(result)

except Exception as e:
    print("FEHLER:")
    print(e)

print("========================================")
