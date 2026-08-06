import tkinter as tk
from tkinter import ttk, messagebox
from utils.data_handler import add_expense
from datetime import datetime

def expense_window(on_add=None, master=None, initial=None, on_submit=None):
    window = tk.Toplevel(master=master)
    window.title("Add Expense")
    window.geometry("400x300")
    if master is not None:
        window.transient(master)
    window.lift()
    try:
        window.attributes('-topmost', True)
        window.after(100, lambda: window.attributes('-topmost', False))
    except Exception:
        pass

    tk.Label(window, text="Date (DD-MM-YYYY):").pack(pady=5)
    # initial["date"] is stored as YYYY-MM-DD; display as DD-MM-YYYY
    if initial and initial.get("date"):
        try:
            _dt = datetime.strptime(initial.get("date"), "%Y-%m-%d")
            date_default = _dt.strftime("%d-%m-%Y")
        except Exception:
            date_default = datetime.now().strftime("%d-%m-%Y")
    else:
        date_default = datetime.now().strftime("%d-%m-%Y")
    date_var = tk.StringVar(value=date_default)
    tk.Entry(window, textvariable=date_var).pack(pady=5)

    tk.Label(window, text="Category:").pack(pady=5)
    category_var = tk.StringVar(value=(initial.get("category") if initial else ""))
    categories = ["Food", "Rent", "Utilities", "Transport", "Entertainment", "Others"]
    ttk.Combobox(window, textvariable=category_var, values=categories).pack(pady=5)

    tk.Label(window, text="Amount:").pack(pady=5)
    amount_var = tk.StringVar(value=(str(initial.get("amount")) if initial and initial.get("amount") is not None else ""))
    tk.Entry(window, textvariable=amount_var).pack(pady=5)

    tk.Label(window, text="Description:").pack(pady=5)
    desc_var = tk.StringVar(value=(initial.get("description") if initial else ""))
    tk.Entry(window, textvariable=desc_var).pack(pady=5)

    def add_expense_action():
        try:
            # Convert from DD-MM-YYYY to YYYY-MM-DD for storage
            _dt = datetime.strptime(date_var.get(), "%d-%m-%Y")
            date = _dt.strftime("%Y-%m-%d")
            category = category_var.get()
            amount = float(amount_var.get())
            description = desc_var.get()
            if not category:
                raise ValueError("Select category")
            if on_submit:
                on_submit({
                    "date": date,
                    "category": category,
                    "amount": amount,
                    "description": description,
                })
            else:
                add_expense(date, category, amount, description)
                if on_add:
                    on_add()
                messagebox.showinfo("Success", "Expense added!")
            window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    tk.Button(window, text=("Save" if on_submit else "Add Expense"), command=add_expense_action).pack(pady=10)
    window.grab_set()
    window.focus_set()