// 我的目標：列出所有目標與各自的完成進度。
import { api, escapeHtml, formatDate, isOverdue, progressOf } from './api.js';

const list = document.getElementById('goal-list');

const STATUS_LABEL = { active: '進行中', completed: '已完成', archived: '已封存' };

async function load() {
  try {
    const goals = await api('/goals');
    if (goals.length === 0) {
      list.innerHTML = `<section class="tp-card app-empty">
        <p>還沒有任何目標。</p>
        <a href="new-goal.html" class="tp-btn tp-btn--primary">建立第一個目標</a></section>`;
      return;
    }
    // 目標數量不多，直接逐一取得任務來計算進度。
    const taskLists = await Promise.all(goals.map(goal => api(`/goals/${goal.id}/tasks`)));
    list.innerHTML = goals.map((goal, i) => goalCard(goal, taskLists[i])).join('');
  } catch (error) {
    list.innerHTML = `<div class="tp-alert tp-alert--error"><b>載入失敗</b>${escapeHtml(error.message)}</div>`;
  }
}

function goalCard(goal, tasks) {
  const { done, total, percent } = progressOf(tasks);
  const deadline = goal.target_date ? `目標期限 ${formatDate(goal.target_date)}` : '未設定期限';
  const overdue = tasks.filter(isOverdue).length;
  const overdueNote = overdue ? ` · <span class="app-overdue-note">${overdue} 個任務逾期</span>` : '';
  return `<a class="tp-card app-goal-card" href="goal-detail.html?id=${goal.id}">
    <div class="tp-row" style="justify-content:space-between">
      <h2 class="tp-h2">${escapeHtml(goal.title)}</h2>
      ${goal.status === 'active' ? '' : `<span class="tp-chip tp-chip--todo">${STATUS_LABEL[goal.status]}</span>`}
    </div>
    <p class="tp-sm tp-muted" style="margin:4px 0 12px">${deadline}${overdueNote}</p>
    <div class="tp-row" style="flex-wrap:nowrap;gap:16px">
      <div class="tp-bar" style="flex:1"><i style="width:${percent}%"></i></div>
      <span class="tp-sm app-num">${done} / ${total} · ${percent}%</span>
    </div></a>`;
}

load();
