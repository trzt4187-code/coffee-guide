"""Automated checks for the Flask back end. Run: python test_app.py"""
import os
import tempfile
import unittest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["COFFEE_DB"] = _tmp.name  # use a throw-away database

from app import app  # noqa: E402


class ShopTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()
        for shop in self.c.get("/shops").get_json()["shops"]:
            self.c.post(f"/shops/delete/{shop['id']}")

    def add(self, **kw):
        values = {"name": "Qahwa", "region": "Riyadh", "rating": "4", "notes": "ok"}
        values.update(kw)
        return self.c.post("/shops/add", data=values)

    def test_empty_list(self):
        self.assertEqual(self.c.get("/shops").get_json()["shops"], [])

    def test_add_view_edit_delete(self):
        shop = self.add().get_json()["shop"]
        self.assertEqual(len(self.c.get("/shops").get_json()["shops"]), 1)
        r = self.c.post(f"/shops/edit/{shop['id']}",
                        data={"name": "New", "region": "Jeddah", "rating": "5", "notes": ""})
        self.assertEqual(r.get_json()["shop"]["name"], "New")
        self.assertEqual(self.c.post(f"/shops/delete/{shop['id']}").status_code, 200)
        self.assertEqual(self.c.get("/shops").get_json()["shops"], [])

    def test_only_chosen_record_changes(self):
        a = self.add(name="A").get_json()["shop"]
        b = self.add(name="B").get_json()["shop"]
        self.c.post(f"/shops/delete/{a['id']}")
        left = self.c.get("/shops").get_json()["shops"]
        self.assertEqual([s["name"] for s in left], ["B"])
        self.assertEqual(left[0]["id"], b["id"])

    def test_missing_and_invalid_input(self):
        self.assertEqual(self.add(name="").status_code, 400)
        self.assertEqual(self.add(region=" ").status_code, 400)
        self.assertEqual(self.add(rating="abc").status_code, 400)
        self.assertEqual(self.add(rating="9").status_code, 400)
        self.assertEqual(self.add(name="x" * 101).status_code, 400)

    def test_unknown_id(self):
        self.assertEqual(self.c.get("/shops/9999").status_code, 404)
        r = self.c.post("/shops/edit/9999",
                        data={"name": "a", "region": "b", "rating": "3"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.c.post("/shops/delete/9999").status_code, 404)

    def test_filters(self):
        self.add(name="A", region="Riyadh", rating="5")
        self.add(name="B", region="Jeddah", rating="2")
        names = lambda q: [s["name"] for s in self.c.get("/shops" + q).get_json()["shops"]]
        self.assertEqual(names("?region=Riyadh"), ["A"])
        self.assertEqual(names("?min_rating=3"), ["A"])
        self.assertEqual(self.c.get("/shops?min_rating=x").status_code, 400)

    def test_sql_injection_is_just_text(self):
        self.add(name="x'); DROP TABLE shops;--")
        self.assertEqual(len(self.c.get("/shops").get_json()["shops"]), 1)

    def test_stats(self):
        empty = self.c.get("/shops/stats").get_json()["stats"]
        self.assertEqual(empty["total"], 0)
        self.assertIsNone(empty["best"])
        self.add(name="A", region="Riyadh", rating="5")
        self.add(name="B", region="Riyadh", rating="3")
        stats = self.c.get("/shops/stats").get_json()["stats"]
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["average"], 4.0)
        self.assertEqual(stats["best"]["name"], "A")
        self.assertEqual(stats["regions"][0]["count"], 2)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        os.unlink(_tmp.name)
