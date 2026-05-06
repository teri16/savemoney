# SaveMoney GUI Design Guide

This document defines the interface direction for SaveMoney as a future mobile
app and web app.

Important clarification: SaveMoney is not meant to run inside Termux. The UI
should only feel similar to Termux: compact, text-forward, direct, and fast.

中文版在下方同一頁面。

## English

### Product Target

SaveMoney should become:

- A mobile app for daily accounting
- A responsive web app for larger screens
- Optionally, a desktop app later

The existing Python CLI is only a prototype for accounting logic and input
flows. It is not the final runtime.

### Visual Direction

The interface should feel like a terminal-inspired finance console:

- Dense but readable
- Text-first
- Fast to operate with touch or keyboard
- Dark mode friendly
- Minimal decoration
- Clear numeric hierarchy
- Built for repeated daily use

### Main App Sections

- `Quick`: fast transaction entry
- `Ledger`: transaction list
- `Report`: monthly totals and charts
- `Memory`: remembered notes, categories, and accounts
- `Settings`: data path, export, backup, sync

### Mobile App Home

Target: phone portrait screens around 360 to 430 px wide.

```text
SaveMoney                      2026-05
--------------------------------------
BALANCE                         37,170
INCOME                          52,000
EXPENSE                        -14,830

[ Quick ] [ Ledger ] [ Report ]

Quick Entry
> Amount     -120
  Note       breakfast
  Category   food
  Account    cash

Suggestions
notes: breakfast, lunch, dinner
cats : food, transport, shopping

Keypad
[1] [2] [3] [+]
[4] [5] [6] [-]
[7] [8] [9] [del]
[0] [00][clr][next]
[food] [transport]
[shopping] [other]
[save]
```

### Mobile Input Model

Mobile input should not depend on terminal key events. It should use real app
controls:

- Native text fields for Chinese and IME support
- Touch keypad for quick amount input
- Suggestion chips for old notes and categories
- Large save button near the bottom
- Optional hardware keyboard shortcuts on tablets

### Web Layout

Target: responsive desktop and tablet screens.

```text
+-------------+ +-----------------------+ +------------------+
| Navigation  | | Quick Entry           | | Month Summary    |
| Quick       | | Amount      -120      | | Balance  37,170  |
| Ledger      | | Note        breakfast | | Income   52,000  |
| Report      | | Category    food      | | Expense -14,830  |
| Memory      | | Account     cash      | +------------------+
| Settings    | | [Save] [Clear]        |
+-------------+ +-----------------------+ +------------------+

+-----------------------------------+ +--------------------+
| Recent Transactions               | | Charts             |
| 05-06  -120  food      breakfast  | | food      ######## |
| 05-06  -950  shopping  groceries  | | housing   ######   |
+-----------------------------------+ | pie share table    |
                                      +--------------------+
```

### Quick Entry Flow

1. User opens the app.
2. Quick Entry is visible immediately.
3. Amount starts ready for expense entry.
4. User types or taps the keypad.
5. User selects an old note/category or types a new one.
6. User chooses account.
7. User taps save.
8. The transaction is stored and note/category suggestions update.

### Remembered Inputs

The app should remember:

- Notes
- Categories
- Accounts

Remembered values should appear as suggestions ordered by recent use and
frequency. Users can still type a new value at any time.

### Charts

Mobile:

- Digital totals at the top
- Compact horizontal bars
- Pie-share list instead of a complex circular chart when space is tight

Web:

- Month summary cards
- Category bar chart
- Pie or donut chart when there is enough space
- Transaction list filtered by selected month

### Style Rules

- Dark console-like background
- High contrast text
- Accent colors for selected controls and important numbers
- Cards should be compact and functional
- Avoid marketing-style hero sections
- Avoid decorative gradients or background ornaments
- Buttons should feel like terminal keys but remain touch-friendly

### Future Implementation Options

Mobile app:

- React Native
- Flutter
- Capacitor with a web UI

Web app:

- React or SvelteKit frontend
- API layer around the same accounting model
- SQLite for local or single-user deployments

Desktop app:

- Tauri or Electron wrapper around the web UI

## 中文

### 產品目標

SaveMoney 的目標是：

- 手機 App
- 響應式網頁版
- 未來可選擇延伸成桌面 App

目前的 Python CLI 只是用來驗證記帳邏輯與輸入流程，不是最終執行環境。

### 重要方向

SaveMoney 不是要跑在 Termux 裡，而是要做出類似 Termux 的視覺感：

- 緊湊
- 文字優先
- 操作直接
- 速度快
- 適合每天重複使用
- 能在手機 App 與網頁版中呈現

### 主畫面分區

- `Quick`：快速記帳
- `Ledger`：交易列表
- `Report`：月報表與圖表
- `Memory`：舊備註、分類、帳戶
- `Settings`：資料、匯出、備份、同步

### 手機 App 首頁

目標：手機直向畫面，約 360 到 430 px 寬。

```text
SaveMoney                      2026-05
--------------------------------------
BALANCE                         37,170
INCOME                          52,000
EXPENSE                        -14,830

[ Quick ] [ Ledger ] [ Report ]

Quick Entry
> Amount     -120
  Note       早餐
  Category   food
  Account    cash

Suggestions
notes: 早餐, 午餐, 晚餐
cats : food, transport, shopping

Keypad
[1] [2] [3] [+]
[4] [5] [6] [-]
[7] [8] [9] [del]
[0] [00][clr][next]
[food] [transport]
[shopping] [other]
[save]
```

### 手機輸入模型

手機 App 不應依賴 terminal key event，而應使用真正的 App 控制元件：

- 原生文字輸入欄位，支援中文與輸入法
- 觸控數字鍵盤，快速輸入金額
- 舊備註與舊分類用建議 chip 選取
- 儲存按鈕放在容易按的位置
- 平板或網頁版可額外支援鍵盤快捷鍵

### 網頁版版面

目標：桌面與平板的響應式畫面。

```text
+-------------+ +-----------------------+ +------------------+
| Navigation  | | Quick Entry           | | Month Summary    |
| Quick       | | Amount      -120      | | Balance  37,170  |
| Ledger      | | Note        早餐      | | Income   52,000  |
| Report      | | Category    food      | | Expense -14,830  |
| Memory      | | Account     cash      | +------------------+
| Settings    | | [Save] [Clear]        |
+-------------+ +-----------------------+ +------------------+

+-----------------------------------+ +--------------------+
| Recent Transactions               | | Charts             |
| 05-06  -120  food      早餐       | | food      ######## |
| 05-06  -950  shopping  日用品     | | housing   ######   |
+-----------------------------------+ | pie share table    |
                                      +--------------------+
```

### 快速記帳流程

1. 使用者開啟 App。
2. 第一畫面直接顯示 Quick Entry。
3. 金額欄位準備好輸入支出。
4. 使用者可打字或點觸控鍵盤。
5. 備註與分類可選舊資料，也可輸入新資料。
6. 選擇帳戶。
7. 按下儲存。
8. 交易寫入資料庫，備註與分類更新到建議清單。

### 記憶輸入

App 需要記憶：

- 備註
- 分類
- 帳戶

記憶資料依最近使用與常用程度排序，但使用者永遠可以輸入新內容。

### 圖表

手機：

- 上方顯示數字總覽
- 使用緊湊橫向長條圖
- 空間不足時用圓餅比例列表，不一定要畫完整圓形圖

網頁：

- 月份總覽卡片
- 分類長條圖
- 空間足夠時可用圓餅圖或甜甜圈圖
- 下方顯示該月份交易列表

### 視覺規則

- 深色 console 風格背景
- 高對比文字
- 選取狀態與重要數字使用 accent 色
- 卡片要緊湊且功能導向
- 不做行銷式首頁
- 不使用裝飾性漸層或背景圖案
- 按鈕可以像 terminal key，但必須適合觸控

### 未來實作選項

手機 App：

- React Native
- Flutter
- Capacitor 搭配 Web UI

網頁版：

- React 或 SvelteKit frontend
- API layer 包裝同一套記帳模型
- SQLite 適合本地或單人使用

桌面 App：

- Tauri 或 Electron 包裝 web UI
