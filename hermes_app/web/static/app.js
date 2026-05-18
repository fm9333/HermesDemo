const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#chat-input");
const healthPill = document.querySelector("#health-pill");
const panelList = document.querySelector("#panel-list");
const panelTitle = document.querySelector("#panel-title");
const refreshPanel = document.querySelector("#refresh-panel");
const panelAction = document.querySelector("#panel-action");
let activePanel = "homeCards";

const pageToken = document.querySelector('meta[name="hermes-token"]')?.content || "";
const queryToken = new URLSearchParams(window.location.search).get("token") || "";
const bootToken = queryToken || pageToken;
if (bootToken) {
  window.localStorage.setItem("hermes.localToken", bootToken);
}

const panelLabels = {
  homeCards: "\u9996\u9875",
  memory: "记忆",
  memoryCandidates: "记忆候选",
  reminders: "提醒",
  todos: "待办",
  scenes: "场景",
  sceneFeedback: "反馈",
  signals: "信号",
  opportunities: "机会",
  recommendations: "推荐",
  proactive: "主动",
  triggerRuns: "触发",
  ideas: "灵感",
  prdDrafts: "PRD",
  weeklyReviews: "\u590d\u76d8",
  weather: "天气",
  news: "\u65b0\u95fb",
  maps: "\u5730\u56fe",
  wardrobe: "衣橱",
  skills: "技能",
  personalSkills: "个人技能",
  skillPatches: "技能补丁",
  llmProviders: "模型",
  prompts: "提示词",
  llmCalls: "模型调用",
  skillRuns: "技能运行",
  files: "文件",
  images: "图片",
  tools: "工具",
  yellowQueue: "确认",
  autonomy: "自治",
  redZone: "红区",
  evalRuns: "评测",
  growthLog: "成长",
  settings: "设置",
  databaseMigrations: "\u8fc1\u79fb",
  runtimeRecovery: "\u6062\u590d",
  updates: "\u66f4\u65b0",
  performance: "\u6027\u80fd",
  providers: "集成",
  backups: "\u5907\u4efd",
  exports: "\u5bfc\u51fa",
  logs: "日志",
};

const panelEndpoints = {
  homeCards: "/api/home/cards",
  memory: "/api/memory",
  memoryCandidates: "/api/memory/candidates",
  reminders: "/api/reminders",
  todos: "/api/todos",
  scenes: "/api/scenes",
  sceneFeedback: "/api/scene-feedback",
  signals: "/api/context-signals",
  opportunities: "/api/opportunities",
  recommendations: "/api/recommendations",
  proactive: "/api/proactive/suggestions",
  triggerRuns: "/api/triggers/history",
  ideas: "/api/ideas",
  prdDrafts: "/api/prd-drafts",
  weeklyReviews: "/api/weekly-reviews",
  weather: "/api/weather/cache",
  news: "/api/news",
  maps: "/api/maps/places",
  wardrobe: "/api/wardrobe",
  skills: "/api/skills",
  personalSkills: "/api/personal-skills",
  skillPatches: "/api/personal-skill-patches",
  llmProviders: "/api/llm/providers",
  prompts: "/api/prompts",
  llmCalls: "/api/llm/calls",
  skillRuns: "/api/skills/runs",
  files: "/api/files",
  images: "/api/images",
  tools: "/api/tools",
  yellowQueue: "/api/yellow-zone/pending",
  autonomy: "/api/autonomy/zones",
  redZone: "/api/red-zone/rules",
  evalRuns: "/api/eval/runs",
  growthLog: "/api/growth-log",
  settings: "/api/settings",
  databaseMigrations: "/api/database/migrations",
  runtimeRecovery: "/api/runtime/recovery",
  updates: "/api/updates/status",
  performance: "/api/performance/indexes",
  providers: "/api/providers",
  backups: "/api/backups",
  exports: "/api/exports",
  logs: "/api/logs",
};

const panelActions = {
  weeklyReviews: { label: "\u751f\u6210\u590d\u76d8", endpoint: "/api/weekly-reviews/generate" },
  news: { label: "\u5237\u65b0\u65b0\u95fb", endpoint: "/api/news/refresh" },
  maps: { label: "\u641c\u7d22\u5730\u70b9", endpoint: "/api/maps/search" },
  backups: { label: "\u521b\u5efa\u5907\u4efd", endpoint: "/api/backups" },
  exports: { label: "\u521b\u5efa\u5bfc\u51fa", endpoint: "/api/exports" },
  updates: { label: "\u68c0\u67e5\u66f4\u65b0", endpoint: "/api/updates/check" },
  opportunities: { label: "生成机会", endpoint: "/api/opportunities/generate" },
  recommendations: { label: "生成推荐", endpoint: "/api/recommendations/generate" },
  triggerRuns: { label: "运行触发", endpoint: "/api/triggers/run" },
  evalRuns: { label: "运行评测", endpoint: "/api/eval/suites/autonomy.zone.basic/run" },
  llmProviders: { label: "添加模型", endpoint: "/api/llm/providers" },
  personalSkills: { label: "新建草案", endpoint: "/api/personal-skills/drafts" },
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
  const options = { method: "POST" };
  if (activePanel === "maps") {
    const query = window.prompt("\u641c\u7d22\u5730\u70b9");
    if (!query?.trim()) return;
    options.body = JSON.stringify({ query: query.trim() });
  }
  if (activePanel === "llmProviders") {
    const name = window.prompt("模型名称", "OpenAI Compatible");
    if (!name?.trim()) return;
    const baseUrl = window.prompt("Base URL", "https://api.openai.com/v1");
    if (!baseUrl?.trim()) return;
    const model = window.prompt("模型 ID，例如你服务商提供的 model 名称");
    if (!model?.trim()) return;
    const apiKey = window.prompt("API Key，本地保存且界面不会回显完整密钥；本地模型可留空", "");
    options.body = JSON.stringify({
      name: name.trim(),
      provider_type: baseUrl.includes("127.0.0.1") || baseUrl.includes("localhost")
        ? "local_openai_compatible"
        : "openai_compatible",
      base_url: baseUrl.trim(),
      model: model.trim(),
      api_key: apiKey || "",
      is_default: true,
    });
  }
  if (activePanel === "personalSkills") {
    const title = window.prompt("个人技能名称");
    if (!title?.trim()) return;
    const description = window.prompt("技能说明", "从重复任务中沉淀的个人技能草案");
    const promptTemplate = window.prompt("技能提示词", "请按用户偏好稳定输出结构化结果");
    if (!promptTemplate?.trim()) return;
    options.body = JSON.stringify({
      title: title.trim(),
      description: description || "",
      prompt_template: promptTemplate.trim(),
      autonomy_zone: "green",
      output_contract: { format: "json", required: ["title"] },
    });
  }
  const data = await requestJson(action.endpoint, options);
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

async function rollbackGrowthLog(logId) {
  const data = await requestJson(`/api/growth-log/${logId}/rollback`, { method: "POST" });
  addMessage("assistant", `优化已回滚：${data.title}`);
  await loadPanel(activePanel);
}

async function updateSetting(key, rawValue) {
  const value = rawValue === "true" ? true : rawValue === "false" ? false : rawValue;
  const data = await requestJson(`/api/settings/${key}`, {
    method: "PATCH",
    body: JSON.stringify({ value }),
  });
  addMessage("assistant", `设置已更新：${data.key}`);
  await loadPanel(activePanel);
}

async function setProviderStatus(providerId, action) {
  const data = await requestJson(`/api/providers/${providerId}/${action}`, { method: "POST" });
  addMessage("assistant", `Provider 已${action === "connect" ? "连接" : "断开"}：${data.name}`);
  await loadPanel(activePanel);
}

async function testLlmProvider(providerId) {
  const data = await requestJson(`/api/llm/providers/${providerId}/test`, { method: "POST" });
  addMessage("assistant", `模型测试完成：${data.status}`, { cards: [{ title: "模型测试", payload: data }] });
  await loadPanel("llmCalls");
}

async function setDefaultLlmProvider(providerId) {
  const data = await requestJson(`/api/llm/providers/${providerId}/default`, { method: "POST" });
  addMessage("assistant", `默认模型已设置：${data.name}`);
  await loadPanel(activePanel);
}

async function toggleLlmProvider(providerId, status) {
  const data = await requestJson(`/api/llm/providers/${providerId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  addMessage("assistant", `模型状态已更新：${data.status}`);
  await loadPanel(activePanel);
}

async function evaluatePersonalSkill(skillId) {
  const data = await requestJson(`/api/personal-skills/${skillId}/evaluate`, { method: "POST" });
  addMessage("assistant", `个人技能评测：${data.eval_status}`, { cards: [{ title: "个人技能评测", payload: data }] });
  await loadPanel(activePanel);
}

async function activatePersonalSkill(skillId) {
  const data = await requestJson(`/api/personal-skills/${skillId}/activate`, { method: "POST" });
  addMessage("assistant", `个人技能已激活：${data.title}`);
  await loadPanel(activePanel);
}

async function archivePersonalSkill(skillId) {
  const data = await requestJson(`/api/personal-skills/${skillId}/archive`, { method: "POST" });
  addMessage("assistant", `个人技能已归档：${data.title}`);
  await loadPanel(activePanel);
}

async function createPersonalSkillPatch(skillId) {
  const reason = window.prompt("补丁原因", "优化提示词稳定性");
  if (!reason?.trim()) return;
  const promptTemplate = window.prompt("新的提示词模板；留空则沿用当前模板", "");
  const payload = { reason: reason.trim() };
  if (promptTemplate?.trim()) payload.proposed_prompt_template = promptTemplate.trim();
  const data = await requestJson(`/api/personal-skills/${skillId}/patches`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  addMessage("assistant", `技能补丁已创建：${data.id}`);
  await loadPanel("skillPatches");
}

async function evaluateSkillPatch(patchId) {
  const data = await requestJson(`/api/personal-skill-patches/${patchId}/evaluate`, { method: "POST" });
  addMessage("assistant", `技能补丁评测：${data.eval_status}`, { cards: [{ title: "技能补丁评测", payload: data }] });
  await loadPanel(activePanel);
}

async function applySkillPatch(patchId) {
  const data = await requestJson(`/api/personal-skill-patches/${patchId}/apply`, { method: "POST" });
  addMessage("assistant", `技能补丁已应用：${data.skill.title}`);
  await loadPanel(activePanel);
}

async function rollbackPersonalSkill(skillId) {
  const data = await requestJson(`/api/personal-skills/${skillId}/rollback`, { method: "POST" });
  addMessage("assistant", `个人技能已回滚：${data.title}`);
  await loadPanel(activePanel);
}

async function restoreBackup(backupId) {
  if (!window.confirm("\u786e\u8ba4\u6062\u590d\u8fd9\u4e2a\u5907\u4efd\uff1f")) return;
  const data = await requestJson(`/api/backups/${backupId}/restore`, { method: "POST" });
  addMessage("assistant", `\u5907\u4efd\u5df2\u6062\u590d\uff1a${data.backup.id}`);
  await loadPanel(activePanel);
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
  if (panel === "homeCards" && item.route) {
    controls.push(
      `<button class="action-button" data-panel="${escapeHtml(item.route)}">
        ${escapeHtml(item.action_label || "\u67e5\u770b")}
      </button>`
    );
  }
  if (panel === "ideas") {
    controls.push(`<button class="action-button" data-idea-to-todo="${item.id}">转待办</button>`);
    controls.push(`<button class="action-button" data-idea-to-prd="${item.id}">转 PRD</button>`);
    controls.push(`<button class="action-button" data-idea-to-scene="${item.id}">转场景</button>`);
    controls.push(`<button class="action-button" data-idea-preference="${item.id}">记住偏好</button>`);
  }
  if (panel === "todos" && item.status === "open") {
    controls.push(`<button class="action-button" data-complete-todo="${item.id}">完成</button>`);
  }
  if (panel === "growthLog" && item.status === "active") {
    controls.push(`<button class="action-button reject" data-rollback-growth="${item.id}">回滚</button>`);
  }
  if (panel === "yellowQueue" && item.status === "pending") {
    controls.push(`<button class="action-button" data-confirm="${item.id}">确认</button>`);
    controls.push(`<button class="action-button reject" data-reject="${item.id}">拒绝</button>`);
  }
  if (panel === "settings") {
    if (typeof item.value === "boolean") {
      controls.push(
        `<button class="action-button" data-setting-key="${item.key}" data-setting-value="${String(!item.value)}">
          ${item.value ? "关闭" : "开启"}
        </button>`
      );
    }
    if (item.key === "red_zone_policy") {
      const nextValue = item.value === "block" ? "confirm_only" : "block";
      controls.push(
        `<button class="action-button reject" data-setting-key="${item.key}" data-setting-value="${nextValue}">
          切换为 ${nextValue}
        </button>`
      );
    }
  }
  if (panel === "providers") {
    const action = item.status === "connected" ? "disconnect" : "connect";
    controls.push(
      `<button class="action-button${action === "disconnect" ? " reject" : ""}"
        data-provider-id="${item.provider_id}" data-provider-action="${action}">
        ${action === "connect" ? "连接" : "断开"}
      </button>`
    );
  }
  if (panel === "llmProviders") {
    controls.push(`<button class="action-button" data-llm-test="${item.provider_id}">测试</button>`);
    if (!item.is_default) {
      controls.push(`<button class="action-button" data-llm-default="${item.provider_id}">设为默认</button>`);
    }
    const nextStatus = item.status === "connected" ? "disabled" : "connected";
    controls.push(
      `<button class="action-button${nextStatus === "disabled" ? " reject" : ""}"
        data-llm-toggle="${item.provider_id}" data-llm-status="${nextStatus}">
        ${nextStatus === "connected" ? "启用" : "停用"}
      </button>`
    );
  }
  if (panel === "personalSkills") {
    if (item.status !== "archived") {
      controls.push(`<button class="action-button" data-personal-skill-patch="${item.id}">新补丁</button>`);
    }
    if (item.status === "draft") {
      controls.push(`<button class="action-button" data-personal-skill-eval="${item.id}">评测</button>`);
      controls.push(`<button class="action-button" data-personal-skill-activate="${item.id}">激活</button>`);
    }
    if (item.version > 1) {
      controls.push(`<button class="action-button reject" data-personal-skill-rollback="${item.id}">回滚</button>`);
    }
    if (item.status !== "archived") {
      controls.push(`<button class="action-button reject" data-personal-skill-archive="${item.id}">归档</button>`);
    }
  }
  if (panel === "skillPatches") {
    if (item.status === "draft" || item.status === "failed") {
      controls.push(`<button class="action-button" data-skill-patch-eval="${item.id}">评测</button>`);
    }
    if (item.eval_status === "passed" && item.status !== "applied") {
      controls.push(`<button class="action-button" data-skill-patch-apply="${item.id}">应用</button>`);
    }
  }
  if (panel === "backups") {
    controls.push(`<button class="action-button reject" data-restore-backup="${item.id}">\u6062\u590d</button>`);
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
  const items = Array.isArray(data) ? data : [data];
  if (!items.length) {
    panelList.innerHTML = `<div class="panel-empty">No records</div>`;
    return;
  }
  panelList.innerHTML = items.map((item) => renderPanelItem(item, panel)).join("");
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
  const rollbackGrowthId = event.target.dataset?.rollbackGrowth;
  const settingKey = event.target.dataset?.settingKey;
  const settingValue = event.target.dataset?.settingValue;
  const providerId = event.target.dataset?.providerId;
  const providerAction = event.target.dataset?.providerAction;
  const llmTestId = event.target.dataset?.llmTest;
  const llmDefaultId = event.target.dataset?.llmDefault;
  const llmToggleId = event.target.dataset?.llmToggle;
  const llmStatus = event.target.dataset?.llmStatus;
  const personalSkillEvalId = event.target.dataset?.personalSkillEval;
  const personalSkillActivateId = event.target.dataset?.personalSkillActivate;
  const personalSkillArchiveId = event.target.dataset?.personalSkillArchive;
  const personalSkillPatchId = event.target.dataset?.personalSkillPatch;
  const personalSkillRollbackId = event.target.dataset?.personalSkillRollback;
  const skillPatchEvalId = event.target.dataset?.skillPatchEval;
  const skillPatchApplyId = event.target.dataset?.skillPatchApply;
  const restoreBackupId = event.target.dataset?.restoreBackup;
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
    if (rollbackGrowthId) await rollbackGrowthLog(rollbackGrowthId);
    if (settingKey) await updateSetting(settingKey, settingValue);
    if (providerId) await setProviderStatus(providerId, providerAction);
    if (llmTestId) await testLlmProvider(llmTestId);
    if (llmDefaultId) await setDefaultLlmProvider(llmDefaultId);
    if (llmToggleId) await toggleLlmProvider(llmToggleId, llmStatus);
    if (personalSkillEvalId) await evaluatePersonalSkill(personalSkillEvalId);
    if (personalSkillActivateId) await activatePersonalSkill(personalSkillActivateId);
    if (personalSkillArchiveId) await archivePersonalSkill(personalSkillArchiveId);
    if (personalSkillPatchId) await createPersonalSkillPatch(personalSkillPatchId);
    if (personalSkillRollbackId) await rollbackPersonalSkill(personalSkillRollbackId);
    if (skillPatchEvalId) await evaluateSkillPatch(skillPatchEvalId);
    if (skillPatchApplyId) await applySkillPatch(skillPatchApplyId);
    if (restoreBackupId) await restoreBackup(restoreBackupId);
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
