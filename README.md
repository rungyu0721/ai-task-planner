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
- 資料庫、CRUD 與 AI API 將依後續週次串接。`/api/hello`、`/docs` 繼續可用。

前端結構：`frontend/pages/` 為六個展示頁面，`frontend/css/` 為樣式，
`frontend/integration.js` 處理後端連線狀態與示意提示。
`frontend/tokens.json`、`frontend/設計規範.md` 與 `frontend/DESIGN-README.md`
保留原始設計參考；原始 README 的 Live Server 操作不適用於整合後的入口。
