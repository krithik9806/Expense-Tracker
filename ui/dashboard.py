import tkinter as tk
from tkinter import ttk, messagebox
from utils.data_handler import (
    load_expenses,
    calculate_total_expenses,
    load_expenses_for_month,
    list_available_months,
    sum_total,
    sum_by_category,
    sum_by_day,
    load_expenses_between,
    export_expenses_to_csv,
    load_expenses_between_with_indices,
    load_expenses_with_indices,
    update_expense_at,
    delete_expense_at,
    load_budgets,
    save_budgets,
    save_goal,
    load_goal,
    save_weekly_challenge,
    load_weekly_challenge,
    iso_week_bounds,
    load_expenses_between_dates_iso,
    sum_expenses_between,
    sum_expenses_by_category_between,
    load_family,
    save_family,
)
from collections import defaultdict
import importlib

def dashboard_window(salary, master=None):
    # Dynamically import matplotlib modules to avoid static import warnings in some IDE linters
    try:
        mpl_backend = importlib.import_module("matplotlib.backends.backend_tkagg")
        FigureCanvasTkAgg = getattr(mpl_backend, "FigureCanvasTkAgg")
        plt = importlib.import_module("matplotlib.pyplot")
    except Exception:
        messagebox.showerror("Error", "matplotlib is required for charts but could not be imported.")
        return

    # Use a Toplevel so we don't create a second Tk root
    window = tk.Toplevel(master=master)
    window.title("Expense Tracker Dashboard")
    window.geometry("1200x800")
    try:
        window.minsize(1000, 700)
    except Exception:
        pass
    if master is not None:
        window.transient(master)
    window.lift()
    try:
        window.attributes('-topmost', True)
        window.after(100, lambda: window.attributes('-topmost', False))
    except Exception:
        pass

    # Controls frame (split into two rows to avoid overflow)
    controls = tk.Frame(window)
    controls.pack(fill=tk.X, padx=10, pady=(10,5))
    controls_row2 = tk.Frame(window)
    controls_row2.pack(fill=tk.X, padx=10, pady=(0,10))
    # Right-aligned container for action buttons
    btns_container = tk.Frame(controls_row2)
    btns_container.pack(side=tk.RIGHT)

    tk.Label(controls, text=f"Monthly Salary: ₹{salary:.2f}", font=("Arial", 12)).pack(side=tk.LEFT)
    # Show shared budget if set
    family_data = load_family()
    shared_budget_val = family_data.get("shared_budget", 0.0)
    shared_label = tk.Label(controls, text=(f"  |  Family Budget: ₹{shared_budget_val:.2f}" if shared_budget_val > 0 else ""), font=("Arial", 10))
    shared_label.pack(side=tk.LEFT)

    # Date range filter (DD-MM-YYYY)
    tk.Label(controls, text="From (DD-MM-YYYY):").pack(side=tk.LEFT, padx=(20, 5))
    from_var = tk.StringVar()
    from_entry = ttk.Entry(controls, textvariable=from_var, width=12)
    from_entry.pack(side=tk.LEFT)
    tk.Label(controls, text="To (DD-MM-YYYY):").pack(side=tk.LEFT, padx=(10, 5))
    to_var = tk.StringVar()
    to_entry = ttk.Entry(controls, textvariable=to_var, width=12)
    to_entry.pack(side=tk.LEFT)
    
    # Apply dates button
    def on_set_dates():
        render()
    ttk.Button(controls, text="Set", command=on_set_dates).pack(side=tk.LEFT, padx=(10, 0))

    # Action buttons
    def on_refresh():
        render()

    def on_add_expense():
        try:
            from ui.expense_entry import expense_window
        except Exception as e:
            messagebox.showerror("Error", f"Could not open Add Expense window: {e}")
            return

        def after_add():
            render()

        # Attach to this window for modality
        expense_window(after_add, master=window)

    def on_clear_filters():
        from_var.set("")
        to_var.set("")
        render()

    ttk.Button(btns_container, text="Refresh", command=on_refresh).pack(side=tk.RIGHT)
    ttk.Button(btns_container, text="Clear", command=on_clear_filters).pack(side=tk.RIGHT, padx=(0,10))
    ttk.Button(btns_container, text="Add Expense", command=on_add_expense).pack(side=tk.RIGHT, padx=(0,10))

    # Export button
    def on_export():
        try:
            start_date = from_var.get().strip()
            end_date = to_var.get().strip()
            # Convert DD-MM-YYYY to YYYY-MM-DD for filtering
            def _to_iso(s):
                if not s:
                    return ""
                try:
                    from datetime import datetime as _dt
                    return _dt.strptime(s, "%d-%m-%Y").strftime("%Y-%m-%d")
                except Exception:
                    return ""
            s_iso = _to_iso(start_date)
            e_iso = _to_iso(end_date)
            if s_iso or e_iso:
                export_rows = load_expenses_between(s_iso, e_iso)
            else:
                export_rows = load_expenses()
            from tkinter import filedialog
            target = filedialog.asksaveasfilename(
                title="Export Expenses",
                defaultextension=".csv",
                filetypes=[("CSV files","*.csv")],
                initialfile="expenses_export.csv",
            )
            if not target:
                return
            export_expenses_to_csv(export_rows, target)
            messagebox.showinfo("Export", "Expenses exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    ttk.Button(btns_container, text="Export CSV", command=on_export).pack(side=tk.RIGHT, padx=(0,10))

    # Manage Family dialog
    def on_manage_family():
        fam = load_family()
        dlg = tk.Toplevel(master=window)
        dlg.title("Manage Family")
        dlg.geometry("560x460")
        frm = tk.Frame(dlg)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Shared budget
        tk.Label(frm, text="Shared Monthly Family Budget:").grid(row=0, column=0, sticky='w')
        sb_var = tk.StringVar(value=str(fam.get("shared_budget", 0)))
        tk.Entry(frm, textvariable=sb_var, width=12).grid(row=0, column=1, sticky='w')

        # Members list
        cols = ("name", "role")
        tv = ttk.Treeview(frm, columns=cols, show='headings', height=10)
        for c in cols:
            tv.heading(c, text=c.title())
        vs = ttk.Scrollbar(frm, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        tv.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=(8,8))
        vs.grid(row=1, column=3, sticky='ns', pady=(8,8))
        frm.grid_rowconfigure(1, weight=1)
        frm.grid_columnconfigure(2, weight=1)

        def refresh_members():
            for i in tv.get_children():
                tv.delete(i)
            for m in fam.get("members", []):
                tv.insert('', tk.END, values=(m.get("name",""), m.get("role","Member")))

        # Add/edit controls
        tk.Label(frm, text="Name:").grid(row=2, column=0, sticky='e')
        name_var = tk.StringVar()
        tk.Entry(frm, textvariable=name_var, width=16).grid(row=2, column=1, sticky='w')
        tk.Label(frm, text="Role:").grid(row=2, column=2, sticky='e')
        role_var = tk.StringVar(value="Member")
        role_combo = ttk.Combobox(frm, textvariable=role_var, values=["Admin","Member"], width=12, state='readonly')
        role_combo.grid(row=2, column=3, sticky='w')

        def add_member():
            name = (name_var.get() or '').strip()
            role = (role_var.get() or 'Member').strip()
            if not name:
                return
            fam.setdefault("members", []).append({"name": name, "role": role})
            refresh_members()
            name_var.set("")
            role_var.set("Member")

        def remove_selected():
            sel = tv.selection()
            if not sel:
                return
            val = tv.item(sel[0], 'values')
            name = val[0]
            fam["members"] = [m for m in fam.get("members", []) if m.get("name") != name]
            refresh_members()

        def on_select(event=None):
            sel = tv.selection()
            if not sel:
                return
            val = tv.item(sel[0], 'values')
            if val:
                name_var.set(val[0])
                role_var.set(val[1] or 'Member')
                try:
                    role_combo.set(val[1])
                except Exception:
                    pass
        tv.bind('<<TreeviewSelect>>', on_select)

        def save_family_changes():
            try:
                sb = float(sb_var.get())
            except Exception:
                sb = 0.0
            save_family(sb, fam.get("members", []))
            # Update header label
            shared_label.config(text=(f"  |  Family Budget: ₹{sb:.2f}" if sb > 0 else ""))
            dlg.destroy()

        tk.Button(frm, text="Add", command=add_member).grid(row=3, column=1, sticky='w', pady=(8,0))
        tk.Button(frm, text="Remove Selected", command=remove_selected).grid(row=3, column=2, sticky='w', pady=(8,0))
        tk.Button(frm, text="Save & Close", command=save_family_changes).grid(row=3, column=3, sticky='w', pady=(8,0))

        refresh_members()

    ttk.Button(btns_container, text="Manage Family", command=on_manage_family).pack(side=tk.RIGHT, padx=(0,10))

    # Budgets management
    def on_manage_budgets():
        budgets = load_budgets()
        dlg = tk.Toplevel(master=window)
        dlg.title("Manage Budgets")
        dlg.geometry("400x350")
        dlg.transient(window)
        dlg.lift()
        try:
            dlg.attributes('-topmost', True)
            dlg.after(100, lambda: dlg.attributes('-topmost', False))
        except Exception:
            pass

        frame = tk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cols = ("category", "monthly_budget")
        tv = ttk.Treeview(frame, columns=cols, show='headings', height=10)
        for c in cols:
            tv.heading(c, text=c.replace('_',' ').title())
        tv.column("category", width=180)
        tv.column("monthly_budget", width=120, anchor='e')
        vs = ttk.Scrollbar(frame, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vs.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_tv():
            for i in tv.get_children():
                tv.delete(i)
            for cat, amt in budgets.items():
                tv.insert('', tk.END, values=(cat, f"₹{amt:.2f}"))

        entry_frame = tk.Frame(dlg)
        entry_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        tk.Label(entry_frame, text="Category:").pack(side=tk.LEFT)
        cat_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=cat_var, width=18).pack(side=tk.LEFT, padx=(5,15))
        tk.Label(entry_frame, text="Monthly Budget:").pack(side=tk.LEFT)
        amt_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=amt_var, width=12).pack(side=tk.LEFT, padx=(5,15))

        def save_entry():
            cat = (cat_var.get() or '').strip()
            if not cat:
                messagebox.showerror("Budgets", "Category required.")
                return
            try:
                amt = float(amt_var.get())
            except Exception:
                messagebox.showerror("Budgets", "Enter a valid amount.")
                return
            budgets[cat] = amt
            save_budgets(budgets)
            refresh_tv()

        def remove_selected():
            sel = tv.selection()
            if not sel:
                return
            val = tv.item(sel[0], 'values')
            cat = val[0]
            if cat in budgets:
                del budgets[cat]
                save_budgets(budgets)
                refresh_tv()

        btns = tk.Frame(dlg)
        btns.pack(fill=tk.X, padx=10)
        ttk.Button(btns, text="Save/Update", command=save_entry).pack(side=tk.LEFT)
        ttk.Button(btns, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=10)

        refresh_tv()

    ttk.Button(btns_container, text="Budgets", command=on_manage_budgets).pack(side=tk.RIGHT, padx=(0,10))

    # Summary frame
    summary = tk.Frame(window)
    summary.pack(fill=tk.X)
    total_label = tk.Label(summary, text="Total Expenses: ₹0.00", font=("Arial", 12))
    total_label.pack(side=tk.LEFT, padx=10)
    balance_label = tk.Label(summary, text="Remaining Balance: ₹0.00", font=("Arial", 12))
    balance_label.pack(side=tk.LEFT, padx=10)
    summary2_label = tk.Label(summary, text="", font=("Arial", 11))
    summary2_label.pack(side=tk.LEFT, padx=10)

    # Charts container
    charts = tk.Frame(window)
    charts.pack(fill=tk.BOTH, expand=True)

    # Goals and challenge row
    goals_frame = tk.Frame(window)
    goals_frame.pack(fill=tk.X, padx=10, pady=(0,10))

    # Goal tracker UI
    tk.Label(goals_frame, text="Goal Amount (₹):").pack(side=tk.LEFT)
    goal_amount_var = tk.StringVar()
    goal_target_var = tk.StringVar()
    tk.Entry(goals_frame, textvariable=goal_amount_var, width=10).pack(side=tk.LEFT, padx=(5,15))
    tk.Label(goals_frame, text="Target Date (DD-MM-YYYY):").pack(side=tk.LEFT)
    tk.Entry(goals_frame, textvariable=goal_target_var, width=14).pack(side=tk.LEFT)
    goal_progress = ttk.Progressbar(goals_frame, length=180, mode='determinate')
    goal_progress.pack(side=tk.LEFT, padx=(10,10))
    goal_status = tk.Label(goals_frame, text="")
    goal_status.pack(side=tk.LEFT)

    def on_save_goal():
        try:
            amt = float(goal_amount_var.get())
        except Exception:
            messagebox.showerror("Goal", "Enter a valid amount")
            return
        # Expect target in DD-MM-YYYY
        try:
            from datetime import datetime as _dt
            t_iso = _dt.strptime(goal_target_var.get().strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
        except Exception:
            messagebox.showerror("Goal", "Target date must be DD-MM-YYYY")
            return
        from datetime import datetime as _dt
        start_iso = _dt.now().strftime("%Y-%m-%d")
        save_goal(start_iso, t_iso, amt)
        render()

    ttk.Button(goals_frame, text="Save Goal", command=on_save_goal).pack(side=tk.LEFT, padx=(10,0))

    # Weekly challenge UI
    challenge_frame = tk.Frame(window)
    challenge_frame.pack(fill=tk.X, padx=10, pady=(0,10))
    tk.Label(challenge_frame, text="Weekly Limit:").pack(side=tk.LEFT)
    challenge_limit_var = tk.StringVar()
    tk.Entry(challenge_frame, textvariable=challenge_limit_var, width=10).pack(side=tk.LEFT, padx=(5,10))
    challenge_status = tk.Label(challenge_frame, text="")
    challenge_status.pack(side=tk.LEFT, padx=(10,0))

    def on_save_challenge():
        try:
            lim = float(challenge_limit_var.get())
        except Exception:
            messagebox.showerror("Challenge", "Enter a valid limit")
            return
        # Use current week's Monday as week_start
        from datetime import datetime as _dt
        today_iso = _dt.now().strftime("%Y-%m-%d")
        week_start_iso, _week_end_iso = iso_week_bounds(today_iso)
        save_weekly_challenge(week_start_iso, lim)
        render()

    ttk.Button(challenge_frame, text="Save Weekly Limit", command=on_save_challenge).pack(side=tk.LEFT, padx=(10,0))

    # Insights text
    insights_label = tk.Label(window, text="", font=("Arial", 10))
    insights_label.pack(fill=tk.X, padx=10, pady=(0,10))

    # Assistant UI removed per requirements

    # Table for expenses
    table_frame = tk.Frame(window)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    columns = ("date", "category", "amount", "description")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    for col in columns:
        tree.heading(col, text=col.capitalize())
    tree.column("date", width=100)
    tree.column("category", width=120)
    tree.column("amount", width=100, anchor="e")
    tree.column("description", width=300)
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    # Actions under the table
    actions = tk.Frame(window)
    actions.pack(fill=tk.X, padx=10, pady=(0,10))
    edit_btn = ttk.Button(actions, text="Edit")
    delete_btn = ttk.Button(actions, text="Delete")
    edit_btn.pack(side=tk.LEFT)
    delete_btn.pack(side=tk.LEFT, padx=(10,0))

    # Keep mapping of tree items to CSV indices for edit/delete
    item_to_index = {}

    # Keep reference to the over-budget label so we can replace it
    overbudget_label = None

    def render():
        nonlocal overbudget_label, item_to_index

        # Clear previous charts and any warning label
        for child in charts.winfo_children():
            child.destroy()
        if overbudget_label is not None:
            try:
                overbudget_label.destroy()
            except Exception:
                pass
            overbudget_label = None

        # Data
        start_date = from_var.get().strip()
        end_date = to_var.get().strip()

        # Convert DD-MM-YYYY to YYYY-MM-DD for filtering
        def _to_iso(s):
            if not s:
                return ""
            try:
                from datetime import datetime as _dt
                return _dt.strptime(s, "%d-%m-%Y").strftime("%Y-%m-%d")
            except Exception:
                return ""

        s_iso = _to_iso(start_date)
        e_iso = _to_iso(end_date)
        if s_iso or e_iso:
            expenses = load_expenses_between_with_indices(s_iso, e_iso)
        else:
            expenses = load_expenses_with_indices()

        # Text search removed

        # Compute totals
        total_val = sum_total(expenses)
        balance_val = salary - total_val
        total_label.config(text=f"Total Expenses: ₹{total_val:.2f}")
        balance_label.config(text=f"Remaining Balance: ₹{balance_val:.2f}")

        category_totals = sum_by_category(expenses)
        daily_totals = sum_by_day(expenses)

        # Monthly summary: top category and average daily spend for current filter
        try:
            top_cat = "—"
            if category_totals:
                top_cat = max(category_totals.items(), key=lambda x: x[1])[0]
            avg_daily = 0.0
            if daily_totals:
                avg_daily = sum(daily_totals.values()) / len(daily_totals)
            summary2_label.config(text=f"Top: {top_cat}   Avg/day: ₹{avg_daily:.2f}")
        except Exception:
            summary2_label.config(text="")

        # Goal progress
        try:
            g = load_goal()
            if g and g.get("amount", 0) > 0:
                # Savings = salary - total expenses for period from goal start to today
                from datetime import datetime as _dt
                today_iso = _dt.now().strftime("%Y-%m-%d")
                spent = sum_expenses_between(g["start_date"], today_iso)
                # assume monthly repeating salary until target; for a simple tracker, use current salary only
                saved = max(0.0, salary - spent)
                pct = max(0, min(100, int((saved / g["amount"]) * 100)))
                goal_progress['value'] = pct
                # display target date as DD-MM-YYYY
                try:
                    t_disp = _dt.strptime(g["target_date"], "%Y-%m-%d").strftime("%d-%m-%Y")
                except Exception:
                    t_disp = g["target_date"]
                goal_status.config(text=f"{pct}% toward ₹{g['amount']:.0f} by {t_disp}")
                goal_amount_var.set(f"{g['amount']:.0f}")
                try:
                    t_disp_input = _dt.strptime(g["target_date"], "%Y-%m-%d").strftime("%d-%m-%Y")
                except Exception:
                    t_disp_input = g["target_date"]
                goal_target_var.set(t_disp_input)
            else:
                goal_progress['value'] = 0
                goal_status.config(text="No goal set")
        except Exception:
            goal_progress['value'] = 0
            goal_status.config(text="")

        # Weekly challenge status and insight
        try:
            from datetime import datetime as _dt, timedelta as _td
            today_iso = _dt.now().strftime("%Y-%m-%d")
            week_start_iso, week_end_iso = iso_week_bounds(today_iso)
            ch = load_weekly_challenge()
            this_week_spend = sum_expenses_between(week_start_iso, week_end_iso)
            if ch and ch.get('week_start'):
                status = f"This week: ₹{this_week_spend:.2f} / limit ₹{ch['limit']:.2f}"
            else:
                status = f"This week: ₹{this_week_spend:.2f}"
            challenge_status.config(text=status)
            # Insight: compare this week vs last week
            week_start_dt = _dt.strptime(week_start_iso, "%Y-%m-%d")
            last_week_start = (week_start_dt - _td(days=7)).strftime("%Y-%m-%d")
            last_week_end = (week_start_dt - _td(days=1)).strftime("%Y-%m-%d")
            last_week_spend = sum_expenses_between(last_week_start, last_week_end)
            if last_week_spend > 0:
                change = ((this_week_spend - last_week_spend) / last_week_spend) * 100
                if change >= 0:
                    insights_label.config(text=f"You’ve spent {change:.0f}% more this week than last week.")
                else:
                    insights_label.config(text=f"You’ve spent {abs(change):.0f}% less this week than last week.")
            else:
                insights_label.config(text="")
        except Exception:
            insights_label.config(text="")

        # Over-budget warnings for current filter
        budgets = load_budgets()
        over = []
        for cat, cat_total in category_totals.items():
            if cat in budgets and budgets[cat] > 0 and cat_total > budgets[cat]:
                over.append(f"{cat} (₹{cat_total:.2f} / ₹{budgets[cat]:.2f})")
        if over:
            message = "Over budget: " + ", ".join(over)
            try:
                overbudget_label = tk.Label(window, text=message, fg='red', font=("Arial", 10))
                # pack right below the summary frame
                overbudget_label.pack(after=summary, fill=tk.X, padx=10, pady=(0,5))
            except Exception:
                pass

        # Pie Chart (category) with improved label layout
        try:
            fig1, ax1 = plt.subplots(figsize=(5,4))
            if category_totals:
                labels = list(category_totals.keys())
                sizes = list(category_totals.values())

                def _fmt_autopct(pct):
                    return ("%1.1f%%" % pct) if pct >= 3 else ""  # hide very small slices

                wedges, texts, autotexts = ax1.pie(
                    sizes,
                    labels=None,                 # put labels in legend instead
                    autopct=_fmt_autopct,
                    pctdistance=0.7,            # keep percents closer to center
                    labeldistance=1.1,          # (no labels on wedges)
                    startangle=90,
                    wedgeprops={"linewidth": 1, "edgecolor": "white"},
                )
                ax1.axis('equal')  # equal aspect ratio for a perfect circle
                ax1.legend(wedges, labels, title="Category", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
            else:
                ax1.text(0.5, 0.5, "No expenses yet", ha='center', va='center')
            ax1.set_title("Expenses by Category")
            fig1.tight_layout()
            pie_canvas = FigureCanvasTkAgg(fig1, master=charts)
            pie_canvas.get_tk_widget().pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
            pie_canvas.draw()
            try:
                plt.close(fig1)
            except Exception:
                pass
        except Exception:
            # If plotting fails, still continue
            pass

        # Bar Chart (daily)
        try:
            fig2, ax2 = plt.subplots(figsize=(4,3))
            if daily_totals:
                dates = list(daily_totals.keys())
                values = list(daily_totals.values())
                # Show dates as DD-MM-YYYY on x-axis
                pretty_dates = []
                from datetime import datetime as _dt
                for d in dates:
                    try:
                        pretty_dates.append(_dt.strptime(d, "%Y-%m-%d").strftime("%d-%m-%Y"))
                    except Exception:
                        pretty_dates.append(d)
                ax2.bar(range(len(pretty_dates)), values)
                ax2.set_xticks(range(len(pretty_dates)))
                ax2.set_xticklabels(pretty_dates, rotation=45, ha='right')
            else:
                ax2.text(0.5, 0.5, "No daily data", ha='center', va='center')
            ax2.set_title("Daily Expenses")
            bar_canvas = FigureCanvasTkAgg(fig2, master=charts)
            bar_canvas.get_tk_widget().pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
            bar_canvas.draw()
            try:
                plt.close(fig2)
            except Exception:
                pass
        except Exception:
            pass

        # Populate table
        for i in tree.get_children():
            tree.delete(i)
        item_to_index.clear()
        from datetime import datetime as _dt
        for e in expenses:
            # Display date as DD-MM-YYYY
            _date_display = e.get("date", "")
            try:
                _date_display = _dt.strptime(_date_display, "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                pass
            amount_val = e.get("amount", 0.0)
            try:
                amount_val = float(amount_val)
            except Exception:
                amount_val = 0.0
            iid = tree.insert("", tk.END, values=(
                _date_display,
                e.get("category",""),
                f"₹{amount_val:.2f}",
                e.get("description",""),
            ))
            if "_index" in e:
                item_to_index[iid] = e["_index"]

    def on_edit():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a row to edit.")
            return
        iid = sel[0]
        if iid not in item_to_index:
            messagebox.showerror("Edit", "Unable to resolve selected row.")
            return
        csv_index = item_to_index[iid]
        # Gather values from the row to prefill
        vals = tree.item(iid, "values")
        # vals[0] is displayed DD-MM-YYYY; convert back to ISO
        try:
            from datetime import datetime as _dt
            _iso_date = _dt.strptime(vals[0], "%d-%m-%Y").strftime("%Y-%m-%d")
        except Exception:
            _iso_date = vals[0]
        # Parse amount string like "₹1,234.56"
        try:
            amt_str = vals[2].replace("₹", "").replace(",", "").strip()
            amt_val = float(amt_str)
        except Exception:
            amt_val = 0.0
        initial = {
            "date": _iso_date,
            "category": vals[1],
            "amount": amt_val,
            "description": vals[3],
        }

        def submit_update(data):
            update_expense_at(csv_index, data["date"], data["category"], data["amount"], data["description"])
            render()

        try:
            from ui.expense_entry import expense_window
            expense_window(on_submit=submit_update, initial=initial, master=window)
        except Exception as e:
            messagebox.showerror("Edit", str(e))

    def on_delete():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Delete", "Select a row to delete.")
            return
        iid = sel[0]
        if iid not in item_to_index:
            messagebox.showerror("Delete", "Unable to resolve selected row.")
            return
        csv_index = item_to_index[iid]
        if not messagebox.askyesno("Confirm", "Delete selected expense?"):
            return
        delete_expense_at(csv_index)
        render()

    edit_btn.configure(command=on_edit)
    delete_btn.configure(command=on_delete)

    # Initial render (light theme by default). If no family set, prompt once.
    def maybe_prompt_family():
        fam = load_family()
        if not fam.get("members") and fam.get("shared_budget", 0) <= 0:
            try:
                on_manage_family()
            except Exception:
                pass

    render()
    maybe_prompt_family()

    # Do not start a new mainloop here; caller manages the Tk loop
