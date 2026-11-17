import sqlite3
from contextlib import closing

from flask import Flask, request, jsonify

DB_PATH = "coffee.db"
app = Flask(__name__)


class ShopDB:
    """All database work lives in this class."""

    def __init__(self, path):
        self.path = path

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        with closing(self.connect()) as conn:
            with conn:  # commits on success
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS shops (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        region TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        notes TEXT
                    )"""
                )

    def get_all(self, region=None, min_rating=None):
        query = "SELECT * FROM shops WHERE 1=1"
        params = []
        if region:
            query += " AND region = ?"
            params.append(region)
        if min_rating is not None:
            query += " AND rating >= ?"
            params.append(min_rating)
        query += " ORDER BY id"
        with closing(self.connect()) as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_one(self, shop_id):
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT * FROM shops WHERE id = ?", (shop_id,)
            ).fetchone()
        return dict(row) if row else None

    def add(self, name, region, rating, notes):
        with closing(self.connect()) as conn:
            with conn:
                cur = conn.execute(
                    "INSERT INTO shops (name, region, rating, notes) VALUES (?, ?, ?, ?)",
                    (name, region, rating, notes),
                )
                new_id = cur.lastrowid
        return self.get_one(new_id)

    def update(self, shop_id, name, region, rating, notes):
        with closing(self.connect()) as conn:
            with conn:
                cur = conn.execute(
                    "UPDATE shops SET name=?, region=?, rating=?, notes=? WHERE id=?",
                    (name, region, rating, notes, shop_id),
                )
                changed = cur.rowcount
        return self.get_one(shop_id) if changed else None

    def delete(self, shop_id):
        with closing(self.connect()) as conn:
            with conn:
                cur = conn.execute("DELETE FROM shops WHERE id = ?", (shop_id,))
                return cur.rowcount > 0


db = ShopDB(DB_PATH)
db.create_table()


def error(message, status):
    return jsonify({"ok": False, "error": message}), status


def validate(form):
    """Return (clean_values, error_message)."""
    name = form.get("name", "").strip()
    region = form.get("region", "").strip()
    notes = form.get("notes", "").strip()
    if not name:
        return None, "Name is required."
    if not region:
        return None, "Region is required."
    try:
        rating = int(form.get("rating", ""))
    except ValueError:
        return None, "Rating must be a whole number."
    if not 1 <= rating <= 5:
        return None, "Rating must be between 1 and 5."
    return {"name": name, "region": region, "rating": rating, "notes": notes}, None


@app.route("/shops", methods=["GET"])
def list_shops():
    region = request.args.get("region", "").strip()
    min_rating = request.args.get("min_rating", "").strip()
    if min_rating:
        try:
            min_rating = int(min_rating)
        except ValueError:
            return error("min_rating must be a number.", 400)
    else:
        min_rating = None
    return jsonify({"ok": True, "shops": db.get_all(region, min_rating)})


@app.route("/shops/<int:shop_id>", methods=["GET"])
def get_shop(shop_id):
    shop = db.get_one(shop_id)
    if shop is None:
        return error("Shop not found.", 404)
    return jsonify({"ok": True, "shop": shop})


@app.route("/shops/add", methods=["POST"])
def add_shop():
    values, problem = validate(request.form)
    if problem:
        return error(problem, 400)
    shop = db.add(**values)
    return jsonify({"ok": True, "message": "Shop saved.", "shop": shop})


@app.route("/shops/edit/<int:shop_id>", methods=["POST"])
def edit_shop(shop_id):
    values, problem = validate(request.form)
    if problem:
        return error(problem, 400)
    shop = db.update(shop_id, **values)
    if shop is None:
        return error("Shop not found.", 404)
    return jsonify({"ok": True, "message": "Shop updated.", "shop": shop})


@app.route("/shops/delete/<int:shop_id>", methods=["POST"])
def delete_shop(shop_id):
    if not db.delete(shop_id):
        return error("Shop not found.", 404)
    return jsonify({"ok": True, "message": "Shop deleted."})


if __name__ == "__main__":
    app.run(port=5050)