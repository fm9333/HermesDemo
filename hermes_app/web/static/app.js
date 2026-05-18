const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");
const healthPill = document.querySelector("#health-pill");
const panelList = document.querySelector("#panel-list");
const panelTitle = document.querySelector("#panel-title");
const refreshPanel = document.querySelector("#refresh-panel");
let activePanel = "memory";

const pageToken = document.querySelector('meta[name="hermes-token"]')?.content || "";
const queryToken = new URLSearchParams(window.location.search).get("token") || "";
const bootToken = queryToken || pageToken;
if (bootToken) {
  window.localStorage.setItem("hermes.localToken", bootToken);
}

const panelLabels = {
  memory: "记忆",
  reminders: "提醒",
  ideas: "灵感",
  weather: "天气",
  wardrobe: "衣橱",
  skills: "技能",
  logs: "日志",
};

const panelEndpoints = {
  memory: "/api/memory",
  reminders: "/api/reminders",
  ideas: "/api/ideas",
  weather: "/api/weather/cache",
  wardrobe: "/api/wardrobe",
  skills: "/api/skills",
  logs: "/api/logs",
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

function renderPanelItem(item, panel) {
  let title = item.title || item.key || item.skill_id || item.intent || item.name || item.action_type || item.id;
  if (panel === "reminders") title = item.title;
  if (panel === "ideas") title = item.title;
  return `
    <article class="panel-item">
      <p class="panel-title">${escapeHtml(title || "Item")}</p>
      <pre>${asJson(item)}</pre>
    </article>
  `;
}

async function loadPanel(panel) {
  activePanel = panel;
  panelTitle.textContent = panelLabels[panel] || panel;
  document.querySelectorAll(".rail-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.panel === panel);
  });

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
  const panel = event.target.dataset?.panel;

  try {
    if (confirmId) await confirmAction(confirmId);
    if (rejectId) await rejectAction(rejectId);
    if (panel) await loadPanel(panel);
  } catch (error) {
    addMessage("assistant", `操作失败：${error.message}`);
  }
});

refreshPanel.addEventListener("click", () => loadPanel(activePanel));

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
