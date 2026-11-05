import csv
import os
from datetime import datetime, date

FIELDS = ["date", "type", "category", "amount", "comment"]

def load_expenses(path):
    if not os.path.exists(path):
        return []
    expenses = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("В файле нет нужных колонок.")
        for row in reader:
            try:
                expenses.append({
                    "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    "type": row.get("type", "expense"), # доход (income) или расход (expense)
                    "category": row["category"].strip(),
                    "amount": float(row["amount"]),
                    "comment": row.get("comment", "").strip(),
                })
            except (ValueError, KeyError):
                continue
    return expenses

def save_expenses(expenses, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for e in expenses:
            writer.writerow({
                "date": e["date"].strftime("%Y-%m-%d"),
                "type": e["type"],
                "category": e["category"],
                "amount": f"{e['amount']:.2f}",
                "comment": e["comment"],
            })

def filter_by_period(expenses, period):
    if period == "all":
        return expenses
    today = date.today()
    return [e for e in expenses if e["date"].year == today.year and e["date"].month == today.month]

def compute_stats(expenses):
    if not expenses:
        return {
            "income": 0, "expense": 0, "balance": 0, 
            "count": 0, "avg": 0, "max": 0, "by_category": {}, "forecast": 0
        }
    
    income = sum(e["amount"] for e in expenses if e.get("type") == "income")
    expense_list = [e for e in expenses if e.get("type") != "income"]
    expense = sum(e["amount"] for e in expense_list)
    
    by_cat = {}
    for e in expense_list:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
        
    today = date.today()
    current_expenses = [e for e in expense_list if e["date"].year == today.year and e["date"].month == today.month]
    
    # Прогноз: если это текущий месяц, считаем средний расход в день и умножаем на кол-во дней в месяце
    forecast = 0
    if current_expenses:
        days_passed = max(today.day, 1)
        daily_avg = sum(e["amount"] for e in current_expenses) / days_passed
        import calendar
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        forecast = daily_avg * days_in_month
        
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "count": len(expenses),
        "avg": expense / len(expense_list) if expense_list else 0,
        "max": max((e["amount"] for e in expense_list), default=0),
        "by_category": by_cat,
        "forecast": forecast
    }