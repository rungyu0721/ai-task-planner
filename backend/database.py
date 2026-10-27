"""SQLite 初始化與連線；每次請求使用獨立連線。"""
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "task_planner.db"


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    try:
        with connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                    description TEXT NOT NULL DEFAULT '',
                    target_date TEXT,
                    weekly_hours INTEGER CHECK(weekly_hours BETWEEN 1 AND 168),
                    ai_summary TEXT,
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active', 'completed', 'archived')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
                    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'todo'
                        CHECK(status IN ('todo', 'in_progress', 'completed')),
                    priority TEXT NOT NULL DEFAULT 'medium'
                        CHECK(priority IN ('high', 'medium', 'low')),
                    due_date TEXT,
                    estimated_minutes INTEGER CHECK(estimated_minutes > 0),
                    sort_order INTEGER NOT NULL DEFAULT 0 CHECK(sort_order >= 0),
                    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('ai', 'manual')),
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tasks_goal_order
                    ON tasks(goal_id, sort_order, id);
            """)
    finally:
        connection.close()
