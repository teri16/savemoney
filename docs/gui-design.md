# MoneyTerm GUI Design Guide

This document defines the first interface direction for MoneyTerm across phone
terminal mode, desktop app mode, and future web mode.

中文版在下方同一頁面。

## English

### Design Direction

MoneyTerm should feel like a small, fast terminal-native finance tool rather
than a heavy banking dashboard. The first screen should support real accounting
work immediately: add a transaction, inspect balance, and see monthly spending.

Core principles:

- Fast entry first
- Works in narrow phone terminals
- Remembers old notes, categories, and accounts
- Shows numbers, bar charts, and pie-share summaries
- Same core layout can later become local app and web UI

### Main Navigation

Suggested sections:

- `Quick`: fast transaction entry
- `Ledger`: transaction list
- `Report`: monthly totals and charts
- `Memory`: remembered notes, categories, and accounts
- `Settings`: data path, export, backup, sync

Terminal shortcut mapping:

- `1`: Quick
- `2`: Ledger
- `3`: Report
- `4`: Memory
- `5`: Settings
- `q`: Quit

### Phone Terminal Layout

Target size: around 40 to 60 columns wide.

```text
MoneyTerm                      May 2026
---------------------------------------
BALANCE                         $37,170
INCOME                          $52,000
EXPENSE                        -$14,830

[1] Quick  [2] Ledger  [3] Report

Quick Entry
> Amount     -120
  Note       breakfast
  Category   food
  Account    cash

Remembered
notes: breakfast, lunch, dinner
cats : food, transport, shopping

Virtual Keyboard
[1] [2] [3] [+]
[4] [5] [6] [-]
[7] [8] [9] [BKSP]
[0] [00][CLR][FIELD]
[FOOD][TRANS][SHOP][OTHER]
[NOTE<][NOTE>][CAT<][CAT>]
[SAVE] [QUIT]
```

### Desktop And Web Layout

Target size: wider than 900 px or around 100 terminal columns.

```text
┌ Sidebar ──────┐ ┌ Quick Entry ─────────────┐ ┌ Month Summary ──────┐
│ Quick         │ │ Amount        -120       │ │ Balance   $37,170   │
│ Ledger        │ │ Note          breakfast  │ │ Income    $52,000   │
│ Report        │ │ Category      food       │ │ Expense  -$14,830   │
│ Memory        │ │ Account       cash       │ └─────────────────────┘
│ Settings      │ │ [Save] [Clear]           │
└───────────────┘ └──────────────────────────┘ ┌ Charts ─────────────┐
                                                │ food      ███████   │
┌ Recent Transactions ────────────────────────┐ │ housing   ██████    │
│ 05-06  -120   food       breakfast          │ │ transport ██        │
│ 05-06  -950   shopping   groceries          │ │ Pie-share table     │
└─────────────────────────────────────────────┘ └─────────────────────┘
```

### Quick Entry Flow

1. User opens `quick`.
2. Amount field is selected by default and starts as `-`.
3. User enters amount by typing or using virtual keyboard.
4. User presses `Tab` or virtual `FIELD` to move fields.
5. Note can be typed or selected with `NOTE<` / `NOTE>`.
6. Category can be typed, selected with `CAT<` / `CAT>`, or chosen by quick category buttons.
7. User presses `SAVE`.
8. Transaction is saved to SQLite and the note/category become remembered values.

### Field Behavior

Amount:

- Default value for quick expense: `-`
- Positive values are income
- Negative values are expense
- Must be a non-zero integer

Note:

- Free text
- Old notes appear as suggestions
- Should support Chinese input in terminal environments that support wide chars

Category:

- Free text
- Old categories appear as suggestions
- Common buttons: `food`, `transport`, `shopping`, `other`

Account:

- Free text
- Old accounts appear as suggestions
- Common defaults: `cash`, `bank`, `card`

### Report Layout

Phone terminal:

```text
Report 2026-05
Income   $52,000
Expense -$14,830
Balance  $37,170

BAR
food      |########....| -$800
housing   |############| -$13,800
transport |##..........| -$1,280

PIE
food        5.4% oo..................
housing    93.0% ooooooooooooooooooo.
transport  8.6% oo..................
```

Desktop/web:

- Top: month selector and totals
- Left: category bar chart
- Right: pie-share table
- Bottom: transaction list for the selected month

### Visual Style

Terminal mode:

- ASCII-first UI
- No dependency on colors
- Optional color later for income, expense, selected button
- Clear focus marker: `>`
- Selected virtual key: `[SAVE]`

Desktop/web mode:

- Compact dashboard, not a marketing page
- 8 px or smaller radius
- Dense but readable table rows
- Use icons only for common actions such as save, delete, edit, export
- Avoid decorative backgrounds

### Future Implementation Options

Terminal:

- Keep Python `curses` for now
- Consider Textual later if richer terminal widgets are needed

Desktop:

- Tauri wrapper around a local web UI
- Local API reads the same SQLite schema

Web:

- FastAPI or similar API server
- React, SvelteKit, or plain server-rendered UI
- Same command concepts: quick add, ledger, report, memory

## 中文

### 設計方向

MoneyTerm 應該像一個小而快的 terminal 原生記帳工具，而不是厚重的銀行後台。第一個畫面就要能做真正的記帳工作：新增交易、查看結餘、查看本月支出。

核心原則：

- 快速輸入優先
- 能在手機窄版 terminal 使用
- 記住舊備註、分類、帳戶
- 顯示數字、長條圖、圓餅比例表
- 同一套介面概念未來可延伸成本地 app 與網頁版

### 主選單

建議分區：

- `Quick`：快速記帳
- `Ledger`：交易列表
- `Report`：月報表與圖表
- `Memory`：舊備註、分類、帳戶
- `Settings`：資料位置、匯出、備份、同步

Terminal 快捷鍵：

- `1`：Quick
- `2`：Ledger
- `3`：Report
- `4`：Memory
- `5`：Settings
- `q`：離開

### 手機 Terminal 版面

目標寬度：約 40 到 60 欄。

```text
MoneyTerm                      2026-05
---------------------------------------
BALANCE                         $37,170
INCOME                          $52,000
EXPENSE                        -$14,830

[1] Quick  [2] Ledger  [3] Report

Quick Entry
> Amount     -120
  Note       早餐
  Category   food
  Account    cash

Remembered
notes: 早餐, 午餐, 晚餐
cats : food, transport, shopping

Virtual Keyboard
[1] [2] [3] [+]
[4] [5] [6] [-]
[7] [8] [9] [BKSP]
[0] [00][CLR][FIELD]
[FOOD][TRANS][SHOP][OTHER]
[NOTE<][NOTE>][CAT<][CAT>]
[SAVE] [QUIT]
```

### 桌面與網頁版面

目標寬度：大於 900 px，或約 100 個 terminal 欄位。

```text
┌ Sidebar ──────┐ ┌ Quick Entry ─────────────┐ ┌ Month Summary ──────┐
│ Quick         │ │ Amount        -120       │ │ Balance   $37,170   │
│ Ledger        │ │ Note          早餐       │ │ Income    $52,000   │
│ Report        │ │ Category      food       │ │ Expense  -$14,830   │
│ Memory        │ │ Account       cash       │ └─────────────────────┘
│ Settings      │ │ [Save] [Clear]           │
└───────────────┘ └──────────────────────────┘ ┌ Charts ─────────────┐
                                                │ food      ███████   │
┌ Recent Transactions ────────────────────────┐ │ housing   ██████    │
│ 05-06  -120   food       早餐               │ │ transport ██        │
│ 05-06  -950   shopping   日用品             │ │ Pie-share table     │
└─────────────────────────────────────────────┘ └─────────────────────┘
```

### 快速輸入流程

1. 使用者開啟 `quick`。
2. 預設選取金額欄位，金額從 `-` 開始，方便輸入支出。
3. 使用者可直接打字，也可使用虛擬鍵盤輸入金額。
4. 使用者按 `Tab` 或虛擬鍵 `FIELD` 切換欄位。
5. 備註可直接輸入，也可用 `NOTE<` / `NOTE>` 選舊備註。
6. 分類可直接輸入，也可用 `CAT<` / `CAT>` 或快速分類按鍵選擇。
7. 使用者按 `SAVE`。
8. 交易寫入 SQLite，備註與分類會成為下次可選的記憶資料。

### 欄位行為

金額：

- 快速支出預設為 `-`
- 正數是收入
- 負數是支出
- 必須是非 0 整數

備註：

- 可自由輸入
- 舊備註會出現在建議清單
- 支援 terminal 環境可處理的中文輸入

分類：

- 可自由輸入
- 舊分類會出現在建議清單
- 常用按鍵：`food`、`transport`、`shopping`、`other`

帳戶：

- 可自由輸入
- 舊帳戶會出現在建議清單
- 常見預設：`cash`、`bank`、`card`

### 報表版面

手機 terminal：

```text
Report 2026-05
Income   $52,000
Expense -$14,830
Balance  $37,170

BAR
food      |########....| -$800
housing   |############| -$13,800
transport |##..........| -$1,280

PIE
food        5.4% oo..................
housing    93.0% ooooooooooooooooooo.
transport  8.6% oo..................
```

桌面/網頁：

- 上方：月份切換與總數
- 左側：分類長條圖
- 右側：圓餅比例表
- 下方：該月份交易列表

### 視覺風格

Terminal 模式：

- ASCII 優先
- 不依賴顏色
- 未來可加收入、支出、選取按鍵顏色
- 使用 `>` 顯示目前欄位
- 使用 `[SAVE]` 表示選取的虛擬按鍵

桌面/網頁模式：

- 緊湊型 dashboard，不做行銷首頁
- 圓角 8 px 以下
- 表格列密集但可讀
- 儲存、刪除、編輯、匯出等常見動作用 icon
- 避免裝飾性背景

### 未來實作選項

Terminal：

- 目前保留 Python `curses`
- 如果需要更完整 terminal widget，可考慮 Textual

桌面：

- Tauri 包裝本地 web UI
- 本地 API 讀取同一份 SQLite schema

網頁：

- FastAPI 或類似 API server
- React、SvelteKit，或純 server-rendered UI
- 延續相同概念：快速記帳、交易列表、報表、記憶資料
