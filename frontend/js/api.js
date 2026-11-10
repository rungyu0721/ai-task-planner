// 前端共用工具：呼叫後端 API、顯示提示訊息、表單讀寫與資料格式化。

export async function api(path, { method = 'GET', body } = {}) {
  let response;
  try {
    response = await fetch('/api' + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error('無法連線到伺服器，請確認後端已啟動。');
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(response.status, data));
  return data;
}

function errorMessage(status, data) {
  if (status === 404) return data?.detail || '找不到資料，可能已被刪除。';
  if (status === 422) return '輸入的資料格式不正確，請檢查後再試一次。';
  return '伺服器發生錯誤，請稍後再試。';
}

// 畫面下方的提示訊息，幾秒後自動消失。
let toastTimer;
export function showToast(message, type = 'ok') {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.setAttribute('role', 'status');
    document.body.append(toast);
  }
  toast.textContent = message;
  toast.className = `tp-toast app-toast app-toast--${type}`;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 3500);
}

// 使用者輸入的文字要先跳脫，避免被當成 HTML 執行。
export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

export const STATUS = {
  todo: { label: '待辦', chip: 'todo' },
  in_progress: { label: '進行中', chip: 'doing' },
  completed: { label: '已完成', chip: 'done' },
};

export const PRIORITY = {
  high: { label: '高', cls: 'high' },
  medium: { label: '中', cls: 'mid' },
  low: { label: '低', cls: 'low' },
};

// '2026-11-19' → '2026/11/19'；short 為 true 時 → '11/19'
export function formatDate(value, short = false) {
  if (!value) return '';
  const [year, month, day] = value.slice(0, 10).split('-');
  return short ? `${month}/${day}` : `${year}/${month}/${day}`;
}

// 今天（使用者本地時間）到指定日期還有幾天。
export function daysUntil(value) {
  const [year, month, day] = value.split('-').map(Number);
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.round((new Date(year, month - 1, day) - start) / 86400000);
}

// 讀取表單欄位：數字與日期留空時送 null，文字送字串。
export function readForm(form) {
  const body = {};
  for (const field of form.elements) {
    if (!field.name || field.disabled) continue;
    if (field.type === 'number') body[field.name] = field.value === '' ? null : Number(field.value);
    else if (field.type === 'date') body[field.name] = field.value || null;
    else body[field.name] = field.value;
  }
  return body;
}

export function fillForm(form, data) {
  for (const field of form.elements) {
    if (field.name) field.value = data[field.name] ?? '';
  }
}

export function progressOf(tasks) {
  const done = tasks.filter(task => task.status === 'completed').length;
  const percent = tasks.length === 0 ? 0 : Math.round((done / tasks.length) * 100);
  return { done, total: tasks.length, percent };
}
