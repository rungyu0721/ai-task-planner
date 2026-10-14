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
