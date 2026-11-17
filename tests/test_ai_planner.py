"""測試提示詞與 AI 回傳內容的檢查；不會真的呼叫 Gemini。"""
from datetime import date
import json
import unittest

from backend.ai_planner import MAX_TASKS, PlanError, available_minutes, build_prompt, parse_plan

TODAY = date(2026, 11, 17)
TARGET = date(2026, 12, 1)


def task(**changes):
    return {"title": "複習第一章", "description": "看講義", "priority": "high",
            "due_date": "2026-11-20", "estimated_minutes": 60, **changes}


def reply(tasks=None, **changes):
    return json.dumps({"summary": "分三階段準備", "tasks": tasks or [task(), task(), task()], **changes},
                      ensure_ascii=False)


class PromptTests(unittest.TestCase):
    def test_prompt_contains_goal_and_rules(self):
        prompt = build_prompt("準備期中考", "範圍第一到五章", TARGET, 7, TODAY)
        for text in ("準備期中考", "範圍第一到五章", "2026-11-17", "2026-12-01", "還有 14 天",
                     "每週可用時間：7 小時", "840 分鐘", "YYYY-MM-DD", "JSON", "繁體中文"):
            self.assertIn(text, prompt)

    def test_prompt_without_optional_fields(self):
        prompt = build_prompt("學吉他", today=TODAY)
        self.assertIn("（未提供）", prompt)
        self.assertIn("希望完成日期：未設定", prompt)
        self.assertIn("每週可用時間：未設定", prompt)

    def test_available_minutes(self):
        self.assertEqual(available_minutes(TARGET, 7, TODAY), 840)
        self.assertEqual(available_minutes(TODAY, 7, TODAY), 60)  # 當天到期至少算一天
        self.assertIsNone(available_minutes(None, 7, TODAY))
        self.assertIsNone(available_minutes(TARGET, None, TODAY))


class ParseTests(unittest.TestCase):
    def test_valid_reply(self):
        plan = parse_plan(reply(), TODAY, TARGET)
        self.assertEqual(plan.summary, "分三階段準備")
        self.assertEqual(len(plan.tasks), 3)
        self.assertEqual(plan.tasks[0].due_date, date(2026, 11, 20))

    def test_code_fence_and_extra_fields(self):
        text = "```json\n" + reply([task(), task(), task(note="多的欄位")]) + "\n```"
        self.assertEqual(len(parse_plan(text, TODAY, TARGET).tasks), 3)

    def test_dates_are_kept_in_range(self):
        tasks = [task(due_date="2026-11-01"), task(due_date="2027-01-01"), task(due_date=None)]
        plan = parse_plan(reply(tasks), TODAY, TARGET)
        self.assertEqual([t.due_date for t in plan.tasks], [TODAY, TARGET, None])

    def test_target_date_already_passed(self):
        plan = parse_plan(reply([task(due_date="2026-11-10"), task(), task()]), TODAY, date(2026, 11, 1))
        self.assertEqual(plan.tasks[0].due_date, TODAY)

    def test_invalid_replies(self):
        cases = {
            "不是 JSON": "好的，以下是任務：1. 複習",
            "缺少 tasks": json.dumps({"summary": "x"}),
            "任務太少": reply([task()]),
            "任務太多": reply([task()] * (MAX_TASKS + 1)),
            "優先級錯誤": reply([task(priority="urgent"), task(), task()]),
            "日期格式錯誤": reply([task(due_date="下週一"), task(), task()]),
            "時間不合理": reply([task(estimated_minutes=0), task(), task()]),
            "空白標題": reply([task(title="  "), task(), task()]),
        }
        for name, text in cases.items():
            with self.subTest(name), self.assertRaises(PlanError):
                parse_plan(text, TODAY, TARGET)

    def test_error_message_points_to_field(self):
        with self.assertRaises(PlanError) as context:
            parse_plan(reply([task(), task(priority="urgent"), task()]), TODAY, TARGET)
        self.assertIn("tasks.1.priority", str(context.exception))


if __name__ == "__main__":
    unittest.main()
