// 新增目標：手動建立目標並存入資料庫；AI 拆解於第 6～8 週串接。
import { api, readForm, showToast } from './api.js';

const form = document.getElementById('goal-form');
const titleInput = form.elements.title;
const titleError = document.getElementById('title-error');

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!titleInput.value.trim()) {
    titleInput.classList.add('tp-input--error');
    titleError.hidden = false;
    titleInput.focus();
    return;
  }
  const submitButton = form.querySelector('[type="submit"]');
  submitButton.disabled = true;
  try {
    const goal = await api('/goals', { method: 'POST', body: readForm(form) });
    location.href = `goal-detail.html?id=${goal.id}`;
  } catch (error) {
    showToast(error.message, 'error');
    submitButton.disabled = false;
  }
});

titleInput.addEventListener('input', () => {
  titleInput.classList.remove('tp-input--error');
  titleError.hidden = true;
});

document.getElementById('ai-button').addEventListener('click', () => {
  showToast('AI 拆解功能將在後續週次串接，目前請先使用「手動建立」。');
});
