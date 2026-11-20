import json
import socket
import sys
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

URL = "http://127.0.0.1:5050/shops"
REPORT_FILE = "report.txt"


def fetch_shops():
    """Ask Flask's JSON route for all saved shops."""
    with urlopen(URL, timeout=5) as reply:
        data = json.loads(reply.read().decode("utf-8"))
    return data["shops"]


def write_report(shops, result):
    """Runs inside the thread: write the shops to a UTF-8 text file."""
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as file:
            file.write("Saudi Coffee Shop Report\n")
            file.write("=" * 30 + "\n")
            if not shops:
                file.write("No shops saved yet.\n")
            for shop in shops:
                file.write(
                    f"#{shop['id']} {shop['name']} | {shop['region']} | "
                    f"rating {shop['rating']}/5 | {shop['notes'] or '-'}\n"
                )
            if shops:
                average = sum(s["rating"] for s in shops) / len(shops)
                file.write(f"\nTotal: {len(shops)} shops, average rating {average:.1f}\n")
        result["saved"] = True
    except OSError as error:
        result["saved"] = False
        result["error"] = str(error)


def main():
    try:
        shops = fetch_shops()
    except HTTPError as error:
        print(f"Server returned an error: {error.code}")
        sys.exit(1)
    except socket.timeout:
        print("The server took too long to answer.")
        sys.exit(1)
    except URLError:
        print("Cannot connect to Flask. Start app.py first.")
        sys.exit(1)
    except (ValueError, KeyError):
        print("Flask sent a reply the report helper cannot read.")
        sys.exit(1)

    result = {}
    worker = Thread(target=write_report, args=(shops, result))
    worker.start()
    worker.join()

    if result.get("saved"):
        print(f"Report saved to {REPORT_FILE} ({len(shops)} shops).")
    else:
        print(f"Could not save the report: {result.get('error')}")


if __name__ == "__main__":
    main()