import urllib.request
import json

print("========================================")
print("Mediathek Monitor")
print("========================================")
print("Verbinde mit MediathekViewWeb...")

url = "https://mediathekviewweb.de/api/query"

try:
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    print("Verbindung erfolgreich!")
    print()
    print("Antwort von MediathekViewWeb:")
    print(type(data))

except Exception as e:
    print("FEHLER:")
    print(e)

print("========================================")
