import os
import sys
# Ensure project root is on sys.path so 'ui' and 'utils' imports resolve when run as a script
PROJECT_ROOT =os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.salary_input import salary_window
from ui.dashboard import dashboard_window

def start_app():
    def on_salary_submit(salary):
        dashboard_window(salary, master=root)

    # Open salary input window first
    import tkinter as tk
    root =tk.Tk()
    root.title("Expense Tracker")
    # Create the salary window first; keep root visible for troubleshooting
    salary_window(on_submit=on_salary_submit, master=root)
    # Keep mainloop running on the hidden root; dashboard opens as a Toplevel
    root.mainloop()

if __name__ =="__main__":
    start_app()
