import json
import socket
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "http://127.0.0.1:5050"


def call(path, values=None):
    """Send one request to Flask. Returns (data, error_message)."""
    body = urlencode(values).encode("utf-8") if values is not None else None
    try:
        with urlopen(BASE + path, data=body, timeout=5) as reply:
            return json.loads(reply.read().decode("utf-8")), None
    except HTTPError as error:  # 400 / 404 from Flask
        try:
            data = json.loads(error.read().decode("utf-8"))
            return None, data.get("error", "Request failed.")
        except ValueError:
            return None, f"Server error ({error.code})."
    except socket.timeout:
        return None, "The server took too long to answer."
    except URLError:
        return None, "Cannot connect to the server. Start Flask and try again."


class CoffeeApp(tk.Tk):
    FIELDS = ("name", "region", "rating", "notes")

    def __init__(self):
        super().__init__()
        self.title("Saudi Coffee Shop Guide")
        self.geometry("860x540")
        self.vars = {key: tk.StringVar() for key in self.FIELDS}
        self.filter_region = tk.StringVar()
        self.filter_rating = tk.StringVar()
        self.status = tk.StringVar()
        self.build()
        self.refresh()

    def build(self):
        form = ttk.LabelFrame(self, text="Coffee shop")
        form.pack(fill="x", padx=10, pady=8)
        labels = ("Name", "Region", "Rating (1-5)", "Notes")
        for i, (key, label) in enumerate(zip(self.FIELDS, labels)):
            ttk.Label(form, text=label).grid(row=i // 2, column=(i % 2) * 2, padx=6, pady=4, sticky="e")
            ttk.Entry(form, textvariable=self.vars[key], width=30).grid(
                row=i // 2, column=(i % 2) * 2 + 1, padx=6, pady=4
            )

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10)
        ttk.Button(buttons, text="Save new", command=self.add_shop).pack(side="left", padx=4)
        ttk.Button(buttons, text="Update selected", command=self.edit_shop).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete selected", command=self.delete_shop).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear form", command=self.clear_form).pack(side="left", padx=4)

        flt = ttk.LabelFrame(self, text="Filter")
        flt.pack(fill="x", padx=10, pady=8)
        ttk.Label(flt, text="Region").pack(side="left", padx=6)
        ttk.Entry(flt, textvariable=self.filter_region, width=18).pack(side="left")
        ttk.Label(flt, text="Min rating").pack(side="left", padx=6)
        ttk.Entry(flt, textvariable=self.filter_rating, width=6).pack(side="left")
        ttk.Button(flt, text="Apply", command=self.apply_filter).pack(side="left", padx=6)
        ttk.Button(flt, text="Show all", command=self.show_all).pack(side="left")

        columns = ("id", "name", "region", "rating", "notes")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col, width in zip(columns, (50, 200, 130, 70, 330)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True, padx=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.status_label = ttk.Label(self, textvariable=self.status)
        self.status_label.pack(fill="x", padx=10, pady=6)

    # ---------- helpers ----------
    def say(self, message, error=False):
        self.status.set(message)
        self.status_label.configure(foreground="red" if error else "green")

    def form_values(self):
        return {key: self.vars[key].get() for key in self.FIELDS}

    def clear_form(self):
        for var in self.vars.values():
            var.set("")
        self.tree.selection_remove(self.tree.selection())

    def selected_id(self):
        selection = self.tree.selection()
        if not selection:
            self.say("Select a shop from the list first.", error=True)
            return None
        return self.tree.item(selection[0])["values"][0]

    def on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        _id, name, region, rating, notes = self.tree.item(selection[0])["values"]
        for key, value in zip(self.FIELDS, (name, region, rating, notes)):
            self.vars[key].set(value)

    # ---------- actions ----------
    def refresh(self):
        query = {}
        if self.filter_region.get().strip():
            query["region"] = self.filter_region.get().strip()
        if self.filter_rating.get().strip():
            query["min_rating"] = self.filter_rating.get().strip()
        path = "/shops" + ("?" + urlencode(query) if query else "")
        data, problem = call(path)
        if problem:
            self.say(problem, error=True)
            return False
        self.tree.delete(*self.tree.get_children())
        for shop in data["shops"]:
            self.tree.insert("", "end", values=(
                shop["id"], shop["name"], shop["region"], shop["rating"], shop["notes"] or ""
            ))
        if data["shops"]:
            self.say(f"{len(data['shops'])} shop(s) loaded.")
        else:
            self.say("No shops found.")
        return True

    def apply_filter(self):
        self.refresh()

    def show_all(self):
        self.filter_region.set("")
        self.filter_rating.set("")
        self.refresh()

    def add_shop(self):
        data, problem = call("/shops/add", self.form_values())
        if problem:
            self.say(problem, error=True)
            return
        self.clear_form()
        self.refresh()
        self.say(data["message"])

    def edit_shop(self):
        shop_id = self.selected_id()
        if shop_id is None:
            return
        data, problem = call(f"/shops/edit/{shop_id}", self.form_values())
        if problem:
            self.say(problem, error=True)
            if problem == "Shop not found.":
                self.refresh()
                self.say(problem, error=True)
            return
        self.refresh()
        self.say(data["message"])

    def delete_shop(self):
        shop_id = self.selected_id()
        if shop_id is None:
            return
        if not messagebox.askyesno("Confirm", "Delete this coffee shop?"):
            return
        data, problem = call(f"/shops/delete/{shop_id}", {})
        if problem:
            self.say(problem, error=True)
            return
        self.clear_form()
        self.refresh()
        self.say(data["message"])


if __name__ == "__main__":
    CoffeeApp().mainloop()