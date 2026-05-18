# Hermes Python MVP

Hermes 是一个面向 C 端用户的受控型个人智能体系统。本仓库当前实现的是第一版 Python MVP：用 FastAPI 提供服务端能力，用 SQLite 保存本地状态，用原生 HTML/CSS/JS 提供客户端控制台。

## 当前已搭建内容

```text
hermes_app/
  main.py                 FastAPI 入口，挂载 API 和 Web 客户端
  api/routes.py           HTTP API
  core/database.py        SQLite 初始化与访问封装
  services/
    intent_router.py      基础意图路由
    safety.py             风险分级
    orchestrator.py       Hermes 主编排
    memory.py             Memory Candidate 与记忆中心
    actions.py            受控 Action Gate
    skills.py             MVP Skill Registry
    inspiration.py        灵感 Idea Card 生成
    logs.py               Execution Log
    llm_providers.py      LLM Provider 配置与 API Key 本地保护保存
    llm_client.py         OpenAI-compatible Chat Completions 调用
    prompt_library.py     Hermes 高智能 Prompt Library
  web/
    templates/index.html  客户端页面
    static/               样式与交互脚本
tests/
  test_api.py             最小 API 回归测试
```

## 启动

服务端开发模式：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn hermes_app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

桌面模式：

```powershell
pip install -r requirements-desktop.txt
python -m desktop.main
```

桌面模式会启动 PySide6 窗口、嵌入式 FastAPI 服务、随机本地端口和一次性本地访问 token。默认数据目录位于 `%APPDATA%/Hermes`，开发时可通过 `HERMES_DESKTOP_HOME` 覆盖。

## 可测试输入

```text
明天早上提醒我带伞
记住我喜欢科技新闻
给我一个产品灵感挑战
把这段会议内容提取待办
帮我生成一个上线清单
把这件黑色外套加入衣橱
帮我分析这个产品下一步怎么做
```

## 大模型配置

Hermes 现在支持 OpenAI-compatible Chat Completions 协议。启动桌面或 Web 控制台后，打开右侧“模型”面板，添加：

```text
Base URL: https://api.openai.com/v1 或本地/第三方 OpenAI-compatible 地址
Model: 由你的服务商提供的模型 ID
API Key: 云模型填写；本地模型可留空
```

API Key 只保存在本地数据库，接口不会回显完整密钥，只返回 `api_key_set` 和 `api_key_preview`。当前实现是本地保护保存，不等同于系统 Keychain 或 SQLCipher 强加密。

云端模型默认不能处理上传文件内容。只有同时打开全局 `llm_allow_cloud_file_context` 设置，并且对应 LLM Provider 的 `allow_file_context=true` 时，文件总结类 Skill 才会把文件文本发送给云端模型；本地 OpenAI-compatible Provider 不受该云端限制。

## API

```text
GET  /api/health
POST /api/chat
GET  /api/llm/providers
POST /api/llm/providers
PATCH /api/llm/providers/{provider_id}
POST /api/llm/providers/{provider_id}/default
POST /api/llm/providers/{provider_id}/test
POST /api/llm/chat
GET  /api/llm/calls
GET  /api/prompts
GET  /api/memory
GET  /api/actions/pending
POST /api/actions/{action_id}/confirm
POST /api/actions/{action_id}/reject
GET  /api/reminders
GET  /api/ideas
GET  /api/wardrobe
GET  /api/skills
GET  /api/personal-skills
POST /api/personal-skills/drafts
POST /api/personal-skills/{skill_id}/evaluate
POST /api/personal-skills/{skill_id}/activate
POST /api/personal-skills/{skill_id}/archive
POST /api/personal-skills/{skill_id}/rollback
GET  /api/personal-skill-patches
POST /api/personal-skills/{skill_id}/patches
POST /api/personal-skill-patches/{patch_id}/evaluate
POST /api/personal-skill-patches/{patch_id}/apply
GET  /api/skill-curator/suggestions
POST /api/skill-curator/run
GET  /api/skill-curator/runs
GET  /api/logs
```

## 重要边界

当前版本已接入真实 LLM Provider 配置和 OpenAI-compatible 调用，但默认不内置任何云端 API Key；用户必须在“模型”面板自行配置。LLM 只负责理解、生成草案和规划，不能直接写数据库或直接调用外部 API；执行类动作仍必须经过 Tool Registry 与 Action Gate。

日历、邮件、网盘仍是占位 Provider；文件解析、天气、新闻、地图、部分 Skill 已有本地或公开接口实现。

天气能力已接入 Open-Meteo Provider v1：

```text
GET /api/weather?location=北京
GET /api/weather/cache
```

Provider 使用 Open-Meteo 官方接口：

```text
Geocoding: https://geocoding-api.open-meteo.com/v1/search
Forecast:  https://api.open-meteo.com/v1/forecast
```

下一步应该继续接入：

1. Responses API / 工具调用协议支持。
2. OS Keychain 或 SQLCipher 级密钥保护。
3. 日历、邮件、网盘 OAuth Provider。
4. 多模态图片识别和文件深度解析模型。
5. 完整 Skills、真实外部 Provider、密钥强保护和正式商用发布链路。
