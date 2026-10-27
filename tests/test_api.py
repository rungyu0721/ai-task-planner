"""以臨時資料庫測試真實 HTTP API，不接觸開發資料。"""
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import sqlite3
from tempfile import TemporaryDirectory
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn

from backend.database import connect
from backend.main import create_app


@contextmanager
def running_app(db_path):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    address = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(create_app(db_path), log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("測試伺服器啟動失敗")
        yield address
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "test.db"
        self.server = running_app(self.db_path)
        self.base = self.server.__enter__()
        self.addCleanup(self.server.__exit__, None, None, None)

    def request(self, path, body=None, method=None):
        request = Request(self.base + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={"Content-Type": "application/json"}, method=method)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            content = response.read()
            return response.status, json.loads(content) if "application/json" in response.headers.get("Content-Type", "") else content

    def create_goal(self, title="期末專題"):
        status, goal = self.request("/api/goals", {"title": title, "target_date": "2026-11-19", "weekly_hours": 8})
        self.assertEqual(status, 201)
        return goal

    def test_create_query_and_persistence(self):
        self.assertEqual(self.request("/api/goals"), (200, []))
        goal = self.create_goal("  期末專題  ")
        self.assertEqual(goal["title"], "期末專題")
        self.assertEqual(goal["status"], "active")
        self.assertTrue(goal["created_at"].endswith("Z"))
        self.assertEqual(self.request(f'/api/goals/{goal["id"]}'), (200, goal))
        path = f'/api/goals/{goal["id"]}/tasks'
        self.assertEqual(self.request(path), (200, []))
        status, task = self.request(path, {"title": "整理需求", "priority": "high", "sort_order": 2})
        self.assertEqual(status, 201)
        self.assertEqual(task["goal_id"], goal["id"])
        self.assertEqual(task["status"], "todo")
        self.assertEqual(task["source"], "manual")
        self.assertIsNone(task["completed_at"])
        self.request(path, {"title": "先做這項", "sort_order": 1})
        self.assertEqual(self.request(path)[1][0]["title"], "先做這項")
        self.assertEqual(self.request(f'/api/tasks/{task["id"]}'), (200, task))
        # 重新建立應用程式並啟動，資料仍存在。
        with running_app(self.db_path) as second_base:
            with urlopen(second_base + f'/api/tasks/{task["id"]}') as response:
                self.assertEqual(json.load(response), task)

    def test_validation_and_not_found(self):
        for body in ({"title": "   "}, {"title": "x", "target_date": "2026-02-30"},
                     {"title": "x", "weekly_hours": 0}, {"title": "x", "weekly_hours": True},
                     {"title": "x", "id": 99}):
            with self.subTest(body=body):
                self.assertEqual(self.request("/api/goals", body)[0], 422)
        goal = self.create_goal()
        path = f'/api/goals/{goal["id"]}/tasks'
        for body in ({"title": ""}, {"title": "x", "priority": "urgent"},
                     {"title": "x", "estimated_minutes": -1}, {"title": "x", "sort_order": -1},
                     {"title": "x", "due_date": "bad-date"}, {"title": "x", "source": "ai"}):
            with self.subTest(body=body):
                self.assertEqual(self.request(path, body)[0], 422)
        for path in ("/api/goals/999", "/api/tasks/999", "/api/goals/999/tasks"):
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/api/goals/999/tasks", {"title": "孤立任務"})[0], 404)
        self.assertEqual(self.request("/api/goals/0")[0], 422)

    def test_isolation_pagination_and_foreign_keys(self):
        first, second = self.create_goal("一"), self.create_goal("二")
        self.assertEqual(self.request("/api/goals?limit=1")[1][0]["id"], second["id"])
        self.assertEqual(self.request("/api/goals?limit=1&offset=1")[1][0]["id"], first["id"])
        self.assertEqual(self.request("/api/goals?limit=101")[0], 422)
        self.request(f'/api/goals/{first["id"]}/tasks', {"title": "任務"})
        self.assertEqual(self.request(f'/api/goals/{second["id"]}/tasks'), (200, []))
        connection = connect(self.db_path)
        try:
            with self.assertRaises(sqlite3.IntegrityError), connection:
                connection.execute("INSERT INTO tasks (goal_id, title, created_at, updated_at) VALUES (999, 'x', 'now', 'now')")
            with connection:
                connection.execute("DELETE FROM goals WHERE id = ?", (first["id"],))
            self.assertEqual(connection.execute("SELECT count(*) FROM tasks").fetchone()[0], 0)
        finally:
            connection.close()

    def test_update_goal(self):
        goal = self.create_goal()
        path = f'/api/goals/{goal["id"]}'
        status, updated = self.request(path, {"title": " 新名稱 ", "target_date": None}, "PATCH")
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "新名稱")
        self.assertIsNone(updated["target_date"])
        self.assertEqual(updated["weekly_hours"], 8)  # 沒傳的欄位不變
        self.assertGreater(updated["updated_at"], goal["updated_at"])
        self.assertEqual(self.request(path, {"status": "archived"}, "PATCH")[1]["status"], "archived")
        for body in ({"title": None}, {"title": " "}, {"status": "done"}, {"weekly_hours": 0}, {"id": 5}):
            with self.subTest(body=body):
                self.assertEqual(self.request(path, body, "PATCH")[0], 422)
        self.assertEqual(self.request("/api/goals/999", {"title": "x"}, "PATCH")[0], 404)

    def test_update_and_complete_task(self):
        goal = self.create_goal()
        _, task = self.request(f'/api/goals/{goal["id"]}/tasks', {"title": "任務", "due_date": "2026-11-01"})
        path = f'/api/tasks/{task["id"]}'
        status, updated = self.request(path, {"priority": "high", "estimated_minutes": 60}, "PATCH")
        self.assertEqual(status, 200)
        self.assertEqual((updated["priority"], updated["estimated_minutes"]), ("high", 60))
        self.assertEqual(updated["due_date"], "2026-11-01")
        # 標記完成會記錄完成時間；重複標記不覆蓋；重新開啟則清除。
        completed = self.request(path, {"status": "completed"}, "PATCH")[1]
        self.assertIsNotNone(completed["completed_at"])
        again = self.request(path, {"status": "completed", "title": "改名"}, "PATCH")[1]
        self.assertEqual(again["completed_at"], completed["completed_at"])
        reopened = self.request(path, {"status": "todo"}, "PATCH")[1]
        self.assertIsNone(reopened["completed_at"])
        for body in ({"status": "done"}, {"priority": None}, {"sort_order": -1}, {"goal_id": 2}, {"source": "ai"}):
            with self.subTest(body=body):
                self.assertEqual(self.request(path, body, "PATCH")[0], 422)
        self.assertEqual(self.request("/api/tasks/999", {"title": "x"}, "PATCH")[0], 404)

    def test_delete_task_and_goal(self):
        goal = self.create_goal()
        tasks_path = f'/api/goals/{goal["id"]}/tasks'
        _, first = self.request(tasks_path, {"title": "一"})
        self.request(tasks_path, {"title": "二"})
        self.assertEqual(self.request(f'/api/tasks/{first["id"]}', method="DELETE")[0], 204)
        self.assertEqual(self.request(f'/api/tasks/{first["id"]}')[0], 404)
        self.assertEqual(len(self.request(tasks_path)[1]), 1)
        self.assertEqual(self.request(f'/api/tasks/{first["id"]}', method="DELETE")[0], 404)
        # 刪除目標時，其任務一併刪除。
        self.assertEqual(self.request(f'/api/goals/{goal["id"]}', method="DELETE")[0], 204)
        self.assertEqual(self.request(f'/api/goals/{goal["id"]}')[0], 404)
        self.assertEqual(self.request(tasks_path)[0], 404)
        self.assertEqual(self.request("/api/goals/999", method="DELETE")[0], 404)

    def test_existing_pages_and_api_docs(self):
        for path in ("/", "/docs", "/static/pages/dashboard.html", "/static/css/style.css", "/api/hello"):
            self.assertEqual(self.request(path)[0], 200)
        paths = self.request("/openapi.json")[1]["paths"]
        self.assertIn("/api/goals/{goal_id}/tasks", paths)


if __name__ == "__main__":
    unittest.main()
