import tkinter as tk
from tkinter import ttk, messagebox
import json, os
from datetime import datetime

# ── Constants ────────────────────────────────────────────────
DATA_FILE = "transactions.json"

COLORS = {
    "bg":     "#F0F4F8",
    "panel":  "#FFFFFF",
    "blue":   "#4361EE",
    "green":  "#2DC653",
    "red":    "#E63946",
    "text":   "#1D3557",
    "gray":   "#6B7A99",
    "border": "#DDE3F0",
}

INCOME_CATS  = ["Salary", "Freelance", "Other Income"]
EXPENSE_CATS = ["Food", "Transport", "Housing",
                "Education", "Health", "Entertainment", "Other"]

# ── Data Manager ─────────────────────────────────────────────
class DataManager:
    """Handles all file I/O and calculations."""

    def __init__(self):
        self.records = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.records = json.load(f)

    def save(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.records, f, indent=2)

    def add(self, record: dict):
        self.records.append(record)
        self.save()

    def delete(self, index: int):
        self.records.pop(index)
        self.save()

    def summary(self):
        income  = sum(r["amount"] for r in self.records if r["type"] == "income")
        expense = sum(r["amount"] for r in self.records if r["type"] == "expense")
        return income, expense, income - expense


# ── Main Application ─────────────────────────────────────────
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.dm      = DataManager()
        self.tx_type = tk.StringVar(value="income")

        self.title("Personal Finance Tracker")
        self.geometry("960x640")
        self.minsize(720, 500)
        self.configure(bg=COLORS["bg"])

        self._setup_treeview_style()
        self._build_ui()
        self._refresh()

    # ── Treeview style (called once) ─────────────────────────
    def _setup_treeview_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview",
                    font=("Segoe UI", 10), rowheight=30,
                    background="white", fieldbackground="white")
        s.configure("Treeview.Heading",
                    font=("Segoe UI", 10, "bold"),
                    background=COLORS["border"])
        s.map("Treeview",
              background=[("selected", COLORS["blue"])],
              foreground=[("selected", "white")])

    # ── Build UI ─────────────────────────────────────────────
    def _build_ui(self):
        # Header bar
        bar = tk.Frame(self, bg=COLORS["blue"], pady=14)
        bar.pack(fill="x")
        tk.Label(bar, text="💰  Personal Finance Tracker",
                 font=("Segoe UI", 17, "bold"),
                 bg=COLORS["blue"], fg="white").pack()

        # Main body: left panel + right panel
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=14)

        # Left column has fixed width; right column stretches
        body.columnconfigure(0, weight=0, minsize=240)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    # ── Left panel: cards + form ──────────────────────────────
    def _build_left(self, parent):
        left = tk.Frame(parent, bg=COLORS["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.columnconfigure(0, weight=1)

        # Summary cards
        self.lbl_income  = self._card(left, "Income",  COLORS["green"])
        self.lbl_expense = self._card(left, "Expense", COLORS["red"])
        self.lbl_balance = self._card(left, "Balance", COLORS["blue"], large=True)

        # ── Form panel ──
        form = tk.Frame(left, bg=COLORS["panel"], padx=14, pady=12,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        form.pack(fill="x", pady=(6, 0))
        form.columnconfigure(0, weight=1)

        tk.Label(form, text="Add Transaction",
                 font=("Segoe UI", 12, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 8))

        # Income / Expense toggle
        btn_row = tk.Frame(form, bg=COLORS["panel"])
        btn_row.pack(fill="x", pady=(0, 10))
        btn_row.columnconfigure((0, 1), weight=1)

        self.btn_inc = tk.Button(
            btn_row, text="Income",
            command=lambda: self._set_type("income"),
            font=("Segoe UI", 10), relief="flat", cursor="hand2", pady=5)
        self.btn_exp = tk.Button(
            btn_row, text="Expense",
            command=lambda: self._set_type("expense"),
            font=("Segoe UI", 10), relief="flat", cursor="hand2", pady=5)
        self.btn_inc.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.btn_exp.grid(row=0, column=1, sticky="ew")

        # Category, Description, Amount
        fields = [
            ("Category",    None),
            ("Description", "entry"),
            ("Amount ($)",  "amount"),
        ]
        for label, kind in fields:
            tk.Label(form, text=label, font=("Segoe UI", 10),
                     bg=COLORS["panel"], fg=COLORS["gray"]).pack(anchor="w")
            if kind is None:
                self.var_cat = tk.StringVar()
                self.cmb_cat = ttk.Combobox(
                    form, textvariable=self.var_cat,
                    state="readonly", font=("Segoe UI", 10))
                self.cmb_cat.pack(fill="x", pady=(2, 8), ipady=3)
                self._set_type("income")
            elif kind == "entry":
                self.ent_desc = tk.Entry(
                    form, font=("Segoe UI", 10), relief="solid", bd=1)
                self.ent_desc.pack(fill="x", pady=(2, 8), ipady=4)
            elif kind == "amount":
                self.ent_amt = tk.Entry(
                    form, font=("Consolas", 10), relief="solid", bd=1)
                self.ent_amt.pack(fill="x", pady=(2, 12), ipady=4)
                # Bind Enter key to submit
                self.ent_amt.bind("<Return>", lambda e: self._add())

        tk.Button(form, text="Add Transaction", command=self._add,
                  font=("Segoe UI", 11, "bold"),
                  bg=COLORS["blue"], fg="white",
                  relief="flat", cursor="hand2", pady=8).pack(fill="x")

    # ── Right panel: transaction history table ────────────────
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=COLORS["panel"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Panel header
        hdr = tk.Frame(right, bg=COLORS["panel"], padx=12, pady=10)
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="Transaction History",
                 font=("Segoe UI", 12, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left")
        tk.Button(hdr, text="🗑  Delete", command=self._delete,
                  font=("Segoe UI", 10), bg=COLORS["red"], fg="white",
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="right")
        tk.Frame(right, height=1, bg=COLORS["border"]).grid(
            row=0, column=0, sticky="ews", pady=(48, 0))

        # Treeview + scrollbar
        tree_frame = tk.Frame(right, bg=COLORS["panel"])
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        cols = ("Date", "Type", "Category", "Description", "Amount")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", selectmode="browse")

        # Column widths — Description stretches with window
        widths   = [115, 75, 100, 0, 110]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            if w:
                self.tree.column(col, width=w, stretch=False, anchor="w")
            else:
                self.tree.column(col, stretch=True, anchor="w", minwidth=120)

        self.tree.tag_configure("income",  foreground=COLORS["green"])
        self.tree.tag_configure("expense", foreground=COLORS["red"])

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    # ── Helper: summary card ──────────────────────────────────
    def _card(self, parent, label, color, large=False):
        """Create a coloured summary card; return the value Label."""
        card = tk.Frame(parent, bg=color, padx=12, pady=8)
        card.pack(fill="x", pady=(0, 6))
        tk.Label(card, text=label, font=("Segoe UI", 9),
                 bg=color, fg="white").pack(anchor="w")
        val = tk.Label(card, text="$0.00",
                       font=("Segoe UI", 15 if large else 12, "bold"),
                       bg=color, fg="white")
        val.pack(anchor="w")
        return val

    # ── Logic ─────────────────────────────────────────────────
    def _set_type(self, t: str):
        """Toggle between Income and Expense mode."""
        self.tx_type.set(t)
        if t == "income":
            self.btn_inc.config(bg=COLORS["green"], fg="white", text="✅ Income")
            self.btn_exp.config(bg=COLORS["border"], fg=COLORS["gray"], text="Expense")
            self.cmb_cat["values"] = INCOME_CATS
        else:
            self.btn_exp.config(bg=COLORS["red"],   fg="white", text="✅ Expense")
            self.btn_inc.config(bg=COLORS["border"], fg=COLORS["gray"], text="Income")
            self.cmb_cat["values"] = EXPENSE_CATS
        self.var_cat.set(self.cmb_cat["values"][0])

    def _add(self):
        """Validate inputs, save record, refresh display."""
        desc = self.ent_desc.get().strip()
        try:
            amount = float(self.ent_amt.get())
            assert amount > 0
        except:
            messagebox.showwarning("Invalid Input", "Please enter a valid positive amount.")
            return
        if not desc:
            messagebox.showwarning("Invalid Input", "Please enter a description.")
            return

        self.dm.add({
            "date":     datetime.now().strftime("%d/%m/%Y %H:%M"),
            "type":     self.tx_type.get(),
            "category": self.var_cat.get(),
            "desc":     desc,
            "amount":   amount,
        })
        self.ent_desc.delete(0, "end")
        self.ent_amt.delete(0, "end")
        self.ent_desc.focus()
        self._refresh()

    def _delete(self):
        """Delete the selected row after confirmation."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No Selection", "Please select a row to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete selected transaction?"):
            n = len(self.dm.records)
            self.dm.delete(n - 1 - self.tree.index(sel[0]))
            self._refresh()

    def _refresh(self):
        """Recalculate summary cards and repopulate the table."""
        income, expense, balance = self.dm.summary()
        self.lbl_income.config(text=f"${income:,.2f}")
        self.lbl_expense.config(text=f"${expense:,.2f}")
        self.lbl_balance.config(text=f"${balance:,.2f}")

        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in reversed(self.dm.records):
            tag  = r.get("type", "expense")
            sign = "+" if tag == "income" else "-"
            self.tree.insert("", "end", values=(
                r.get("date", "-"),
                tag.capitalize(),
                r.get("category", "-"),
                r.get("desc", "-"),
                f"{sign}${r.get('amount', 0):,.2f}",
            ), tags=(tag,))

# ── Run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()