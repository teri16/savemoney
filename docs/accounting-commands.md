# Accounting Commands Guide

This page explains the basic MoneyTerm accounting commands.

中文版在下方同一頁面。

## English

### Command Format

```bash
python money.py <command> [options]
```

Available commands:

- `add`: add one income or expense transaction
- `list`: show recent transactions
- `report`: show a monthly report with charts
- `dash`: open the terminal dashboard
- `demo`: insert sample data for testing

### Add An Expense

Use a negative amount for expenses.

```bash
python money.py add -120 breakfast -c food -a cash
```

Meaning:

- `-120`: spent 120
- `breakfast`: note
- `-c food`: category is food
- `-a cash`: account is cash

More examples:

```bash
python money.py add -80 lunch -c food -a cash
python money.py add -45 bus -c transport -a cash
python money.py add -950 groceries -c shopping -a card
```

### Add Income

Use a positive amount for income.

```bash
python money.py add 52000 salary -c salary -a bank
```

Meaning:

- `52000`: received 52,000
- `salary`: note
- `-c salary`: category is salary
- `-a bank`: account is bank

### Add A Transaction With Date

Use `-d` or `--date`.

```bash
python money.py add -120 breakfast -c food -a cash -d 2026-05-06
```

Supported date values:

- `today`
- `yesterday`
- `YYYY-MM-DD`, for example `2026-05-06`

### List Transactions

Show recent transactions:

```bash
python money.py list
```

Limit the number of rows:

```bash
python money.py list --limit 20
```

Filter by date range:

```bash
python money.py list --from 2026-05-01 --to 2026-05-31
```

### Monthly Report

Show this month's report:

```bash
python money.py report
```

Show a specific month:

```bash
python money.py report -m 2026-05
```

The report includes:

- income total
- expense total
- balance
- text bar chart
- pie-share style summary

### Terminal Dashboard

Open the responsive terminal dashboard:

```bash
python money.py dash
```

Controls:

- `h` or left arrow: previous month
- `l` or right arrow: next month
- `q`: quit

The dashboard changes layout when the terminal is resized. It is designed for
Termux-style phone terminal usage.

### Demo Data

Insert sample data:

```bash
python money.py demo
```

Then view the report:

```bash
python money.py report
```

### Data Location

Default database path:

```text
~/.local/share/moneyterm/ledger.sqlite3
```

Use a custom data folder:

```bash
MONEY_HOME=/path/to/data python money.py list
```

## 中文

### 指令格式

```bash
python money.py <指令> [選項]
```

目前可用指令：

- `add`：新增一筆收入或支出
- `list`：列出最近交易紀錄
- `report`：顯示月報表與圖表
- `dash`：開啟終端機互動儀表板
- `demo`：加入測試用範例資料

### 新增支出

支出使用負數金額。

```bash
python money.py add -120 早餐 -c food -a cash
```

意思是：

- `-120`：花費 120
- `早餐`：備註
- `-c food`：分類是 food
- `-a cash`：帳戶是 cash

更多例子：

```bash
python money.py add -80 午餐 -c food -a cash
python money.py add -45 公車 -c transport -a cash
python money.py add -950 日用品 -c shopping -a card
```

### 新增收入

收入使用正數金額。

```bash
python money.py add 52000 薪水 -c salary -a bank
```

意思是：

- `52000`：收入 52,000
- `薪水`：備註
- `-c salary`：分類是 salary
- `-a bank`：帳戶是 bank

### 指定日期

使用 `-d` 或 `--date` 指定日期。

```bash
python money.py add -120 早餐 -c food -a cash -d 2026-05-06
```

支援的日期：

- `today`
- `yesterday`
- `YYYY-MM-DD`，例如 `2026-05-06`

### 查看交易紀錄

列出最近交易：

```bash
python money.py list
```

限制顯示筆數：

```bash
python money.py list --limit 20
```

用日期範圍篩選：

```bash
python money.py list --from 2026-05-01 --to 2026-05-31
```

### 月報表

查看本月報表：

```bash
python money.py report
```

查看指定月份：

```bash
python money.py report -m 2026-05
```

報表會顯示：

- 總收入
- 總支出
- 結餘
- 文字長條圖
- 圓餅比例表

### 終端機儀表板

開啟可縮放的 terminal dashboard：

```bash
python money.py dash
```

操作方式：

- `h` 或左方向鍵：上一個月
- `l` 或右方向鍵：下一個月
- `q`：離開

儀表板會依照 terminal 大小自動切換版面，適合手機 Termux 風格使用。

### 範例資料

加入範例資料：

```bash
python money.py demo
```

再查看報表：

```bash
python money.py report
```

### 資料位置

預設資料庫位置：

```text
~/.local/share/moneyterm/ledger.sqlite3
```

自訂資料資料夾：

```bash
MONEY_HOME=/path/to/data python money.py list
```
