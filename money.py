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


@dataclass
class QuickEntryState:
    amount: str = "-"
    note: str = ""
    category: str = "food"
    account: str = "cash"
    date: str = "today"
    active_field: int = 0
    selected_key: int = 0
    note_index: int = 0
    category_index: int = 0
    message: str = ""


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


def insert_transaction(
    conn: sqlite3.Connection,
    amount: int,
    note: str,
    category: str,
    account: str,
    date_value: str,
) -> None:
    if amount == 0:
        raise ValueError("Amount cannot be 0.")
    account_id = get_or_create_account(conn, account)
    category_id = get_or_create_category(conn, category, amount)
    conn.execute(
        """
        INSERT INTO transactions(tx_date, amount, account_id, category_id, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (parse_date(date_value), amount, account_id, category_id, note or ""),
    )


def add_transaction(args: argparse.Namespace) -> None:
    amount = int(args.amount)
    if amount == 0:
        raise SystemExit("Amount cannot be 0.")
    with connect() as conn:
        init_db(conn)
        insert_transaction(conn, amount, args.note or "", args.category, args.account, args.date)
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


def fetch_recent_notes(conn: sqlite3.Connection, limit: int = 12) -> list[str]:
    rows = conn.execute(
        """
        SELECT note, COUNT(*) AS use_count, MAX(created_at) AS last_used
        FROM transactions
        WHERE TRIM(note) != ''
        GROUP BY note
        ORDER BY last_used DESC, use_count DESC, note ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [str(row["note"]) for row in rows]


def fetch_remembered_categories(conn: sqlite3.Connection, limit: int = 12) -> list[str]:
    rows = conn.execute(
        """
        SELECT c.name, COUNT(t.id) AS use_count, MAX(t.created_at) AS last_used
        FROM categories c
        LEFT JOIN transactions t ON t.category_id = c.id
        GROUP BY c.id, c.name
        ORDER BY use_count DESC, last_used DESC, c.name ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [str(row["name"]) for row in rows]


def fetch_remembered_accounts(conn: sqlite3.Connection, limit: int = 8) -> list[str]:
    rows = conn.execute(
        """
        SELECT a.name, COUNT(t.id) AS use_count, MAX(t.created_at) AS last_used
        FROM accounts a
        LEFT JOIN transactions t ON t.account_id = a.id
        GROUP BY a.id, a.name
        ORDER BY use_count DESC, last_used DESC, a.name ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [str(row["name"]) for row in rows]


def show_memory(args: argparse.Namespace) -> None:
    with connect() as conn:
        init_db(conn)
        if args.kind == "notes":
            values = fetch_recent_notes(conn, args.limit)
        elif args.kind == "categories":
            values = fetch_remembered_categories(conn, args.limit)
        else:
            values = fetch_remembered_accounts(conn, args.limit)
    if not values:
        print(f"No remembered {args.kind} yet.")
        return
    for index, value in enumerate(values, start=1):
        print(f"{index:>2}. {value}")


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


def quick_entry(args: argparse.Namespace) -> None:
    del args
    with connect() as conn:
        init_db(conn)
    if curses is None:
        print("Quick entry mode needs curses. It is available on Linux/Termux terminals.")
        print("Use `python money.py add <amount> <note> -c <category> -a <account>` instead.")
        return
    try:
        curses.wrapper(draw_quick_entry)
    except curses.error:
        print("Your terminal does not support quick entry mode.")


def draw_quick_entry(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    state = QuickEntryState()
    keyboard = [
        ["1", "2", "3", "+"],
        ["4", "5", "6", "-"],
        ["7", "8", "9", "BKSP"],
        ["0", "00", "CLR", "FIELD"],
        ["FOOD", "TRANS", "SHOP", "OTHER"],
        ["NOTE<", "NOTE>", "CAT<", "CAT>"],
        ["SAVE", "QUIT"],
    ]
    flat_keys = [item for row in keyboard for item in row]
    fields = ["amount", "note", "category", "account"]

    while True:
        with connect() as conn:
            init_db(conn)
            notes = fetch_recent_notes(conn, 8)
            categories = fetch_remembered_categories(conn, 8)
            accounts = fetch_remembered_accounts(conn, 6)
        if accounts and state.account == "cash":
            state.account = accounts[0]

        stdscr.erase()
        height, width = stdscr.getmaxyx()
        lines = build_quick_lines(width, height, state, keyboard, notes, categories, accounts)
        for y, line in enumerate(lines[: max(0, height - 1)]):
            try:
                stdscr.addnstr(y, 0, line, max(0, width - 1))
            except curses.error:
                pass
        stdscr.refresh()

        key = stdscr.get_wch()
        if key in (27, "\x1b", "q", "Q"):
            return
        if key in (9, "\t"):
            state.active_field = (state.active_field + 1) % len(fields)
            continue
        if key == curses.KEY_LEFT:
            state.selected_key = max(0, state.selected_key - 1)
            continue
        if key == curses.KEY_RIGHT:
            state.selected_key = min(len(flat_keys) - 1, state.selected_key + 1)
            continue
        if key == curses.KEY_UP:
            state.selected_key = move_virtual_key(keyboard, state.selected_key, -1)
            continue
        if key == curses.KEY_DOWN:
            state.selected_key = move_virtual_key(keyboard, state.selected_key, 1)
            continue
        if key in (10, 13, "\n", "\r", curses.KEY_ENTER):
            result = apply_virtual_key(state, flat_keys[state.selected_key], notes, categories)
            if result == "quit":
                return
            continue
        if key in (curses.KEY_BACKSPACE, 8, 127, "\b", "\x7f"):
            edit_active_field(state, "BKSP")
            continue
        if isinstance(key, str) and key >= " ":
            apply_typed_key(state, key)


def build_quick_lines(
    width: int,
    height: int,
    state: QuickEntryState,
    keyboard: list[list[str]],
    notes: list[str],
    categories: list[str],
    accounts: list[str],
) -> list[str]:
    del height
    fields = [
        ("amount", state.amount),
        ("note", state.note),
        ("category", state.category),
        ("account", state.account),
    ]
    lines = [
        fit("MoneyTerm Quick Entry", width),
        fit("Type normally, or use arrow keys + Enter on the virtual keyboard. q quits.", width),
        "",
    ]
    for index, (label, value) in enumerate(fields):
        marker = ">" if index == state.active_field else " "
        lines.append(fit(f"{marker} {label.upper():8} {value}", width))
    lines.extend(
        [
            "",
            fit(f"Remembered notes: {', '.join(notes[:4]) if notes else '(none yet)'}", width),
            fit(f"Categories: {', '.join(categories[:6]) if categories else '(none yet)'}", width),
            fit(f"Accounts: {', '.join(accounts[:4]) if accounts else '(none yet)'}", width),
            "",
            "Virtual keyboard",
        ]
    )
    selected = 0
    for row in keyboard:
        parts = []
        for label in row:
            token = f"[{label}]" if selected == state.selected_key else f" {label} "
            parts.append(token.center(8))
            selected += 1
        lines.append(fit("".join(parts), width))
    lines.extend(
        [
            "",
            fit("Tab changes field. Backspace edits. SAVE stores the transaction.", width),
            fit(state.message, width),
        ]
    )
    return lines


def move_virtual_key(keyboard: list[list[str]], selected_key: int, row_delta: int) -> int:
    rows: list[tuple[int, int]] = []
    index = 0
    for row_index, row in enumerate(keyboard):
        for col_index, _ in enumerate(row):
            rows.append((row_index, col_index))
            index += 1
    row_index, col_index = rows[selected_key]
    target_row = max(0, min(len(keyboard) - 1, row_index + row_delta))
    target_col = min(col_index, len(keyboard[target_row]) - 1)
    new_index = 0
    for current_row, row in enumerate(keyboard):
        for current_col, _ in enumerate(row):
            if current_row == target_row and current_col == target_col:
                return new_index
            new_index += 1
    return selected_key


def apply_typed_key(state: QuickEntryState, char: str) -> None:
    if state.active_field == 0 and char in ("m", "M"):
        state.active_field = 0
        return
    if state.active_field == 0 and char in ("n", "N"):
        state.active_field = 1
        return
    if state.active_field == 0 and char in ("c", "C"):
        state.active_field = 2
        return
    if state.active_field == 0 and char in ("a", "A"):
        state.active_field = 3
        return
    if state.active_field == 0 and char in ("s", "S"):
        save_quick_entry(state)
        return
    edit_active_field(state, char)


def apply_virtual_key(
    state: QuickEntryState,
    token: str,
    notes: list[str],
    categories: list[str],
) -> str | None:
    if token == "QUIT":
        return "quit"
    if token == "SAVE":
        save_quick_entry(state)
        return None
    if token == "FIELD":
        state.active_field = (state.active_field + 1) % 4
        return None
    if token in ("BKSP", "CLR", "+", "-", "0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
        edit_active_field(state, token)
        return None
    if token == "FOOD":
        state.category = "food"
    elif token == "TRANS":
        state.category = "transport"
    elif token == "SHOP":
        state.category = "shopping"
    elif token == "OTHER":
        state.category = "other"
    elif token == "NOTE<":
        cycle_note(state, notes, -1)
    elif token == "NOTE>":
        cycle_note(state, notes, 1)
    elif token == "CAT<":
        cycle_category(state, categories, -1)
    elif token == "CAT>":
        cycle_category(state, categories, 1)
    return None


def edit_active_field(state: QuickEntryState, token: str) -> None:
    values = [state.amount, state.note, state.category, state.account]
    current = values[state.active_field]
    if token == "BKSP":
        current = current[:-1]
    elif token == "CLR":
        current = "-" if state.active_field == 0 else ""
    elif state.active_field == 0:
        if token in ("+", "-"):
            current = token
        elif token.isdigit():
            current += token
    else:
        current += token
    state.amount, state.note, state.category, state.account = values[0], values[1], values[2], values[3]
    if state.active_field == 0:
        state.amount = current
    elif state.active_field == 1:
        state.note = current
    elif state.active_field == 2:
        state.category = current
    else:
        state.account = current


def cycle_note(state: QuickEntryState, notes: list[str], delta: int) -> None:
    if not notes:
        state.message = "No remembered notes yet."
        return
    state.note_index = (state.note_index + delta) % len(notes)
    state.note = notes[state.note_index]
    state.active_field = 1


def cycle_category(state: QuickEntryState, categories: list[str], delta: int) -> None:
    if not categories:
        state.message = "No remembered categories yet."
        return
    state.category_index = (state.category_index + delta) % len(categories)
    state.category = categories[state.category_index]
    state.active_field = 2


def save_quick_entry(state: QuickEntryState) -> None:
    try:
        amount = int(state.amount)
        if amount == 0:
            raise ValueError
    except ValueError:
        state.message = "Amount must be a non-zero integer."
        return
    if not state.category.strip():
        state.message = "Category is required."
        return
    if not state.account.strip():
        state.message = "Account is required."
        return
    with connect() as conn:
        init_db(conn)
        insert_transaction(
            conn,
            amount,
            state.note.strip(),
            state.category.strip(),
            state.account.strip(),
            state.date,
        )
        conn.commit()
    state.message = f"Saved {format_money(amount)} in {state.category}."
    state.amount = "-"
    state.note = ""


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
              python money.py notes
              python money.py quick
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

    notes = sub.add_parser("notes", help="Show remembered notes")
    notes.add_argument("--limit", type=int, default=12)
    notes.set_defaults(func=show_memory, kind="notes")

    categories = sub.add_parser("categories", help="Show remembered categories")
    categories.add_argument("--limit", type=int, default=12)
    categories.set_defaults(func=show_memory, kind="categories")

    accounts = sub.add_parser("accounts", help="Show remembered accounts")
    accounts.add_argument("--limit", type=int, default=8)
    accounts.set_defaults(func=show_memory, kind="accounts")

    rep = sub.add_parser("report", help="Show a monthly report with charts")
    rep.add_argument("-m", "--month", default=None, help="YYYY-MM")
    rep.set_defaults(func=report)

    dash = sub.add_parser("dash", help="Open responsive terminal dashboard")
    dash.set_defaults(func=dashboard)

    quick = sub.add_parser("quick", help="Open quick entry with remembered values and virtual keyboard")
    quick.set_defaults(func=quick_entry)

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
