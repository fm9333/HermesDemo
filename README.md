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
```

## API

```text
GET  /api/health
POST /api/chat
GET  /api/memory
GET  /api/actions/pending
POST /api/actions/{action_id}/confirm
POST /api/actions/{action_id}/reject
GET  /api/reminders
GET  /api/ideas
GET  /api/wardrobe
GET  /api/skills
GET  /api/logs
```

## 重要边界

当前版本没有接入真实 LLM，也没有接入日历、邮件、文件解析等第三方服务。现在的编排器使用规则路由和本地 mock Skill，目标是先把产品方案里的架构边界跑通。

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

下一步应该接入：

1. LLM Adapter：把 `HermesOrchestrator` 内的规则回复替换为模型规划。
2. Tool Registry：将 Action executor 从硬编码迁移为注册式工具。
3. Eval Center：为 Skill Patch 和 Tool Plan 增加评测样例。
4. Auth/User：增加真实用户、权限和多租户隔离。
5. Provider：接入天气、日历、文件解析、图片识别等外部能力。
