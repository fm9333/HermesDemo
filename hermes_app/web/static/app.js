const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");
const healthPill = document.querySelector("#health-pill");
const panelList = document.querySelector("#panel-list");
const panelTitle = document.querySelector("#panel-title");
const refreshPanel = document.querySelector("#refresh-panel");
const panelAction = document.querySelector("#panel-action");
let activePanel = "memory";

const pageToken = document.querySelector('meta[name="hermes-token"]')?.content || "";
const queryToken = new URLSearchParams(window.location.search).get("token") || "";
const bootToken = queryToken || pageToken;
if (bootToken) {
  window.localStorage.setItem("hermes.localToken", bootToken);
}

const panelLabels = {
  memory: "记忆",
  memoryCandidates: "记忆候选",
  reminders: "提醒",
  todos: "待办",
  scenes: "场景",
  sceneFeedback: "反馈",
  signals: "信号",
  opportunities: "机会",
  recommendations: "推荐",
  ideas: "灵感",
  prdDrafts: "PRD",
  weather: "天气",
  wardrobe: "衣橱",
  skills: "技能",
  skillRuns: "技能运行",
  files: "文件",
  images: "图片",
  tools: "工具",
  autonomy: "自治",
  evalRuns: "评测",
  logs: "日志",
};

const panelEndpoints = {
  memory: "/api/memory",
  memoryCandidates: "/api/memory/candidates",
  reminders: "/api/reminders",
  todos: "/api/todos",
  scenes: "/api/scenes",
  sceneFeedback: "/api/scene-feedback",
  signals: "/api/context-signals",
  opportunities: "/api/opportunities",
  recommendations: "/api/recommendations",
  ideas: "/api/ideas",
  prdDrafts: "/api/prd-drafts",
  weather: "/api/weather/cache",
  wardrobe: "/api/wardrobe",
  skills: "/api/skills",
  skillRuns: "/api/skills/runs",
  files: "/api/files",
  images: "/api/images",
  tools: "/api/tools",
  autonomy: "/api/autonomy/zones",
  evalRuns: "/api/eval/runs",
  logs: "/api/logs",
};

const panelActions = {
  opportunities: { label: "生成机会", endpoint: "/api/opportunities/generate" },
  recommendations: { label: "生成推荐", endpoint: "/api/recommendations/generate" },
  evalRuns: { label: "运行评测", endpoint: "/api/eval/suites/autonomy.zone.basic/run" },
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function asJson(value) {
  return escapeHtml(JSON.stringify(value, null, 2));
}

function addMessage(role, body, data) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = `
    <div class="message-meta">${role === "user" ? "You" : "Hermes"}</div>
    <p>${escapeHtml(body)}</p>
  `;

  if (data) {
    const cards = document.createElement("div");
    cards.className = "card-list";

    if (data.cards?.length) {
      data.cards.forEach((card) => {
        cards.insertAdjacentHTML(
          "beforeend",
          `<div class="result-card">
            <p class="card-title">${escapeHtml(card.title || card.type || "Result")}</p>
            <pre>${asJson(card.payload || card)}</pre>
          </div>`
        );
      });
    }

    if (data.task_plan) {
      cards.insertAdjacentHTML(
        "beforeend",
        `<div class="result-card">
          <p class="card-title">Task Plan · ${escapeHtml(data.task_plan.intent)}</p>
          <pre>${asJson(data.task_plan)}</pre>
        </div>`
      );
    }

    if (data.memory_candidates?.length) {
      data.memory_candidates.forEach((candidate) => {
        cards.insertAdjacentHTML(
          "beforeend",
          `<div class="result-card warning">
            <p class="card-title">Memory Candidate</p>
            <pre>${asJson(candidate)}</pre>
          </div>`
        );
      });
    }

    if (data.actions?.length) {
      data.actions.forEach((action) => {
        cards.insertAdjacentHTML(
          "beforeend",
          `<div class="result-card warning" data-action-card="${action.id}">
            <p class="card-title">${escapeHtml(action.action_type)} · ${escapeHtml(action.risk_level)}</p>
            <pre>${asJson(action.payload)}</pre>
            <div class="action-row">
              <button class="action-button" data-confirm="${action.id}">确认执行</button>
              <button class="action-button reject" data-reject="${action.id}">拒绝</button>
            </div>
          </div>`
        );
      });
    }

    if (cards.children.length) {
      article.appendChild(cards);
    }
  }

  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

async function requestJson(url, options = {}) {
  const token = window.localStorage.getItem("hermes.localToken") || "";
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "X-Hermes-Token": token } : {}),
    ...(options.headers || {}),
  };
  const response = await fetch(url, {
    headers,
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

async function sendChat(message) {
  addMessage("user", message);
  const data = await requestJson("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  addMessage("assistant", data.reply, data);
  await loadPanel(activePanel);
}

async function confirmAction(actionId) {
  const data = await requestJson(`/api/actions/${actionId}/confirm`, { method: "POST" });
  addMessage("assistant", `Action 已执行：${data.action.action_type}`, data);
  await loadPanel(activePanel);
}

async function rejectAction(actionId) {
  const data = await requestJson(`/api/actions/${actionId}/reject`, { method: "POST" });
  addMessage("assistant", `Action 已拒绝：${data.action_type || data.id}`);
  await loadPanel(activePanel);
}

async function runPanelAction() {
  const action = panelActions[activePanel];
  if (!action) return;
  const data = await requestJson(action.endpoint, { method: "POST" });
  addMessage("assistant", `${action.label}完成`, { cards: [{ title: action.label, payload: data }] });
  await loadPanel(activePanel);
}

async function dismissRecommendation(recommendationId) {
  const data = await requestJson(`/api/recommendations/${recommendationId}/dismiss`, { method: "POST" });
  addMessage("assistant", `推荐已忽略：${data.title || data.id}`);
  await loadPanel(activePanel);
}

async function recordSceneFeedback(sceneId, rating) {
  const data = await requestJson(`/api/scenes/${sceneId}/feedback`, {
    method: "POST",
    body: JSON.stringify({
      rating,
      reason: rating === "misfire" ? "用户标记误触发" : "用户标记有效",
      payload: { source: "inspector" },
    }),
  });
  addMessage("assistant", `场景反馈已记录：${data.rating}`);
  await loadPanel(activePanel);
}

async function convertIdeaToTodo(ideaId) {
  const data = await requestJson(`/api/ideas/${ideaId}/to-todo`, { method: "POST" });
  addMessage("assistant", `已生成待办：${data.todos.length} 条`);
  await loadPanel("todos");
}

async function convertIdeaToPrd(ideaId) {
  const data = await requestJson(`/api/ideas/${ideaId}/to-prd`, { method: "POST" });
  addMessage("assistant", `PRD 草案已生成：${data.title}`);
  await loadPanel("prdDrafts");
}

async function convertIdeaToScene(ideaId) {
  const data = await requestJson(`/api/ideas/${ideaId}/to-scene`, { method: "POST" });
  addMessage("assistant", `Scene 草案已生成：${data.name}`);
  await loadPanel("scenes");
}

async function createIdeaPreferenceCandidate(ideaId) {
  const data = await requestJson(`/api/ideas/${ideaId}/preference-candidate`, { method: "POST" });
  addMessage("assistant", "灵感偏好候选已生成，确认后写入记忆。", {
    memory_candidates: [data.candidate],
    actions: [data.action],
  });
  await loadPanel("memoryCandidates");
}

async function completeTodo(todoId) {
  const data = await requestJson(`/api/todos/${todoId}/complete`, { method: "POST" });
  addMessage("assistant", `待办已完成：${data.title}`);
  await loadPanel(activePanel);
}

function renderPanelItem(item, panel) {
  let title = item.title || item.key || item.skill_id || item.intent || item.name || item.action_type || item.id;
  if (panel === "reminders") title = item.title;
  if (panel === "ideas") title = item.title;
  const controls = [];
  if (panel === "ideas") {
    controls.push(`<button class="action-button" data-idea-to-todo="${item.id}">转待办</button>`);
    controls.push(`<button class="action-button" data-idea-to-prd="${item.id}">转 PRD</button>`);
    controls.push(`<button class="action-button" data-idea-to-scene="${item.id}">转场景</button>`);
    controls.push(`<button class="action-button" data-idea-preference="${item.id}">记住偏好</button>`);
  }
  if (panel === "todos" && item.status === "open") {
    controls.push(`<button class="action-button" data-complete-todo="${item.id}">完成</button>`);
  }
  if (panel === "scenes") {
    controls.push(`<button class="action-button" data-scene-feedback-positive="${item.id}">有效</button>`);
    controls.push(`<button class="action-button reject" data-scene-feedback-misfire="${item.id}">误触发</button>`);
  }
  if (panel === "recommendations" && item.status === "open") {
    controls.push(`<button class="action-button reject" data-dismiss-recommendation="${item.id}">忽略</button>`);
  }
  return `
    <article class="panel-item">
      <p class="panel-title">${escapeHtml(title || "Item")}</p>
      <pre>${asJson(item)}</pre>
      ${controls.length ? `<div class="action-row">${controls.join("")}</div>` : ""}
    </article>
  `;
}

async function loadPanel(panel) {
  activePanel = panel;
  panelTitle.textContent = panelLabels[panel] || panel;
  document.querySelectorAll(".rail-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.panel === panel);
  });
  const action = panelActions[panel];
  panelAction.hidden = !action;
  if (action) {
    panelAction.textContent = action.label;
    panelAction.title = action.label;
  }

  panelList.innerHTML = `<div class="panel-empty">Loading</div>`;
  const data = await requestJson(panelEndpoints[panel]);
  if (!data.length) {
    panelList.innerHTML = `<div class="panel-empty">No records</div>`;
    return;
  }
  panelList.innerHTML = data.map((item) => renderPanelItem(item, panel)).join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  try {
    await sendChat(message);
  } catch (error) {
    addMessage("assistant", `请求失败：${error.message}`);
  }
});

document.addEventListener("click", async (event) => {
  const confirmId = event.target.dataset?.confirm;
  const rejectId = event.target.dataset?.reject;
  const dismissRecommendationId = event.target.dataset?.dismissRecommendation;
  const positiveSceneId = event.target.dataset?.sceneFeedbackPositive;
  const misfireSceneId = event.target.dataset?.sceneFeedbackMisfire;
  const ideaToTodoId = event.target.dataset?.ideaToTodo;
  const ideaToPrdId = event.target.dataset?.ideaToPrd;
  const ideaToSceneId = event.target.dataset?.ideaToScene;
  const ideaPreferenceId = event.target.dataset?.ideaPreference;
  const completeTodoId = event.target.dataset?.completeTodo;
  const panel = event.target.dataset?.panel;

  try {
    if (confirmId) await confirmAction(confirmId);
    if (rejectId) await rejectAction(rejectId);
    if (dismissRecommendationId) await dismissRecommendation(dismissRecommendationId);
    if (positiveSceneId) await recordSceneFeedback(positiveSceneId, "positive");
    if (misfireSceneId) await recordSceneFeedback(misfireSceneId, "misfire");
    if (ideaToTodoId) await convertIdeaToTodo(ideaToTodoId);
    if (ideaToPrdId) await convertIdeaToPrd(ideaToPrdId);
    if (ideaToSceneId) await convertIdeaToScene(ideaToSceneId);
    if (ideaPreferenceId) await createIdeaPreferenceCandidate(ideaPreferenceId);
    if (completeTodoId) await completeTodo(completeTodoId);
    if (panel) await loadPanel(panel);
  } catch (error) {
    addMessage("assistant", `操作失败：${error.message}`);
  }
});

refreshPanel.addEventListener("click", () => loadPanel(activePanel));
panelAction.addEventListener("click", runPanelAction);

async function boot() {
  try {
    const health = await requestJson("/api/health");
    healthPill.textContent = health.status;
    healthPill.classList.add("ok");
  } catch {
    healthPill.textContent = "offline";
    healthPill.classList.add("fail");
  }
  await loadPanel(activePanel);
}

boot();
