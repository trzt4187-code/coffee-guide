# Saudi Coffee Shop Guide

**Author:** Tariq Eid Al-Amri · **Student ID:** 451008273 · **GitHub:** https://github.com/YOUR_USER/coffee-guide
Course: Advanced Programming 462 – Individual Project (Dr. Majed Hariri)

## What the application does
A desktop guide for coffee shops in Saudi Arabia. A **Tkinter** window lets the user
add, view, edit and delete coffee shops (name, region, rating 1–5, notes) and filter
them by region and minimum rating. The window never touches the database: it sends
HTTP requests to a **Flask** server on port 5050, and Flask stores the data in **SQLite**.

**Extra feature – Statistics:** the *Statistics* button shows the number of shops, the average
rating, the top-rated shop and the average rating per region (route `GET /shops/stats`).

```
Tkinter (gui.py)  <-- HTTP + JSON -->  Flask (app.py)  <-->  SQLite (coffee.db)
```

## Files
| File | Purpose |
|---|---|
| `app.py` | Flask back end, `ShopDB` class, validation, routes |
| `gui.py` | Tkinter front end (`CoffeeApp` class, `call()` helper) |
| `init_db.py` | Table setup code (+ optional sample data) |
| `report.py` | Report helper using a `Thread` and a UTF-8 file |
| `test_app.py` | Automated back-end tests |
| `requirements.txt` | Python packages (Flask) |
| `slides/` | Presentation slides |

## Install and run
Requires Python 3.9+ with Tkinter (included with the standard Python installer on Windows/macOS;
on Linux: `sudo apt install python3-tk`).

```bash
# 1. install packages (optional: use a virtual environment)
pip install -r requirements.txt

# 2. create the tables (safe to repeat; existing records are kept)
python init_db.py            # add --sample for 3 sample shops

# 3. start Flask FIRST (port 5050) - keep this terminal open
python app.py

# 4. start Tkinter in a second terminal
python gui.py
```

### Report command (threading demo)
With Flask running:
```bash
python report.py
```
It asks `GET /shops` for the saved records, starts one `Thread` that writes
`report.txt` (UTF-8), waits with `join()`, then prints whether the file was saved.

### Automated tests
```bash
python test_app.py
```

## HTTP routes
| Method | Route | Action |
|---|---|---|
| GET | `/shops?region=&min_rating=` | list / filter records (JSON) |
| GET | `/shops/<id>` | one record (404 if unknown) |
| GET | `/shops/stats` | statistics (extra feature) |
| POST | `/shops/add` | add (400 if invalid) |
| POST | `/shops/edit/<id>` | edit (400 invalid, 404 unknown) |
| POST | `/shops/delete/<id>` | delete (404 unknown) |

**One request explained (Save):** the user clicks *Save new* → `CoffeeApp.add_shop()` calls
`call("/shops/add", values)` → `urlencode(...).encode()` is passed as `data` to `urlopen`, which makes a POST →
Flask `add_shop()` reads `request.form`, `validate()` checks it, `ShopDB.add()` runs an `INSERT` with `?` placeholders →
Flask replies `{"ok": true, "message": "Shop saved.", "shop": {...}}` → the window reloads the table and shows the message.

## Where each course topic appears
| Topic | Evidence |
|---|---|
| Python and collections | `app.py`: `validate()` (conditions, dict of clean values), `ShopDB.get_all()` (list of dicts, `params` list), `ShopDB.stats()` (list comprehension); `gui.py`: `CoffeeApp.refresh()` (loop over records), `show_stats()`; `init_db.py`: `SAMPLES` list of tuples |
| Exceptions | `gui.py` `call()` (`HTTPError`, `socket.timeout`, `URLError`, `ValueError`); `app.py` `validate()` (`ValueError`) and `database_problem()` (`sqlite3.Error`); `report.py` `main()` and `write_report()` (`OSError`) |
| Classes | `app.py` class `ShopDB` (all database work); `gui.py` class `CoffeeApp(tk.Tk)` |
| SQLite | `app.py` `ShopDB`: `create_table`, `get_all`, `get_one`, `add`, `update`, `delete`, `stats`; `?` placeholders; a new connection per call, committed with `with conn:` and closed with `closing()` |
| Threads and files | `report.py`: `Thread(target=write_report)`, `start()`, `join()`, `with open(..., encoding="utf-8")` |
| Tkinter | `gui.py` `CoffeeApp.build()`: labels, entries, buttons, `Treeview`, confirmation `askyesno`, status label (green/red) |
| Client and server | `gui.py` `call()` ↔ `app.py` routes (see "One request explained") |
| Flask | `app.py`: `@app.route` functions, `validate()`, `error()`, `jsonify`, error handler |

## Test results
Automated (`python test_app.py`, 8 tests, **all passed**): empty list; add/view/edit/delete;
only the chosen record changes; missing and invalid input (empty name/region, non-numeric rating,
rating 9, too-long name); unknown ID (404 for get, edit, delete); filters; SQL-injection text stored as plain text;
statistics (empty and filled).

Back end and report helper, checked against a running server:
- Report helper saved `report.txt` with the saved shops and the total/average line.
- Stopped Flask → `report.py` printed "Cannot connect to Flask. Start app.py first."
- Restarted Flask → previously added records were still there (data persists in `coffee.db`).

Tkinter manual checklist (tick after running it on your own computer):
- [ ] Add, view, edit, delete; confirmation dialog appears before delete
- [ ] Missing name / rating 9 / rating "abc" → red error message
- [ ] Empty list → "No shops found."
- [ ] Unknown ID: select a shop in two windows, delete it in one, edit it in the other → "Shop not found."
- [ ] Stop Flask, click an action → connection error; start Flask, click again → works without restarting the window
- [ ] Statistics button

## Credits
- Python standard library, Flask (BSD licence), Tkinter, SQLite.

