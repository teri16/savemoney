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

## Usage Guide

Basic accounting command syntax is documented on a standalone GitHub page:

[Accounting Commands Guide](docs/accounting-commands.md)

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

## 同步更新操作手冊

本專案已連接到 GitHub repository:

```text
https://github.com/teri16/savemoney
```

### 查看目前狀態

```bash
git status
```

如果看到 `working tree clean`，代表本機檔案目前沒有未提交的修改。

### 將本機修改同步到 GitHub

1. 查看修改內容：

```bash
git status
git diff
```

2. 加入要提交的檔案：

```bash
git add README.md money.py
```

或加入全部修改：

```bash
git add .
```

3. 建立 commit：

```bash
git commit -m "Update project documentation"
```

4. 推送到 GitHub：

```bash
git push
```

### 從 GitHub 更新到本機

在開始修改前，建議先拉取遠端更新：

```bash
git pull
```

如果有其他裝置也在修改同一個專案，這一步可以讓本機保持最新。

### 第一次在新裝置下載專案

```bash
git clone https://github.com/teri16/savemoney.git
cd savemoney
```

### 常見狀況

如果 `git push` 要求登入 GitHub，請依照 Git 提示完成登入或輸入 token。

如果 `git pull` 出現 conflict，代表本機和 GitHub 上同一段內容都被修改過，需要手動整理衝突後再 commit。

如果只想確認遠端位置：

```bash
git remote -v
```

目前應該會看到：

```text
origin  https://github.com/teri16/savemoney.git
```

## Sync And Update Manual

This project is connected to the GitHub repository:

```text
https://github.com/teri16/savemoney
```

### Check Current Status

```bash
git status
```

If you see `working tree clean`, your local files have no uncommitted changes.

### Sync Local Changes To GitHub

1. Review local changes:

```bash
git status
git diff
```

2. Stage the files you want to commit:

```bash
git add README.md money.py
```

Or stage all changes:

```bash
git add .
```

3. Create a commit:

```bash
git commit -m "Update project documentation"
```

4. Push to GitHub:

```bash
git push
```

### Update Local Files From GitHub

Before editing, it is a good habit to pull the latest remote changes:

```bash
git pull
```

This keeps your local project up to date when the same repository is edited on
another device.

### Download The Project On A New Device

```bash
git clone https://github.com/teri16/savemoney.git
cd savemoney
```

### Common Cases

If `git push` asks you to sign in to GitHub, follow the Git prompt or provide a
GitHub token.

If `git pull` shows a conflict, both your local copy and GitHub changed the same
part of a file. Resolve the conflict manually, then commit the fixed file.

To check the remote repository URL:

```bash
git remote -v
```

You should see:

```text
origin  https://github.com/teri16/savemoney.git
```
