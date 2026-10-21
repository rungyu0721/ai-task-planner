// 第二週只展示介面與頁面動線，不呼叫 AI 或寫入資料。
const backendStatus = document.getElementById('backend-status');
if (backendStatus) {
  fetch('/api/hello')
    .then(response => {
      if (!response.ok) throw new Error('Backend unavailable');
      return response.json();
    })
    .then(() => { backendStatus.textContent = '後端連線正常'; })
    .catch(() => { backendStatus.textContent = '後端未連線，請透過 FastAPI 網址開啟。'; });
}

const notice = document.createElement('div');
notice.className = 'tp-toast tp-prototype-message';
notice.setAttribute('role', 'status');
notice.hidden = true;
notice.style.display = 'none';
document.body.append(notice);
let noticeTimer;
function showPrototypeNotice() {
  notice.textContent = '目前為介面示意，此操作尚未串接資料儲存或 AI。';
  notice.hidden = false;
  notice.style.display = 'block';
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.hidden = true;
    notice.style.display = 'none';
  }, 3500);
}

document.addEventListener('click', event => {
  const placeholder = event.target.closest('button, a[href="#"]');
  if (!placeholder) return;
  event.preventDefault();
  showPrototypeNotice();
});

// 手機可橫向查看任務草稿，避免固定欄寬把整個頁面撐開。
if (location.pathname.endsWith('/ai-preview.html')) {
  document.querySelector('.tp-grid-side > section')?.classList.add('tp-prototype-table');
}
