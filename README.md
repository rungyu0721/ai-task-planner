# AI 智慧任務規劃與管理系統

結合 AI 技術，協助使用者將複雜目標拆解為具體任務，並透過任務管理與進度追蹤提升效率。

## 技術
- 後端：Python FastAPI
- 資料庫：SQLite
- 前端：HTML / CSS / JavaScript、Chart.js

## 執行方式

```powershell
# 第一次：建立虛擬環境並安裝套件
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 啟動伺服器
uvicorn backend.main:app --reload
```

- 網站首頁：http://127.0.0.1:8000
- API 測試頁面：http://127.0.0.1:8000/docs

## 專案結構
```
backend/    後端程式（API、資料庫）
frontend/   前端頁面（HTML、CSS、JS）
```

## 第二週：前端介面雛形

已整合提供的 task-planner-ui 設計，保留原有配色與版面。
沿用上述 FastAPI 啟動方式，不需要另外啟動 Live Server 或安裝前端套件。

- 開啟 http://127.0.0.1:8000，會進入首頁。
- 展示動線：首頁 → 新增目標 → AI 任務草稿 → 確認並儲存 → 目標詳情。
- 側邊選單可切換首頁、目標詳情與進度分析；小螢幕提供上方導覽。
- 手機版設計示意：http://127.0.0.1:8000/static/pages/mobile.html。
- 所有任務、統計與 AI 文字都是固定範例；確認儲存只切換頁面，不會寫入資料。
- 表單目前是視覺稿，尚不能輸入；其餘未實作按鈕會顯示提示。
- 第三週已新增資料庫與目標、任務的新增、查詢、修改、刪除 API；前端串接與 AI 功能依後續週次實作。`/api/hello`、`/docs` 繼續可用。

前端結構：`frontend/pages/` 為六個展示頁面，`frontend/css/` 為樣式，
`frontend/integration.js` 處理後端連線狀態與示意提示。
`frontend/tokens.json`、`frontend/設計規範.md` 與 `frontend/DESIGN-README.md`
保留原始設計參考；原始 README 的 Live Server 操作不適用於整合後的入口。

## 第三週：SQLite 與基礎 API

啟動指令不變，首次啟動會自動建立 `backend/data/task_planner.db`，不需要另裝資料庫套件。
資料檔已由 `.gitignore` 的 `*.db` 排除，不提交 Git。重新啟動不會清空資料，也不會自動塞入範例資料。

| 方法 | 路徑 | 功能 |
|---|---|---|
| POST | `/api/goals` | 新增目標 |
| GET | `/api/goals` | 目標列表 |
| GET | `/api/goals/{goal_id}` | 查詢單一目標 |
| POST | `/api/goals/{goal_id}/tasks` | 在指定目標下新增任務 |
| GET | `/api/goals/{goal_id}/tasks` | 查詢指定目標的任務 |
| GET | `/api/tasks/{task_id}` | 查詢單一任務 |
| PATCH | `/api/goals/{goal_id}` | 修改目標（只更新有傳入的欄位） |
| DELETE | `/api/goals/{goal_id}` | 刪除目標（連同其任務） |
| PATCH | `/api/tasks/{task_id}` | 修改任務；`status` 改為 `completed` 即標記完成 |
| DELETE | `/api/tasks/{task_id}` | 刪除任務 |

列表支援 `limit`（1～100，預設 100）與 `offset`（預設 0）。
目標依 ID 由新到舊；任務依 `sort_order`、ID 由小到大。

操作範例與驗收步驟見 [第三週操作說明](docs/week3-api.md)。
目前網頁仍使用第二週假資料；新增資料請在 `/docs` 查看，第四週再串接網頁。

執行自動測試（使用臨時資料庫，不更動正式資料）：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 第四週：前後端串接

目標與任務管理已改用資料庫的真實資料，從側邊選單的「我的目標」進入。

- **我的目標**（`goals.html`）：列出所有目標與完成進度。
- **新增目標**：填寫表單後按「不用 AI，手動建立」即寫入資料庫；「AI 幫我拆解」於第 6～8 週串接。
- **目標詳情**（`goal-detail.html?id=目標ID`）：新增、編輯、刪除任務，勾選完成／取消完成，依狀態篩選；可編輯或刪除目標（刪除前會確認）。
- 首頁、進度分析與 AI 預覽頁仍為範例資料，依後續週次串接。

前端程式位於 `frontend/js/`：`api.js` 為共用工具（呼叫 API、提示訊息、表單讀寫），其餘檔案各對應一個頁面。

## 第五週：日期、優先級與逾期判斷

- **逾期判斷**：任務有截止日期、尚未完成，且截止日早於今天（以使用者電腦的日期為準），即視為逾期。已完成的任務不算逾期。
- **目標詳情**：逾期任務的截止日期顯示為紅色，並加上「逾期」標籤與「逾期 N 天」；今天或明天到期的任務也會提示。新增「逾期」分頁可只看逾期任務。
- **排序**：可切換「預設順序」、「截止日期」（未設定日期的排最後）、「優先級」（高→中→低，同級再依截止日期）。
- **我的目標**：目標卡片會顯示有幾個任務逾期。

判斷與排序邏輯位於 `frontend/js/api.js` 的 `isOverdue`、`dueHint`、`sortTasks`。
