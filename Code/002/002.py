import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
FILE = "transactions.json"

C = {
    "bg":      "#F0F4F8",
    "sidebar": "#1E3A5F",
    "income":  "#27AE60",
    "expense": "#E74C3C",
    "accent":  "#2980B9",
    "card":    "#FFFFFF",
    "sub":     "#7F8C8D",
    "gold":    "#F39C12",
}

CATEGORIES = {
    "Income":  ["Salary", "Freelance", "Sales", "Interest", "Gift", "Other"],
    "Expense": ["Food", "Transport", "Housing", "Clothing",
                "Entertainment", "Health", "Education", "Shopping", "Other"],
}

FN = ("Segoe UI", 10)
FB = ("Segoe UI", 11, "bold")
FS = ("Segoe UI", 9)

# ── Data helpers ──────────────────────────────────────────────────────────────
def load():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    migrated = []
    for t in raw:
        migrated.append({
            "date":     t.get("date")     or t.get("วันที่",    ""),
            "type":     t.get("type")     or t.get("ประเภท",    "Income"),
            "category": t.get("category") or t.get("หมวดหมู่", "Other"),
            "amount":   t.get("amount")   or t.get("จำนวนเงิน", 0.0),
            "note":     t.get("note")     or t.get("หมายเหตุ",  ""),
        })
    return migrated

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_entry(data, kind, cat, amount, note):
    data.append({
        "date":     datetime.date.today().strftime("%d/%m/%Y"),
        "type":     kind,
        "category": cat,
        "amount":   float(amount),
        "note":     note,
    })
    save(data)

def delete_entry(data, idx):
    data.pop(idx)
    save(data)

def get_summary(data):
    inc = np.array([t["amount"] for t in data if t["type"] == "Income"] or [0])
    exp = np.array([t["amount"] for t in data if t["type"] == "Expense"] or [0])
    return {
        "total_inc": float(np.sum(inc)),
        "total_exp": float(np.sum(exp)),
        "balance":   float(np.sum(inc) - np.sum(exp)),
        "avg_inc":   float(np.mean(inc)),
        "avg_exp":   float(np.mean(exp)),
    }

# ── Application ───────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("💰 Income & Expense Tracker")
        self.minsize(700, 500)
        self.geometry("1060x680")
        self.configure(bg=C["bg"])

        self.data       = load()
        self.filter_var = tk.StringVar(value="All")
        self.type_var   = tk.StringVar(value="Income")
        self.cat_var    = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.note_var   = tk.StringVar()

        self._build()
        self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Fixed-width sidebar on the left
        self.sb_frame = tk.Frame(self, bg=C["sidebar"], width=260)
        self.sb_frame.pack(side="left", fill="y")
        self.sb_frame.pack_propagate(False)

        # Right panel expands freely
        right = tk.Frame(self, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True)

        # Summary cards row
        self.card_row = tk.Frame(right, bg=C["bg"])
        self.card_row.pack(fill="x", padx=16, pady=(16, 8))

        self._toolbar(right)
        self._table(right)
        self._form()

    # ── Sidebar form ──────────────────────────────────────────────────────────

    def _form(self):
        sb = self.sb_frame
        tk.Label(sb, text="💰 Finance Tracker", bg=C["sidebar"], fg="white",
                 font=("Segoe UI", 15, "bold")).pack(pady=(22, 2))
        tk.Label(sb, text="Track your money easily",
                 bg=C["sidebar"], fg="#BDC3C7", font=FS).pack()
        ttk.Separator(sb).pack(fill="x", padx=18, pady=14)

        frm = tk.Frame(sb, bg=C["sidebar"])
        frm.pack(fill="x", padx=20)

        # -- Type radio buttons --
        self._lbl(frm, "Type")
        rb = tk.Frame(frm, bg=C["sidebar"])
        rb.pack(fill="x", pady=(4, 12))
        for name, color in [("Income", C["income"]), ("Expense", C["expense"])]:
            tk.Radiobutton(rb, text=name, variable=self.type_var, value=name,
                           bg=C["sidebar"], fg=color, selectcolor=C["sidebar"],
                           activebackground=C["sidebar"], font=FN,
                           command=self._sync_cats).pack(side="left", padx=6)

        # -- Category dropdown --
        self._lbl(frm, "Category")
        self.cat_cb = ttk.Combobox(frm, textvariable=self.cat_var,
                                   state="readonly", font=FN)
        self.cat_cb.pack(fill="x", pady=(4, 12))
        self._sync_cats()

        # -- Amount & Note fields --
        for lbl, var in [("Amount (THB)", self.amount_var),
                          ("Note (optional)", self.note_var)]:
            self._lbl(frm, lbl)
            tk.Entry(frm, textvariable=var, font=FN, relief="flat",
                     bg="#2C4F73", fg="white",
                     insertbackground="white").pack(fill="x", ipady=6, pady=(4, 12))

        # -- Submit button --
        tk.Button(frm, text="➕  Add Transaction", bg=C["accent"], fg="white",
                  font=FB, relief="flat", cursor="hand2",
                  activebackground="#1a6fa3",
                  command=self._on_add).pack(fill="x", ipady=8, pady=(4, 0))

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, bg=C["sidebar"],
                 fg="white", font=FB).pack(anchor="w")

    def _sync_cats(self):
        cats = CATEGORIES[self.type_var.get()]
        self.cat_cb["values"] = cats
        self.cat_var.set(cats[0])

    # ── Toolbar ───────────────────────────────────────────────────────────────
    def _toolbar(self, parent):
        bar = tk.Frame(parent, bg=C["bg"])
        bar.pack(fill="x", padx=16, pady=(0, 6))

        tk.Label(bar, text="Show:", bg=C["bg"],
                 fg="#2C3E50", font=FN).pack(side="left")
        for opt in ["All", "Income", "Expense"]:
            tk.Radiobutton(bar, text=opt, variable=self.filter_var, value=opt,
                           bg=C["bg"], fg="#2C3E50", activebackground=C["bg"],
                           font=FN, command=self._refresh_table
                           ).pack(side="left", padx=4)

        tk.Button(bar, text="🗑  Delete Selected",
                  bg=C["expense"], fg="white", font=FS,
                  relief="flat", cursor="hand2", activebackground="#c0392b",
                  command=self._on_delete).pack(side="right")

    # ── Table ─────────────────────────────────────────────────────────────────
    def _table(self, parent):
        frame = tk.Frame(parent, bg=C["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols    = ("Date", "Type", "Category", "Amount", "Note")
        weights = (1, 1, 1, 1, 3)

        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", selectmode="extended")
        for col in cols:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", minwidth=70, stretch=True)

        # Resize columns whenever the frame width changes
        self._col_weights = dict(zip(cols, weights))
        frame.bind("<Configure>",
                   lambda e: self._resize_cols(e.width))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Apply styles
        s = ttk.Style()
        s.configure("Treeview", font=FN, rowheight=32,
                    background=C["card"], fieldbackground=C["card"])
        s.configure("Treeview.Heading", font=FB)
        s.map("Treeview", background=[("selected", C["accent"])])
        self.tree.tag_configure("Income",  foreground=C["income"])
        self.tree.tag_configure("Expense", foreground=C["expense"])

    def _resize_cols(self, total_width):
        avail = max(total_width - 20, 1)
        total = sum(self._col_weights.values())
        for col, w in self._col_weights.items():
            self.tree.column(col, width=int(avail * w / total))

    # ── Summary cards ─────────────────────────────────────────────────────────
    def _refresh_cards(self):
        for w in self.card_row.winfo_children():
            w.destroy()
        s = get_summary(self.data)
        for lbl, val, color in [
            ("💚 Total Income",   s["total_inc"], C["income"]),
            ("❤️  Total Expense", s["total_exp"], C["expense"]),
            ("💛 Balance",        s["balance"],   C["gold"]),
            ("📈 Avg Income",     s["avg_inc"],   C["accent"]),
            ("📉 Avg Expense",    s["avg_exp"],   C["sub"]),
        ]:
            card = tk.Frame(self.card_row, bg=C["card"])
            card.pack(side="left", expand=True, fill="both", padx=4)
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=lbl,  bg=C["card"], fg=C["sub"],  font=FS).pack(pady=(8, 2))
            tk.Label(card, text=f"{val:,.2f} ฿", bg=C["card"], fg=color,
                     font=("Segoe UI", 13, "bold")).pack(pady=(0, 10))

    # ── Table refresh ─────────────────────────────────────────────────────────
    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        f = self.filter_var.get()
        for t in self.data:
            if f != "All" and t["type"] != f:
                continue
            self.tree.insert("", "end", tag=t["type"],
                             values=(t["date"], t["type"], t["category"],
                                     f"{t['amount']:,.2f} ฿", t["note"]))

    def _refresh(self):
        self._refresh_cards()
        self._refresh_table()

    # ── Actions ───────────────────────────────────────────────────────────────
    def _on_add(self):
        raw = self.amount_var.get().strip()
        if not raw:
            messagebox.showwarning("Warning", "Please enter an amount.")
            return
        try:
            amt = float(raw)
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number.")
            return

        add_entry(self.data, self.type_var.get(), self.cat_var.get(),
                  amt, self.note_var.get().strip())
        self.amount_var.set("")
        self.note_var.set("")
        self._refresh()
        messagebox.showinfo("Added ✅",
                            f"{self.type_var.get()} of {amt:,.2f} ฿ recorded.")

    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a row to delete.")
            return
        if not messagebox.askyesno("Confirm", "Delete selected transaction(s)?"):
            return

        for s in sel:
            sv = self.tree.item(s, "values")
            for i, t in enumerate(self.data):
                if (t["date"] == sv[0] and t["type"] == sv[1] and
                        t["category"] == sv[2] and
                        f"{t['amount']:,.2f} ฿" == sv[3] and
                        t["note"] == sv[4]):
                    delete_entry(self.data, i)
                    break

        self._refresh()
        messagebox.showinfo("Deleted 🗑", "Transaction(s) removed.")

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
