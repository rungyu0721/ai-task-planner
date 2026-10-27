"""公開 API 的輸入驗證與輸出格式。"""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: str = Field(default="", max_length=10000)
    target_date: date | None = None
    weekly_hours: int | None = Field(default=None, ge=1, le=168, strict=True)


class GoalRead(GoalCreate):
    id: int
    ai_summary: str | None
    status: Literal["active", "completed", "archived"]
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: str = Field(default="", max_length=10000)
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, strict=True)
    sort_order: int = Field(default=0, ge=0, strict=True)


class TaskRead(TaskCreate):
    id: int
    goal_id: int
    status: Literal["todo", "in_progress", "completed"]
    source: Literal["ai", "manual"]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
