"""測試 Gemini API Key 是否可以使用。

執行方式：python scripts/test_gemini.py
"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("找不到 GEMINI_API_KEY，請確認 .env 檔案存在且有填入金鑰。")

client = genai.Client(api_key=api_key)

# 列出可用的 Flash 模型（速度快、免費額度較多）
flash_models = [
    m.name for m in client.models.list()
    if "flash" in m.name and "generateContent" in (m.supported_actions or [])
]
print("可用的 Flash 模型：")
for name in flash_models:
    print("  -", name)

model = flash_models[0]
print(f"\n使用 {model} 測試…")
response = client.models.generate_content(
    model=model,
    contents="請把「兩週內準備好期中考」拆成 3 個具體任務，用條列式回答。",
)
print(response.text)
