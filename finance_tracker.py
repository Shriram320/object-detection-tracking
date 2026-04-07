#!/usr/bin/env python3
"""Simple full-time finance tracker CLI.

Features:
- Add income or expense entries
- Set monthly budget targets by category
- Show month summary with category-level spending/budget status
- Persist data in SQLite
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

DB_PATH = Path("finance_tracker.db")


@dataclass
class Entry:
    kind: str
    category: str
    amount: float
    entry_date: str
    note: str


class FinanceTracker:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._setup()

    def _setup(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT CHECK(kind IN ('income', 'expense')) NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                entry_date TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                UNIQUE(category, month)
            )
            """
        )
        self.conn.commit()

    def add_entry(self, entry: Entry) -> None:
        self.conn.execute(
            "INSERT INTO entries (kind, category, amount, entry_date, note) VALUES (?, ?, ?, ?, ?)",
            (entry.kind, entry.category.lower(), entry.amount, entry.entry_date, entry.note),
        )
        self.conn.commit()

    def set_budget(self, category: str, month: str, amount: float) -> None:
        self.conn.execute(
            """
            INSERT INTO budgets (category, month, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(category, month) DO UPDATE SET amount=excluded.amount
            """,
            (category.lower(), month, amount),
        )
        self.conn.commit()

    def month_summary(self, month: str) -> dict:
        cur = self.conn.cursor()
        income = cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM entries WHERE kind='income' AND substr(entry_date,1,7)=?",
            (month,),
        ).fetchone()[0]
        expense = cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM entries WHERE kind='expense' AND substr(entry_date,1,7)=?",
            (month,),
        ).fetchone()[0]
        categories = cur.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0)
            FROM entries
            WHERE kind='expense' AND substr(entry_date,1,7)=?
            GROUP BY category
            ORDER BY 2 DESC
            """,
            (month,),
        ).fetchall()
        budgets = {
            cat: amt
            for cat, amt in cur.execute(
                "SELECT category, amount FROM budgets WHERE month=?", (month,)
            ).fetchall()
        }
        return {
            "month": month,
            "income": income,
            "expense": expense,
            "net": income - expense,
            "categories": categories,
            "budgets": budgets,
        }

    def close(self) -> None:
        self.conn.close()


def parse_month(text: str) -> str:
    if len(text) != 7 or text[4] != "-":
        raise argparse.ArgumentTypeError("Month must be in YYYY-MM format")
    year, month = text.split("-")
    if not (year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
        raise argparse.ArgumentTypeError("Month must be in YYYY-MM format")
    return text


def parse_date(text: str) -> str:
    try:
        date.fromisoformat(text)
    except ValueError as err:
        raise argparse.ArgumentTypeError("Date must be in YYYY-MM-DD format") from err
    return text


def print_summary(summary: dict) -> None:
    print(f"Month: {summary['month']}")
    print(f"Income:  ${summary['income']:.2f}")
    print(f"Expense: ${summary['expense']:.2f}")
    print(f"Net:     ${summary['net']:.2f}")
    print("\nExpenses by category:")
    if not summary["categories"]:
        print("  (none)")
        return

    for category, spent in summary["categories"]:
        budget = summary["budgets"].get(category)
        if budget is None:
            print(f"  - {category}: ${spent:.2f}")
        else:
            delta = budget - spent
            status = "under" if delta >= 0 else "over"
            print(
                f"  - {category}: ${spent:.2f} / ${budget:.2f} "
                f"({abs(delta):.2f} {status} budget)"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Full-time finance tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add an income or expense entry")
    add_parser.add_argument("kind", choices=["income", "expense"])
    add_parser.add_argument("category")
    add_parser.add_argument("amount", type=float)
    add_parser.add_argument("--date", dest="entry_date", type=parse_date, default=date.today().isoformat())
    add_parser.add_argument("--note", default="")

    budget_parser = subparsers.add_parser("budget", help="Set monthly budget by category")
    budget_parser.add_argument("category")
    budget_parser.add_argument("month", type=parse_month)
    budget_parser.add_argument("amount", type=float)

    summary_parser = subparsers.add_parser("summary", help="Show a monthly summary")
    summary_parser.add_argument("month", type=parse_month)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    tracker = FinanceTracker()
    try:
        if args.command == "add":
            tracker.add_entry(
                Entry(
                    kind=args.kind,
                    category=args.category,
                    amount=args.amount,
                    entry_date=args.entry_date,
                    note=args.note,
                )
            )
            print("Entry added.")
            return 0

        if args.command == "budget":
            tracker.set_budget(args.category, args.month, args.amount)
            print("Budget saved.")
            return 0

        if args.command == "summary":
            print_summary(tracker.month_summary(args.month))
            return 0

        parser.print_help()
        return 1
    finally:
        tracker.close()


if __name__ == "__main__":
    raise SystemExit(main())
