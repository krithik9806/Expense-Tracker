import tkinter as tk
from tkinter import messagebox

def salary_window(on_submit, master=None):
    window = tk.Toplevel(master=master)
    window.title("Enter Monthly Salary")
    window.geometry("300x150")
    if master is not None:
        window.transient(master)
    window.lift()
    try:
        window.attributes('-topmost', True)
        window.after(100, lambda: window.attributes('-topmost', False))
    except Exception:
        pass

    tk.Label(window, text="Enter your monthly salary:").pack(pady=10)
    salary_var = tk.StringVar()
    tk.Entry(window, textvariable=salary_var).pack(pady=5)

    def submit_salary():
        try:
            salary = float(salary_var.get())
            if salary <= 0:
                raise ValueError
            on_submit(salary)
            window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid salary")

    tk.Button(window, text="Submit", command=submit_salary).pack(pady=10)
    window.grab_set()
    window.focus_set()
