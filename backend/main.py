from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.database import DEFAULT_DB_PATH, initialize
from backend.routes import router

def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(app.state.db_path)
        yield

    application = FastAPI(title="AI 智慧任務規劃與管理系統", lifespan=lifespan)
    application.state.db_path = Path(db_path)
    application.include_router(router)
    application.add_api_route("/api/hello", hello, methods=["GET"])
    application.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    application.add_api_route("/", index, methods=["GET"], response_class=FileResponse)
    return application

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def hello():
    """測試用 API：確認後端有正常運作。"""
    return {"message": "Hello, AI 任務規劃系統！"}


def index():
    """首頁：回傳前端的 index.html。"""
    return FileResponse(FRONTEND_DIR / "index.html")


app = create_app()
