# 智慧任務規劃 — 前端版面

## 怎麼打開
1. VS Code：檔案 → 開啟資料夾 → 選這個 `task-planner-ui` 資料夾
2. 安裝擴充功能 **Live Server**，在 `index.html` 按右鍵 →「Open with Live Server」
3. 瀏覽器會打開首頁，點左側選單、「新增目標」→「AI 幫我拆解」→「確認並儲存」可以走一遍流程

## 資料夾
- `css/tokens.css`：顏色、間距、圓角等變數（淺色／深色）
- `css/style.css`：所有元件樣式，class 都是 `tp-` 開頭
- `pages/`：六個畫面（dashboard、new-goal、ai-preview、goal-detail、progress、mobile）
- `tokens.json`：設計 token 原始資料
- `設計規範.md`：配色、字體、版面規則說明

## 切換深色模式
把頁面 `<html data-theme="light">` 改成 `data-theme="dark"`。

## 注意
目前是靜態版面，資料都是寫死的示意內容。接後端時，把任務列表改成用 JavaScript 從 API 拿資料再產生 `tp-task` 元素即可。
