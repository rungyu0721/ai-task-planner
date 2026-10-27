# 第三週：資料庫與基礎 API

本週成果：依第二週 ERD 建立 `goals` 與 `tasks` 資料表，完成新增及查詢。
採單人模式；修改、刪除、標記完成和前端串接安排在第四週，AI 紀錄表留待 AI 串接階段建立。

## 啟動與展示

在專案根目錄執行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

開啟 http://127.0.0.1:8000/docs，每一項 API 都可以按 **Try it out** → **Execute**。

1. 展開 `POST /api/goals`，貼上以下目標內容，執行後應回傳 **201**。
2. 記下回傳的 `id`，作為之後的 `goal_id`。
3. 展開 `POST /api/goals/{goal_id}/tasks`，填入實際的目標 ID 及下方任務內容，應回傳 **201**。
4. 用 `GET /api/goals`、`GET /api/goals/{goal_id}/tasks` 查看新增結果，應回傳 **200**。
5. 在終端機按 Ctrl+C 停止，再重新啟動，查詢相同 ID，確認資料仍存在。
6. 將名稱改成空字串測試，應回傳 **422**；查詢不存在的 ID，應回傳 **404**。

新增目標範例：

```json
{
  "title": "完成資訊科技專題",
  "description": "建立 AI 目標與任務管理系統",
  "target_date": "2027-01-15",
  "weekly_hours": 8
}
```

新增任務範例（日期僅供測試，依實際進度調整）：

```json
{
  "title": "完成資料庫與基礎 API",
  "description": "建立目標、任務資料表並測試新增與查詢",
  "priority": "high",
  "due_date": "2026-11-02",
  "estimated_minutes": 120,
  "sort_order": 0
}
```

## 欄位與驗證規則

- 名稱 `title` 必填，去除頭尾空白後為 1～200 字；說明最多 10000 字。
- 日期使用 `YYYY-MM-DD`，未指定時傳 `null` 或省略；不接受不存在的日期。
- `weekly_hours` 為 1～168 的整數，`estimated_minutes` 為正整數，均可省略或傳 `null`。
- `priority` 為 `high`／`medium`／`low`，預設 `medium`。
- `sort_order` 為非負整數，預設 0。
- 不接受未定義的輸入欄位，避免拼錯欄位卻被默默忽略。
- ID、狀態、來源與時間由後端設定：目標為 `active`；任務為 `todo`、`manual`，完成時間為 `null`。
- 日期不含時分；建立與更新時間統一使用 UTC，API 回傳含時區的 ISO 8601 字串。
- 新增任務前確認目標存在，SQLite 外鍵也會阻擋孤立任務。
- 資料表已設定刪除目標時連帶刪除任務；本週尚未提供刪除 API。

## 檔案位置

- `backend/database.py`：建表、索引、SQLite 連線與外鍵設定。
- `backend/schemas.py`：API 輸入與輸出格式。
- `backend/routes.py`：六個新增、查詢 API。
- `backend/main.py`：啟動時初始化資料庫，保留原有首頁與靜態頁面。
- `backend/data/task_planner.db`：首次啟動自動建立，路徑固定於專案內，不隨啟動目錄改變。
- `tests/test_api.py`：HTTP 整合測試，驗證持久化、欄位檢查、任務歸屬、外鍵及頁面可用性。

## 本週可報告的進度

已完成 SQLite 資料庫與目標、任務的新增及查詢 API，可透過 Swagger UI 實際操作，
資料重新啟動後仍保留；已通過自動測試。下一週進行修改、刪除、完成狀態與前端串接。
