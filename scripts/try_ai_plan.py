"""第六週：實際請 Gemini 拆解目標，檢查回傳的 JSON 是否符合格式。

執行方式：
  python scripts/try_ai_plan.py
  python scripts/try_ai_plan.py "準備多益考試" --description "目標 800 分" --days 30 --hours 6
  python scripts/try_ai_plan.py --show-prompt   # 一併印出送給 AI 的提示詞
  python scripts/try_ai_plan.py --model models/gemini-2.5-flash   # 模型忙碌時換一個
"""
import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.ai_planner import AiPlan, PlanError, available_minutes, build_prompt, parse_plan  # noqa: E402

PRIORITY = {"high": "高", "medium": "中", "low": "低"}

parser = argparse.ArgumentParser(description="測試 AI 任務拆解")
parser.add_argument("title", nargs="?", default="兩週內準備好資料結構期中考")
parser.add_argument("--description", default="範圍是陣列、鏈結串列、堆疊、佇列與樹")
parser.add_argument("--days", type=int, default=14, help="幾天後要完成")
parser.add_argument("--hours", type=int, default=10, help="每週可用幾小時")
parser.add_argument("--model", default="models/gemini-3.8-flash")
parser.add_argument("--show-prompt", action="store_true")
args = parser.parse_args()

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("找不到 GEMINI_API_KEY，請確認 .env 檔案存在且有填入金鑰。")

today = date.today()
target = today + timedelta(days=args.days)
prompt = build_prompt(args.title, args.description, target, args.hours, today)
if args.show_prompt:
    print("===== 提示詞 =====\n" + prompt + "\n")

print(f"使用 {args.model} 拆解「{args.title}」…\n")
client = genai.Client(api_key=api_key)  # 要先存成變數，否則連線會在送出前被關閉
try:
    response = client.models.generate_content(
        model=args.model,
        contents=prompt,
        # 要求模型只回傳符合 AiPlan 結構的 JSON。
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=AiPlan),
    )
except errors.APIError as error:
    if error.code in (429, 503):
        reason = "目前使用人數過多" if error.code == 503 else "已達免費額度上限"
        raise SystemExit(f"AI 模型暫時無法使用（{error.code}，{reason}）。\n"
                         "請稍後再試，或加上 --model models/gemini-2.5-flash 改用其他模型。")
    raise SystemExit(f"呼叫 AI 失敗（{error.code}）：{error.message}")

try:
    plan = parse_plan(response.text, today, target)
except PlanError as error:
    print("格式檢查失敗：", error)
    print("\n原始回傳內容：\n" + response.text)
    raise SystemExit(1)

print("規劃摘要：", plan.summary, "\n")
for number, task in enumerate(plan.tasks, 1):
    due = task.due_date.strftime("%m/%d") if task.due_date else "未定"
    print(f"{number:>2}. [{PRIORITY[task.priority]}] {task.title}（{due}，{task.estimated_minutes} 分鐘）")
    if task.description:
        print(f"    {task.description}")

total = sum(task.estimated_minutes for task in plan.tasks)
budget = available_minutes(target, args.hours, today)
print(f"\n共 {len(plan.tasks)} 個任務，預估 {total} 分鐘；可用時間約 {budget} 分鐘。")
print("格式檢查通過 ✓")
