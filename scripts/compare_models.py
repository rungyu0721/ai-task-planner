"""用同一個目標測試多個 Gemini 模型，比較回答品質與速度。

執行方式：python scripts/compare_models.py
"""
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 想比較哪些模型就寫在這裡
MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-3.5-flash",
    "models/gemini-3.8-flash",
]

PROMPT = "請把「四週內完成資料分析課程期末專題」拆成 5 個具體任務，每個任務一行，包含任務名稱和一句說明。"

for model in MODELS:
    start = time.time()
    try:
        response = client.models.generate_content(model=model, contents=PROMPT)
        print(f"===== {model}（{time.time() - start:.1f} 秒）=====")
        print(response.text)
    except Exception as e:
        print(f"===== {model} 失敗：{e}")
    print()
