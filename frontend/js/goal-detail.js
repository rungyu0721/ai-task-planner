// 目標詳情：顯示目標與任務，並提供任務的新增、編輯、刪除、標記完成，以及目標的編輯、刪除。
import {
  api, daysUntil, escapeHtml, fillForm, formatDate, PRIORITY, progressOf, readForm, showToast, STATUS,
} from './api.js';

const goalId = Number(new URLSearchParams(location.search).get('id'));
const taskList = document.getElementById('task-list');
const taskDialog = document.getElementById('task-dialog');
const taskForm = taskDialog.querySelector('form');
const goalDialog = document.getElementById('goal-dialog');
const goalForm = goalDialog.querySelector('form');

let goal = null;
let tasks = [];
let filter = 'all';
let editingTaskId = null; // null 表示新增任務

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'todo', label: '待辦' },
  { key: 'in_progress', label: '進行中' },
  { key: 'completed', label: '已完成' },
];

async function load() {
  if (!goalId) {
    location.replace('goals.html');
    return;
  }
  try {
    [goal, tasks] = await Promise.all([api(`/goals/${goalId}`), api(`/goals/${goalId}/tasks`)]);
    render();
  } catch (error) {
    const box = document.getElementById('load-error');
    box.innerHTML = `<b>載入失敗</b>${escapeHtml(error.message)} <a href="goals.html" class="app-link">回到我的目標</a>`;
    box.hidden = false;
    document.getElementById('goal-header').hidden = true;
    document.querySelector('[data-action="add-task"]').hidden = true;
    taskList.hidden = true;
  }
}

function render() {
  document.title = `${goal.title}｜智慧任務規劃`;
  document.getElementById('goal-title').textContent = goal.title;
  document.getElementById('goal-description').textContent = goal.description;

  const meta = [];
  if (goal.target_date) {
    const days = daysUntil(goal.target_date);
    const remain = days > 0 ? `還有 ${days} 天` : days === 0 ? '今天到期' : `已超過 ${-days} 天`;
    meta.push(`目標期限 ${formatDate(goal.target_date)} · ${remain}`);
  } else {
    meta.push('未設定期限');
  }
  if (goal.weekly_hours) meta.push(`每週 ${goal.weekly_hours} 小時`);
  meta.push(`建立於 ${formatDate(goal.created_at.slice(0, 10), true)}`);
  document.getElementById('goal-meta').textContent = meta.join(' · ');

  const { done, total, percent } = progressOf(tasks);
  document.getElementById('goal-bar').style.width = `${percent}%`;
  document.getElementById('goal-progress').textContent = `${done} / ${total} · ${percent}%`;

  document.getElementById('status-tabs').innerHTML = FILTERS.map(({ key, label }) => {
    const count = key === 'all' ? tasks.length : tasks.filter(task => task.status === key).length;
    const on = key === filter;
    return `<button type="button" role="tab" aria-selected="${on}" class="tp-tab app-tab${on ? ' tp-tab--on' : ''}"
      data-filter="${key}">${label} ${count}</button>`;
  }).join('');

  const shown = filter === 'all' ? tasks : tasks.filter(task => task.status === filter);
  taskList.innerHTML = shown.length
    ? shown.map(taskRow).join('')
    : `<p class="tp-muted app-empty">${tasks.length ? '這個分類沒有任務。' : '還沒有任務，按「＋ 新增任務」開始規劃。'}</p>`;
}

function taskRow(task) {
  const done = task.status === 'completed';
  const status = STATUS[task.status];
  const priority = PRIORITY[task.priority];
  const meta = [];
  if (task.due_date) meta.push(`<span class="tp-due">${formatDate(task.due_date, true)}</span>`);
  if (task.estimated_minutes) meta.push(`<span>預估 ${task.estimated_minutes} 分鐘</span>`);
  return `<div class="tp-task${done ? ' tp-task--done' : ''}" data-id="${task.id}">
    <button type="button" class="tp-check app-check${done ? ' tp-check--on' : ''}" data-action="toggle"
      aria-label="${done ? '取消完成' : '標記完成'}：${escapeHtml(task.title)}" aria-pressed="${done}"></button>
    <div><div class="tp-task__title">${escapeHtml(task.title)}</div>
      ${task.description ? `<div class="tp-sm tp-muted">${escapeHtml(task.description)}</div>` : ''}
      ${meta.length ? `<div class="tp-task__meta">${meta.join('')}</div>` : ''}</div>
    <div class="tp-task__side">
      <span class="tp-chip tp-chip--${status.chip}">${status.label}</span>
      <span class="tp-prio tp-prio--${priority.cls}">${priority.label}</span>
      <button type="button" class="tp-btn tp-btn--ghost tp-btn--sm" data-action="edit-task">編輯</button>
      <button type="button" class="tp-btn tp-btn--ghost tp-btn--sm app-danger" data-action="delete-task">刪除</button>
    </div></div>`;
}

// ===== 操作 =====

document.addEventListener('click', async event => {
  const tab = event.target.closest('[data-filter]');
  if (tab) {
    filter = tab.dataset.filter;
    render();
    return;
  }
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const taskId = Number(button.closest('[data-id]')?.dataset.id);
  const task = tasks.find(item => item.id === taskId);
  const actions = {
    'toggle': () => toggleTask(task),
    'edit-task': () => openTaskDialog(task),
    'delete-task': () => deleteTask(task),
    'add-task': () => openTaskDialog(null),
    'edit-goal': () => openGoalDialog(),
    'delete-goal': () => deleteGoal(),
  };
  await actions[button.dataset.action]?.();
});

async function toggleTask(task) {
  const status = task.status === 'completed' ? 'todo' : 'completed';
  try {
    replaceTask(await api(`/tasks/${task.id}`, { method: 'PATCH', body: { status } }));
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteTask(task) {
  if (!confirm(`確定要刪除任務「${task.title}」嗎？此操作無法復原。`)) return;
  try {
    await api(`/tasks/${task.id}`, { method: 'DELETE' });
    tasks = tasks.filter(item => item.id !== task.id);
    render();
    showToast('已刪除任務');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteGoal() {
  const message = `確定要刪除目標「${goal.title}」嗎？\n它的 ${tasks.length} 個任務也會一起刪除，此操作無法復原。`;
  if (!confirm(message)) return;
  try {
    await api(`/goals/${goal.id}`, { method: 'DELETE' });
    location.href = 'goals.html';
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function replaceTask(updated) {
  tasks = tasks.map(item => (item.id === updated.id ? updated : item));
  render();
}

// ===== 對話框 =====

function openTaskDialog(task) {
  editingTaskId = task?.id ?? null;
  document.getElementById('task-dialog-title').textContent = task ? '編輯任務' : '新增任務';
  // 新增時狀態固定為待辦（後端新增 API 不接受狀態欄位）。
  const statusField = document.getElementById('task-status-field');
  statusField.hidden = !task;
  taskForm.elements.status.disabled = !task;
  fillForm(taskForm, task ?? { priority: 'medium', status: 'todo' });
  clearErrors(taskForm);
  taskDialog.showModal();
}

function openGoalDialog() {
  fillForm(goalForm, goal);
  clearErrors(goalForm);
  goalDialog.showModal();
}

taskForm.addEventListener('submit', async event => {
  event.preventDefault();
  if (!checkTitle(taskForm)) return;
  const body = readForm(taskForm);
  try {
    if (editingTaskId) {
      replaceTask(await api(`/tasks/${editingTaskId}`, { method: 'PATCH', body }));
      showToast('已更新任務');
    } else {
      // 新任務排在最後面。
      body.sort_order = tasks.reduce((max, item) => Math.max(max, item.sort_order + 1), 0);
      tasks.push(await api(`/goals/${goalId}/tasks`, { method: 'POST', body }));
      render();
      showToast('已新增任務');
    }
    taskDialog.close();
  } catch (error) {
    showToast(error.message, 'error');
  }
});

goalForm.addEventListener('submit', async event => {
  event.preventDefault();
  if (!checkTitle(goalForm)) return;
  try {
    goal = await api(`/goals/${goal.id}`, { method: 'PATCH', body: readForm(goalForm) });
    render();
    goalDialog.close();
    showToast('已更新目標');
  } catch (error) {
    showToast(error.message, 'error');
  }
});

for (const dialog of [taskDialog, goalDialog]) {
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
}

function checkTitle(form) {
  const input = form.elements.title;
  const ok = input.value.trim() !== '';
  input.classList.toggle('tp-input--error', !ok);
  if (!ok) input.focus();
  return ok;
}

function clearErrors(form) {
  form.querySelectorAll('.tp-input--error').forEach(input => input.classList.remove('tp-input--error'));
}

load();
