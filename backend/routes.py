"""第三週：目標與任務的新增、查詢、修改、刪除及標記完成。"""
from datetime import date, datetime, timezone
from typing import Annotated
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response

from backend.database import connect
from backend.schemas import (GoalCreate, GoalRead, GoalUpdate, TaskCreate, TaskRead,
                             TaskUpdate)

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
    return find_task(db, task_id)


@router.patch("/goals/{goal_id}", response_model=GoalRead, tags=["目標"])
def update_goal(goal_id: Identifier, body: GoalUpdate, db: Database):
    find_goal(db, goal_id)
    changes = to_columns(body)
    if changes:
        save_changes(db, "goals", goal_id, changes)
    return find_goal(db, goal_id)


@router.delete("/goals/{goal_id}", status_code=204, response_class=Response, tags=["目標"])
def delete_goal(goal_id: Identifier, db: Database):
    """刪除目標，並連帶刪除其所有任務（資料表設定 ON DELETE CASCADE）。"""
    find_goal(db, goal_id)
    with db:
        db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))


@router.patch("/tasks/{task_id}", response_model=TaskRead, tags=["任務"])
def update_task(task_id: Identifier, body: TaskUpdate, db: Database):
    task = find_task(db, task_id)
    changes = to_columns(body)
    new_status = changes.get("status")
    if new_status == "completed" and task["status"] != "completed":
        changes["completed_at"] = datetime.now(timezone.utc).isoformat()
    elif new_status is not None and new_status != "completed":
        changes["completed_at"] = None
    if changes:
        save_changes(db, "tasks", task_id, changes)
    return find_task(db, task_id)


@router.delete("/tasks/{task_id}", status_code=204, response_class=Response, tags=["任務"])
def delete_task(task_id: Identifier, db: Database):
    find_task(db, task_id)
    with db:
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def find_task(db: sqlite3.Connection, task_id: int):
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到此任務")
    return dict(row)


def to_columns(body: GoalUpdate | TaskUpdate) -> dict:
    """只取使用者有傳入的欄位，日期轉成 YYYY-MM-DD 字串。"""
    changes = body.model_dump(exclude_unset=True)
    return {key: value.isoformat() if isinstance(value, date) else value
            for key, value in changes.items()}


def save_changes(db: sqlite3.Connection, table: str, row_id: int, changes: dict) -> None:
    # 欄位名稱來自 schemas 的固定定義，不是使用者輸入，可以安全組進 SQL。
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    assignments = ", ".join(f"{column} = ?" for column in changes)
    with db:
        db.execute(f"UPDATE {table} SET {assignments} WHERE id = ?",
                   (*changes.values(), row_id))
