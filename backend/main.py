from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI 智慧任務規劃與管理系統")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/api/hello")
def hello():
    """測試用 API：確認後端有正常運作。"""
    return {"message": "Hello, AI 任務規劃系統！"}


# 前端靜態檔案（CSS、JS）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    """首頁：回傳前端的 index.html。"""
    return FileResponse(FRONTEND_DIR / "index.html")
