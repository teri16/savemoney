#!/usr/bin/env python3
"""A small terminal-first personal ledger.

The app intentionally uses only the Python standard library so it can run in
Termux or a minimal Linux terminal without a package manager step.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
import textwrap
from dataclasses import dataclass
from pathlib import Path

try:
    import curses
except ImportError:  # Windows often lacks curses; CLI/report still work there.
    curses = None


APP_DIR = Path(os.environ.get("MONEY_HOME", Path.home() / ".local" / "share" / "moneyterm"))
DB_PATH = APP_DIR / "ledger.sqlite3"


@dataclass(frozen=True)
class Summary:
    income: int
    expense: int
    balance: int


def connect() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'cash'
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL CHECK (kind IN ('income', 'expense', 'transfer'))
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_date TEXT NOT NULL,
            amount INTEGER NOT NULL,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            category_id INTEGER NOT NULL REFERENCES categories(id),
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    ensure_seed_data(conn)
    conn.commit()


def ensure_seed_data(conn: sqlite3.Connection) -> None:
    accounts = [("cash", "cash"), ("bank", "bank"), ("card", "credit")]
    categories = [
        ("salary", "income"),
        ("food", "expense"),
        ("transport", "expense"),
        ("shopping", "expense"),
        ("housing", "expense"),
        ("other", "expense"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO accounts(name, type) VALUES (?, ?)",
        accounts,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO categories(name, kind) VALUES (?, ?)",
        categories,
    )


def parse_date(value: str | None) -> str:
    if value in (None, "today"):
        return dt.date.today().isoformat()
    if value == "yesterday":
        return (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return dt.date.fromisoformat(value).isoformat()


def get_or_create_account(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM accounts WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cur = conn.execute("INSERT INTO accounts(name, type) VALUES (?, 'cash')", (name,))
    return int(cur.lastrowid)


def get_or_create_category(conn: sqlite3.Connection, name: str, amount: int) -> int:
    row = conn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    kind = "income" if amount > 0 else "expense"
    cur = conn.execute("INSERT INTO categories(name, kind) VALUES (?, ?)", (name, kind))
    return int(cur.lastrowid)


def add_transaction(args: argparse.Namespace) -> None:
    amount = int(args.amount)
    if amount == 0:
        raise SystemExit("Amount cannot be 0.")
    with connect() as conn:
        init_db(conn)
        account_id = get_or_create_account(conn, args.account)
        category_id = get_or_create_category(conn, args.category, amount)
        conn.execute(
            """
            INSERT INTO transactions(tx_date, amount, account_id, category_id, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (parse_date(args.date), amount, account_id, category_id, args.note or ""),
        )
        conn.commit()
    print(f"Added {format_money(amount)} in {args.category} via {args.account}.")


def list_transactions(args: argparse.Namespace) -> None:
    with connect() as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT t.id, t.tx_date, t.amount, a.name AS account, c.name AS category, t.note
            FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            JOIN categories c ON c.id = t.category_id
            WHERE (? IS NULL OR t.tx_date >= ?)
              AND (? IS NULL OR t.tx_date <= ?)
            ORDER BY t.tx_date DESC, t.id DESC
            LIMIT ?
            """,
            (args.from_date, args.from_date, args.to_date, args.to_date, args.limit),
        ).fetchall()
    if not rows:
        print("No transactions yet.")
        return
    widths = [4, 10, 12, 12, 14]
    print(f"{'ID':>{widths[0]}}  {'DATE':{widths[1]}}  {'AMOUNT':>{widths[2]}}  {'ACCOUNT':{widths[3]}}  {'CATEGORY':{widths[4]}}  NOTE")
    for row in rows:
        print(
            f"{row['id']:>{widths[0]}}  "
            f"{row['tx_date']:{widths[1]}}  "
            f"{format_money(row['amount']):>{widths[2]}}  "
            f"{row['account']:{widths[3]}.{widths[3]}}  "
            f"{row['category']:{widths[4]}.{widths[4]}}  "
            f"{row['note']}"
        )


def month_range(month: str | None) -> tuple[str, str]:
    if month is None:
        today = dt.date.today()
        start = today.replace(day=1)
    else:
        start = dt.date.fromisoformat(f"{month}-01")
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start.isoformat(), (end - dt.timedelta(days=1)).isoformat()


def fetch_summary(conn: sqlite3.Connection, start: str, end: str) -> Summary:
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END), 0) AS expense
        FROM transactions
        WHERE tx_date BETWEEN ? AND ?
        """,
        (start, end),
    ).fetchone()
    income = int(row["income"])
    expense = int(row["expense"])
    return Summary(income=income, expense=expense, balance=income - expense)


def fetch_category_totals(conn: sqlite3.Connection, start: str, end: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT c.name AS category, SUM(-t.amount) AS total
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        WHERE t.amount < 0 AND t.tx_date BETWEEN ? AND ?
        GROUP BY c.name
        ORDER BY total DESC
        """,
        (start, end),
    ).fetchall()


def report(args: argparse.Namespace) -> None:
    start, end = month_range(args.month)
    with connect() as conn:
        init_db(conn)
        summary = fetch_summary(conn, start, end)
        rows = fetch_category_totals(conn, start, end)
    print(f"Report {start} to {end}")
    print(f"Income : {format_money(summary.income)}")
    print(f"Expense: {format_money(-summary.expense)}")
    print(f"Balance: {format_money(summary.balance)}")
    print()
    print(render_bars([(row["category"], int(row["total"])) for row in rows], width=36))
    print()
    print(render_pie_table([(row["category"], int(row["total"])) for row in rows], width=36))


def dashboard(args: argparse.Namespace) -> None:
    del args
    with connect() as conn:
        init_db(conn)
    if curses is None:
        print("Dashboard mode needs curses. It is available on Linux/Termux terminals.")
        print("Use `python money.py report` for the non-interactive chart view.")
        return
    try:
        curses.wrapper(draw_dashboard)
    except curses.error:
        print("Your terminal does not support this dashboard mode. Try `python money.py report`.")


def draw_dashboard(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    selected_month = dt.date.today().strftime("%Y-%m")
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        start, end = month_range(selected_month)
        with connect() as conn:
            init_db(conn)
            summary = fetch_summary(conn, start, end)
            category_totals = [(row["category"], int(row["total"])) for row in fetch_category_totals(conn, start, end)]
        lines = build_dashboard_lines(width, height, selected_month, start, end, summary, category_totals)
        for y, line in enumerate(lines[: max(0, height - 1)]):
            try:
                stdscr.addnstr(y, 0, line, max(0, width - 1))
            except curses.error:
                pass
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("q"), ord("Q"), 27):
            return
        if key == curses.KEY_RESIZE:
            continue
        if key in (ord("h"), curses.KEY_LEFT):
            selected_month = shift_month(selected_month, -1)
        if key in (ord("l"), curses.KEY_RIGHT):
            selected_month = shift_month(selected_month, 1)
        curses.napms(120)


def build_dashboard_lines(
    width: int,
    height: int,
    selected_month: str,
    start: str,
    end: str,
    summary: Summary,
    category_totals: list[tuple[str, int]],
) -> list[str]:
    compact = width < 72 or height < 24
    chart_width = max(12, min(52, width - 22))
    lines = [
        fit(f"MoneyTerm  {selected_month}  ({start}..{end})", width),
        fit("h/left prev  l/right next  q quit", width),
        "",
        fit(f"INCOME  {format_money(summary.income)}", width),
        fit(f"EXPENSE {format_money(-summary.expense)}", width),
        fit(f"BALANCE {format_money(summary.balance)}", width),
        "",
    ]
    if compact:
        lines.append("BAR")
        lines.extend(render_bars(category_totals, chart_width).splitlines())
        lines.append("")
        lines.append("PIE")
        lines.extend(render_pie_table(category_totals, chart_width).splitlines())
        return [fit(line, width) for line in lines]

    bars = render_bars(category_totals, chart_width).splitlines()
    pie = render_pie_table(category_totals, max(18, width - chart_width - 8)).splitlines()
    lines.append("EXPENSE BAR".ljust(chart_width + 4) + "PIE SHARE")
    for i in range(max(len(bars), len(pie))):
        left = bars[i] if i < len(bars) else ""
        right = pie[i] if i < len(pie) else ""
        lines.append(left.ljust(chart_width + 4) + right)
    return [fit(line, width) for line in lines]


def shift_month(month: str, delta: int) -> str:
    year, mon = [int(part) for part in month.split("-")]
    mon += delta
    while mon < 1:
        year -= 1
        mon += 12
    while mon > 12:
        year += 1
        mon -= 12
    return f"{year:04d}-{mon:02d}"


def render_bars(rows: list[tuple[str, int]], width: int) -> str:
    if not rows:
        return "No expense data."
    max_value = max(value for _, value in rows) or 1
    label_width = min(14, max(6, width // 4))
    bar_width = max(6, width - label_width - 14)
    lines = []
    for label, value in rows:
        filled = max(1, round((value / max_value) * bar_width))
        bar = "#" * filled + "." * (bar_width - filled)
        lines.append(f"{label[:label_width]:{label_width}} |{bar}| {format_money(-value)}")
    return "\n".join(lines)


def render_pie_table(rows: list[tuple[str, int]], width: int) -> str:
    if not rows:
        return "No expense data."
    total = sum(value for _, value in rows) or 1
    label_width = min(14, max(6, width // 3))
    lines = []
    for label, value in rows:
        percent = value / total
        slices = max(1, round(percent * 20))
        ring = "o" * slices + "." * (20 - slices)
        lines.append(f"{label[:label_width]:{label_width}} {percent:6.1%} {ring}")
    return "\n".join(lines)


def format_money(amount: int) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,}"


def fit(text: str, width: int) -> str:
    if width <= 1:
        return ""
    return text[: max(0, width - 1)]


def seed_demo(args: argparse.Namespace) -> None:
    del args
    today = dt.date.today()
    month_start = today.replace(day=1)
    demo_rows = [
        (month_start.isoformat(), 52000, "bank", "salary", "monthly salary"),
        ((month_start + dt.timedelta(days=1)).isoformat(), -120, "cash", "food", "breakfast"),
        ((month_start + dt.timedelta(days=2)).isoformat(), -950, "card", "shopping", "daily goods"),
        ((month_start + dt.timedelta(days=4)).isoformat(), -1280, "bank", "transport", "monthly pass"),
        ((month_start + dt.timedelta(days=6)).isoformat(), -13800, "bank", "housing", "rent"),
        ((month_start + dt.timedelta(days=8)).isoformat(), -680, "cash", "food", "dinner"),
    ]
    with connect() as conn:
        init_db(conn)
        for date_value, amount, account, category, note in demo_rows:
            account_id = get_or_create_account(conn, account)
            category_id = get_or_create_category(conn, category, amount)
            conn.execute(
                """
                INSERT INTO transactions(tx_date, amount, account_id, category_id, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (date_value, amount, account_id, category_id, note),
            )
        conn.commit()
    print("Demo data added.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="money",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Terminal-first personal ledger for Termux-like workflows.",
        epilog=textwrap.dedent(
            """
            Examples:
              python money.py add -120 breakfast -c food -a cash
              python money.py add 52000 salary -c salary -a bank
              python money.py list --limit 20
              python money.py report
              python money.py dash
            """
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add one transaction")
    add.add_argument("amount", help="Positive for income, negative for expense")
    add.add_argument("note", nargs="?", default="", help="Short note")
    add.add_argument("-c", "--category", default="other")
    add.add_argument("-a", "--account", default="cash")
    add.add_argument("-d", "--date", default="today", help="YYYY-MM-DD, today, or yesterday")
    add.set_defaults(func=add_transaction)

    list_cmd = sub.add_parser("list", help="List recent transactions")
    list_cmd.add_argument("--from", dest="from_date", default=None)
    list_cmd.add_argument("--to", dest="to_date", default=None)
    list_cmd.add_argument("--limit", type=int, default=30)
    list_cmd.set_defaults(func=list_transactions)

    rep = sub.add_parser("report", help="Show a monthly report with charts")
    rep.add_argument("-m", "--month", default=None, help="YYYY-MM")
    rep.set_defaults(func=report)

    dash = sub.add_parser("dash", help="Open responsive terminal dashboard")
    dash.set_defaults(func=dashboard)

    demo = sub.add_parser("demo", help="Insert sample data")
    demo.set_defaults(func=seed_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
