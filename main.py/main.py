import os
import sys

PROJECT_ROOT =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.salary_input import salary_window
from ui.dashboard import dashboard_window

def start_app():
    def on_salary_submit(salary):
        dashboard_window(salary, master=root)

   
    import tkinter as tk
    root =tk.Tk()
    root.title("Expense Tracker")

    salary_window(on_submit=on_salary_submit, master=root)

    root.mainloop()

if __name__ =="__main__":
    start_app()
