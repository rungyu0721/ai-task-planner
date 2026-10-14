// 呼叫後端測試 API，確認前後端有連通
async function checkBackend() {
  const status = document.getElementById("status");
  try {
    const res = await fetch("/api/hello");
    const data = await res.json();
    status.textContent = "✅ " + data.message;
  } catch (err) {
    status.textContent = "❌ 無法連線到後端";
  }
}

checkBackend();
