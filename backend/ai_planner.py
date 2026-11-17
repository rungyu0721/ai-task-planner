"""AI 任務拆解：產生提示詞、規定 JSON 輸出格式，並檢查 AI 回傳的內容。

第六週只處理「問什麼、回傳什麼格式、怎麼檢查」；網頁串接與錯誤重試在第七週。
"""
from datetime import date
import json
import math
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

MIN_TASKS = 3
MAX_TASKS = 12

Text = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class AiTask(BaseModel):
    """AI 產生的單一任務；欄位與 TaskCreate 對應，之後可直接存入資料庫。"""
    model_config = ConfigDict(extra="ignore")

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: Text = ""
    priority: Literal["high", "medium", "low"]
    due_date: date | None = None
    estimated_minutes: int = Field(ge=5, le=600)


class AiPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: Text
    tasks: list[AiTask] = Field(min_length=MIN_TASKS, max_length=MAX_TASKS)


class PlanError(ValueError):
    """AI 回傳的內容無法使用（不是 JSON、缺欄位或格式錯誤）。"""


def build_prompt(title: str, description: str = "", target_date: date | None = None,
                 weekly_hours: int | None = None, today: date | None = None) -> str:
    today = today or date.today()
    lines = [
        "你是一位擅長時間管理的學習與專案規劃助理。",
        "請把使用者的目標拆解成具體、可執行的任務，並依照建議的執行順序排列。",
        "",
        "【使用者的目標】",
        f"目標名稱：{title}",
        f"目標說明：{description or '（未提供）'}",
        f"今天日期：{today.isoformat()}",
    ]
    if target_date:
        lines.append(f"希望完成日期：{target_date.isoformat()}（還有 {(target_date - today).days} 天）")
    else:
        lines.append("希望完成日期：未設定（請自行安排合理的進度，約 4 週內完成）")
    budget = available_minutes(target_date, weekly_hours, today)
    if budget:
        lines.append(f"每週可用時間：{weekly_hours} 小時（到期前總共約 {budget} 分鐘）")
    else:
        lines.append("每週可用時間：未設定")
    lines += [
        "",
        "【拆解規則】",
        f"1. 拆成 {MIN_TASKS} 到 {MAX_TASKS} 個任務，每個任務要具體到看了就知道要做什麼，以動詞開頭。",
        "2. 每個任務的預估時間在 5 到 600 分鐘之間；太大的任務請再拆小。",
        "3. 截止日期使用 YYYY-MM-DD 格式，不可早於今天" + ("，也不可晚於希望完成日期。" if target_date else "。"),
        "4. 截止日期要依執行順序由早到晚，並平均分配，不要全部擠在最後幾天。",
        "5. 優先級只能是 high、medium、low：關鍵或有先後依賴的任務設為 high。",
    ]
    if budget:
        lines.append(f"6. 所有任務的預估時間加總，盡量不要超過 {budget} 分鐘。")
    lines += [
        "",
        "【輸出格式】",
        "只輸出一個 JSON 物件，不要加任何其他文字，欄位如下：",
        '{"summary": "一兩句話說明整體規劃", "tasks": [{"title": "任務名稱", "description": "簡短說明",'
        ' "priority": "high", "due_date": "YYYY-MM-DD", "estimated_minutes": 60}]}',
        "所有文字使用繁體中文。",
    ]
    return "\n".join(lines)


def available_minutes(target_date: date | None, weekly_hours: int | None, today: date) -> int | None:
    """到期前大約可用的總分鐘數；資料不足時回傳 None。"""
    if not target_date or not weekly_hours:
        return None
    weeks = max((target_date - today).days, 1) / 7
    return math.ceil(weeks * weekly_hours * 60)


def parse_plan(text: str, today: date | None = None, target_date: date | None = None) -> AiPlan:
    """把 AI 回傳的文字轉成 AiPlan；日期超出範圍時調整到範圍內，其他錯誤丟出 PlanError。"""
    today = today or date.today()
    # 有些模型會把 JSON 包在 ```json ... ``` 裡，先拿掉。
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    raw = match.group(1) if match else text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PlanError(f"AI 回傳的不是正確的 JSON：{error.msg}") from error
    try:
        plan = AiPlan.model_validate(data)
    except ValidationError as error:
        first = error.errors()[0]
        place = ".".join(str(part) for part in first["loc"]) or "整體"
        raise PlanError(f"AI 回傳的格式不正確（{place}：{first['msg']}）") from error

    latest = target_date if target_date and target_date >= today else None
    for task in plan.tasks:
        if task.due_date and task.due_date < today:
            task.due_date = today
        if task.due_date and latest and task.due_date > latest:
            task.due_date = latest
    return plan
