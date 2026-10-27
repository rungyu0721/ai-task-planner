"""第三週：目標與任務的新增、列表及單筆查詢。"""
from datetime import datetime, timezone
from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from backend.database import connect
from backend.schemas import GoalCreate, GoalRead, TaskCreate, TaskRead

router = APIRouter(prefix="/api")
Identifier = Annotated[int, Path(ge=1)]


def get_db(request: Request):
    connection = connect(request.app.state.db_path)
    try:
        yield connection
    finally:
        connection.close()


Database = Annotated[sqlite3.Connection, Depends(get_db)]


def find_goal(db: sqlite3.Connection, goal_id: int):
    row = db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到此目標")
    return dict(row)


@router.post("/goals", response_model=GoalRead, status_code=201, tags=["目標"])
def create_goal(body: GoalCreate, db: Database):
    now = datetime.now(timezone.utc).isoformat()
    with db:
        cursor = db.execute(
            """INSERT INTO goals
               (title, description, target_date, weekly_hours, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (body.title, body.description, body.target_date.isoformat() if body.target_date else None,
             body.weekly_hours, now, now),
        )
    return find_goal(db, cursor.lastrowid)


@router.get("/goals", response_model=list[GoalRead], tags=["目標"])
def list_goals(db: Database, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    return [dict(row) for row in db.execute(
        "SELECT * FROM goals ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
    )]


@router.get("/goals/{goal_id}", response_model=GoalRead, tags=["目標"])
def get_goal(goal_id: Identifier, db: Database):
    return find_goal(db, goal_id)


@router.post("/goals/{goal_id}/tasks", response_model=TaskRead, status_code=201, tags=["任務"])
def create_task(goal_id: Identifier, body: TaskCreate, db: Database):
    find_goal(db, goal_id)
    now = datetime.now(timezone.utc).isoformat()
    with db:
        cursor = db.execute(
            """INSERT INTO tasks
               (goal_id, title, description, priority, due_date, estimated_minutes,
                sort_order, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, body.title, body.description, body.priority,
             body.due_date.isoformat() if body.due_date else None,
             body.estimated_minutes, body.sort_order, now, now),
        )
    return dict(db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone())


@router.get("/goals/{goal_id}/tasks", response_model=list[TaskRead], tags=["任務"])
def list_tasks(goal_id: Identifier, db: Database,
               offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100)):
    find_goal(db, goal_id)
    return [dict(row) for row in db.execute(
        "SELECT * FROM tasks WHERE goal_id = ? ORDER BY sort_order, id LIMIT ? OFFSET ?",
        (goal_id, limit, offset),
    )]


@router.get("/tasks/{task_id}", response_model=TaskRead, tags=["任務"])
def get_task(task_id: Identifier, db: Database):
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到此任務")
    return dict(row)
