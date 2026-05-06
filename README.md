# MoneyTerm

MoneyTerm is a terminal-first personal ledger prototype for Termux-like usage.
It uses only Python standard library modules and stores data in local SQLite.

## Goals

- Fast CLI entry for phone terminals.
- Responsive terminal dashboard that works when the terminal is resized.
- Digital monthly totals, text bar charts, and pie-share style summaries.
- A clean SQLite core that can later power a local app and web app.

## Quick Start

```bash
python money.py demo
python money.py report
python money.py dash
```

Add records:

```bash
python money.py add -120 breakfast -c food -a cash
python money.py add 52000 salary -c salary -a bank
python money.py list --limit 20
```

Amounts use positive numbers for income and negative numbers for expenses.

## Termux

```bash
pkg install python
python money.py demo
python money.py dash
```

The dashboard automatically switches between a compact stacked layout and a
wider two-column layout based on terminal size.

Controls:

- `h` or left arrow: previous month
- `l` or right arrow: next month
- `q`: quit

## Data Location

By default, data is stored at:

```text
~/.local/share/moneyterm/ledger.sqlite3
```

You can override this with:

```bash
MONEY_HOME=/path/to/data python money.py list
```

## Future App Shape

The current CLI can become the shared core for:

- Local desktop app: Tauri, Electron, or a native wrapper.
- Web app: API server reading the same SQLite schema.
- Phone terminal mode: the current CLI/TUI experience in Termux.
