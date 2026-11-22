"""Table setup: creates the shops table if missing. Existing records are kept.

Usage:
    python init_db.py            # only create the table
    python init_db.py --sample   # also add sample shops if the table is empty
"""
import sys

from app import db

SAMPLES = [
    ("Camel Step Coffee", "Riyadh", 5, "Great Saudi coffee and dates"),
    ("Brew92", "Madinah", 4, "Quiet place for studying"),
    ("zoy", "Maka", 5, "good"),
    ("Qahwa Corner", "Jeddah", 3, "Nice view, slow service"),
]


def main():
    db.create_table()
    print("Table 'shops' is ready.")
    if "--sample" in sys.argv:
        if db.get_all():
            print("Table already has records; sample data not added.")
        else:
            for name, region, rating, notes in SAMPLES:
                db.add(name, region, rating, notes)
            print(f"Added {len(SAMPLES)} sample shops.")


if __name__ == "__main__":
    main()
