import csv
import os
import json
from datetime import datetime

# Resolve data path relative to project root (one level up from utils)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "expenses.csv")
BUDGETS_FILE = os.path.join(DATA_DIR, "budgets.csv")
GOAL_FILE = os.path.join(DATA_DIR, "goal.csv")  # columns: start_date,target_date,amount
CHALLENGE_FILE = os.path.join(DATA_DIR, "weekly_challenge.csv")  # columns: week_start,limit
FAMILY_FILE = os.path.join(DATA_DIR, "family.json")  # {"shared_budget": number, "members":[{"name":"Dad","role":"Admin"}]}

# Ensure data folder and file exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
EXPECTED_EXPENSES_HEADER = ["date", "category", "amount", "description"]

def _ensure_expenses_file_with_header():
    """Ensure expenses.csv exists and has the correct header.
    If the file exists but the first row is not the expected header, prepend it.
    """
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(EXPECTED_EXPENSES_HEADER)
        return

    # File exists; verify header
    try:
        with open(DATA_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            # empty file → write header
            with open(DATA_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(EXPECTED_EXPENSES_HEADER)
            return
        first = rows[0]
        if [c.strip() for c in first] != EXPECTED_EXPENSES_HEADER:
            # Prepend header, keep existing rows as data
            with open(DATA_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(EXPECTED_EXPENSES_HEADER)
                writer.writerows(rows)
    except Exception:
        # On any error, do not modify file contents silently
        pass

_ensure_expenses_file_with_header()
if not os.path.exists(BUDGETS_FILE):
    with open(BUDGETS_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["category", "monthly_budget"])  # amounts in same currency as expenses

# Initialize goal/challenge files if absent
if not os.path.exists(GOAL_FILE):
    with open(GOAL_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["start_date", "target_date", "amount"])  # empty means none
if not os.path.exists(CHALLENGE_FILE):
    with open(CHALLENGE_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["week_start", "limit"])  # ISO week start Monday
if not os.path.exists(FAMILY_FILE):
    with open(FAMILY_FILE, "w", encoding="utf-8") as f:
        json.dump({"shared_budget": 0.0, "members": []}, f)

def add_expense(date, category, amount, description):
    _ensure_expenses_file_with_header()
    with open(DATA_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date, category, amount, description])

def load_expenses():
    expenses = []
    if not os.path.exists(DATA_FILE):
        return expenses
    with open(DATA_FILE, "r", newline="") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        for row in reader:
            # Trim whitespace from all fields
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            # Skip malformed rows
            if not row.get("date") or not row.get("category") or not row.get("amount"):
                continue
            try:
                row["amount"] = float(str(row["amount"]).strip())
            except (TypeError, ValueError):
                continue
            # Normalize parseable fields
            try:
                dt = datetime.strptime(row["date"], "%Y-%m-%d")
                row["_dt"] = dt
                row["_month"] = dt.strftime("%Y-%m")
            except Exception:
                # Skip rows with invalid date format
                continue
            expenses.append(row)
    return expenses

def load_expenses_with_indices():
    """Load expenses and include original CSV row index as _index (0-based, excluding header)."""
    indexed = []
    if not os.path.exists(DATA_FILE):
        return indexed
    with open(DATA_FILE, "r", newline="") as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        for idx, row in enumerate(reader):
            # Trim whitespace from all fields
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            if not row.get("date") or not row.get("category") or not row.get("amount"):
                continue
            try:
                row["amount"] = float(str(row["amount"]).strip())
            except (TypeError, ValueError):
                continue
            try:
                dt = datetime.strptime(row["date"], "%Y-%m-%d")
                row["_dt"] = dt
                row["_month"] = dt.strftime("%Y-%m")
            except Exception:
                continue
            row["_index"] = idx
            indexed.append(row)
    return indexed

def calculate_total_expenses():
    expenses = load_expenses()
    total = sum(item["amount"] for item in expenses)
    return total

def load_expenses_for_month(month_yyyy_mm):
    """Return expenses filtered by month string like '2025-10'. Pass None or '' for all."""
    expenses = load_expenses()
    if not month_yyyy_mm:
        return expenses
    return [e for e in expenses if e.get("_month") == month_yyyy_mm]

def list_available_months():
    """Return sorted list of months (YYYY-MM) present in the data, descending."""
    expenses = load_expenses()
    months = sorted({e.get("_month") for e in expenses if e.get("_month")}, reverse=True)
    return months

def sum_total(expenses):
    return sum(e.get("amount", 0.0) for e in expenses)

def sum_by_category(expenses):
    totals = {}
    for e in expenses:
        cat = e.get("category") or "Unknown"
        totals[cat] = totals.get(cat, 0.0) + e.get("amount", 0.0)
    return totals

def sum_by_day(expenses):
    totals = {}
    for e in expenses:
        d = e.get("date")
        if not d:
            continue
        totals[d] = totals.get(d, 0.0) + e.get("amount", 0.0)
    return totals

def load_expenses_between(start_date_str, end_date_str):
    """Filter expenses between inclusive start and end dates in format YYYY-MM-DD.
    Empty None/"" means unbounded on that side.
    """
    expenses = load_expenses()
    if not start_date_str and not end_date_str:
        return expenses
    start_dt = None
    end_dt = None
    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_dt = None
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        except Exception:
            end_dt = None
    filtered = []
    for e in expenses:
        dt = e.get("_dt")
        if dt is None:
            continue
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue
        filtered.append(e)
    return filtered

def load_expenses_between_with_indices(start_date_str, end_date_str):
    rows = load_expenses_with_indices()
    if not start_date_str and not end_date_str:
        return rows
    start_dt = None
    end_dt = None
    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        except Exception:
            start_dt = None
    if end_date_str:
        try:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        except Exception:
            end_dt = None
    filtered = []
    for e in rows:
        dt = e.get("_dt")
        if dt is None:
            continue
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue
        filtered.append(e)
    return filtered

def export_expenses_to_csv(expenses, target_path):
    """Export given expense rows to a CSV with standard headers."""
    fieldnames = ["date", "category", "amount", "description"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in expenses:
            writer.writerow({
                "date": e.get("date", ""),
                "category": e.get("category", ""),
                "amount": e.get("amount", 0.0),
                "description": e.get("description", ""),
            })

def update_expense_at(index, date, category, amount, description):
    """Update the CSV row at given 0-based index (excluding header)."""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError("Data file not found")
    # Read all rows including header
    with open(DATA_FILE, "r", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        raise IndexError("Empty CSV")
    header = rows[0]
    target = index + 1
    if target < 1 or target >= len(rows):
        raise IndexError("Row index out of range")
    # Reconstruct row in header order if possible
    col_map = {name: i for i, name in enumerate(header)}
    new_row = [""] * len(header)
    def set_col(name, value):
        if name in col_map:
            new_row[col_map[name]] = value
    set_col("date", date)
    set_col("category", category)
    set_col("amount", str(amount))
    set_col("description", description)
    rows[target] = new_row
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def delete_expense_at(index):
    """Delete the CSV row at given 0-based index (excluding header)."""
    if not os.path.exists(DATA_FILE):
        return
    with open(DATA_FILE, "r", newline="") as f:
        rows = list(csv.reader(f))
    target = index + 1
    if target < 1 or target >= len(rows):
        return
    del rows[target]
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# Budgets helpers
def load_budgets():
    budgets = {}
    if not os.path.exists(BUDGETS_FILE):
        return budgets
    with open(BUDGETS_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                amt = float(row.get("monthly_budget", 0) or 0)
            except (TypeError, ValueError):
                amt = 0.0
            cat = row.get("category") or ""
            if cat:
                budgets[cat] = amt
    return budgets

def save_budgets(budgets_dict):
    with open(BUDGETS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "monthly_budget"])
        writer.writeheader()
        for cat, amt in budgets_dict.items():
            writer.writerow({"category": cat, "monthly_budget": amt})

# Goals and weekly challenge helpers
def save_goal(start_date_iso, target_date_iso, amount):
    with open(GOAL_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["start_date", "target_date", "amount"])
        w.writerow([start_date_iso, target_date_iso, str(amount)])

def load_goal():
    if not os.path.exists(GOAL_FILE):
        return None
    with open(GOAL_FILE, "r", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return None
    try:
        amt = float(rows[1][2])
    except Exception:
        amt = 0.0
    return {"start_date": rows[1][0], "target_date": rows[1][1], "amount": amt}

def save_weekly_challenge(week_start_iso, limit_amount):
    with open(CHALLENGE_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week_start", "limit"])
        w.writerow([week_start_iso, str(limit_amount)])

def load_weekly_challenge():
    if not os.path.exists(CHALLENGE_FILE):
        return None
    with open(CHALLENGE_FILE, "r", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return None
    try:
        lim = float(rows[1][1])
    except Exception:
        lim = 0.0
    return {"week_start": rows[1][0], "limit": lim}

def iso_week_bounds(date_iso):
    dt = datetime.strptime(date_iso, "%Y-%m-%d")
    # Monday as week start
    week_start = dt
    while week_start.weekday() != 0:
        from datetime import timedelta
        week_start = week_start - timedelta(days=1)
    from datetime import timedelta
    week_end = week_start + timedelta(days=6)
    return week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")

def load_expenses_between_dates_iso(start_iso, end_iso):
    return load_expenses_between(start_iso, end_iso)

def sum_expenses_between(start_iso, end_iso):
    return sum_total(load_expenses_between(start_iso, end_iso))

def sum_expenses_by_category_between(start_iso, end_iso, category):
    rows = load_expenses_between(start_iso, end_iso)
    total = 0.0
    for r in rows:
        if (r.get("category") or "").lower() == (category or "").lower():
            total += r.get("amount", 0.0)
    return total

# Family storage helpers
def load_family():
    try:
        with open(FAMILY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalize
        shared_budget = float(data.get("shared_budget", 0) or 0)
        members = data.get("members", []) or []
        norm_members = []
        for m in members:
            name = (m.get("name") or "").strip()
            role = (m.get("role") or "Member").strip()
            if name:
                norm_members.append({"name": name, "role": role})
        return {"shared_budget": shared_budget, "members": norm_members}
    except Exception:
        return {"shared_budget": 0.0, "members": []}

def save_family(shared_budget, members_list):
    try:
        data = {"shared_budget": float(shared_budget or 0), "members": members_list or []}
        with open(FAMILY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
