# Hermes 代码评审记录

## 2026-05-18 基线原型评审

范围：

```text
FastAPI MVP
Web 客户端原型
产品开发计划文档
```

结论：

```text
通过，作为后续桌面化开发基线。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
GET /api/health
GET /
GET /static/styles.css
```

风险：

```text
当前尚未初始化 Git 仓库。
桌面壳、系统托盘、本地 token、打包流程还未完成。
```

## 2026-05-18 阶段 1 桌面壳与本地服务评审

范围：

```text
本地 token API 保护
DesktopServiceManager
PySide6 桌面窗口
QtWebEngine 加载本地 UI
系统托盘菜单
桌面数据目录初始化
桌面启动说明
```

结论：

```text
通过，形成可提交点 stage-1-desktop-shell-local-service。
```

已验证：

```text
python -m compileall hermes_app desktop tests
python -m pytest -q
DesktopServiceManager 随机端口启动与关闭
无 token 访问受保护 API 返回 401
带 X-Hermes-Token 访问受保护 API 返回 200
HermesDesktopWindow 非交互式构造成功
QSystemTrayIcon.isSystemTrayAvailable() 返回 True
```

评审结论：

```text
API token 中间件只在 HERMES_LOCAL_TOKEN 存在时启用，不影响普通开发模式。
桌面服务只绑定 127.0.0.1，符合本地应用安全边界。
DesktopServiceManager 会恢复环境变量，避免测试污染。
桌面窗口关闭时默认隐藏到托盘，退出菜单会停止本地服务。
```

遗留事项：

```text
当前全局 Python 环境中的 PySide6 会输出 NumPy 2.x 兼容性警告；requirements-desktop.txt 已固定 numpy<2，正式桌面环境需按该依赖安装。
尚未实现桌面日志滚动文件。
已初始化 Git 仓库并推送 GitHub main 分支。
```

提交记录：

```text
f3e3241 stage 1 desktop shell and local service
```

## 2026-05-18 阶段 1 桌面日志系统评审

范围：

```text
desktop/logging_config.py
DesktopServiceManager 日志接入
HermesDesktopWindow 日志接入
日志单元测试
```

结论：

```text
通过，形成可提交点 stage-1-desktop-logging。
```

已验证：

```text
python -m compileall desktop tests
python -m pytest -q
```

评审结论：

```text
日志写入 %APPDATA%/Hermes/logs/desktop.log 或 HERMES_DESKTOP_HOME/logs/desktop.log。
RotatingFileHandler 单文件 2MB，最多保留 5 份，满足桌面 MVP 的本地诊断需求。
setup_desktop_logging(reset=True) 支持测试隔离，避免重复 handler。
服务启动、服务就绪、服务停止、窗口初始化、托盘初始化、退出路径均已记录。
```

提交记录：

```text
91aeb74 stage 1 desktop logging
```

## 2026-05-18 阶段 2 天气 Provider v1 评审

范围：

```text
weather_cache 数据表
WeatherService
Open-Meteo Geocoding
Open-Meteo Forecast
/api/weather
/api/weather/cache
Hermes 对话天气意图接入
客户端天气缓存面板
```

结论：

```text
通过，形成可提交点 stage-2-weather-provider-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
WeatherService 真实查询 Beijing 返回 ok
```

评审结论：

```text
天气 Provider 不需要 API Key，适合桌面 MVP。
Provider 错误不会让 Hermes 崩溃，会返回 provider_error 并写入缓存。
天气查询结果写入 weather_cache，右侧天气面板可查看历史。
对话输入如“北京天气”会直接调用 WeatherService。
```

资料来源：

```text
Open-Meteo Geocoding API: https://open-meteo.com/en/docs/geocoding-api
Open-Meteo Forecast API: https://open-meteo.com/en/docs
```

提交记录：

```text
c67d12c stage 2 weather provider v1
```

## 2026-05-18 阶段 2 Task Decomposer v1 评审

范围：

```text
TaskPlan / TaskStep schema
TaskDecomposer 服务
/api/decompose
/api/chat task_plan 输出
客户端 Task Plan 展示
```

结论：

```text
通过，形成可提交点 stage-2-task-decomposer-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
每个对话请求现在都有结构化任务计划。
中风险及以上步骤会标记 requires_confirmation。
天气、记忆、提醒、衣橱、灵感和 MVP Skills 都有明确步骤。
Task Plan 只描述和规划，不直接绕过 Action Gate。
```

提交记录：

```text
3a76b06 stage 2 task decomposer v1
```

## 2026-05-18 阶段 2 Memory Candidate Pipeline v1 评审

范围：

```text
memory_candidates 数据表
MemoryService 候选创建、确认、拒绝
/api/memory/candidates
/api/memory/candidates/{id}/confirm
/api/memory/candidates/{id}/reject
Action Gate memory.confirm_candidate
客户端记忆候选面板
```

结论：

```text
通过，形成可提交点 stage-2-memory-candidate-pipeline。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
记忆写入不再直接依赖临时 payload，而是先进入候选区。
用户可以通过 Action Gate 确认候选写入长期记忆。
候选可以被拒绝，被拒绝后不能再次确认。
候选记录保留来源、原因、敏感性、置信度和状态，方便审计。
```

提交记录：

```text
827b28f stage 2 memory candidate pipeline
```

## 2026-05-18 阶段 2 Tool Registry v1 评审

范围：

```text
ToolDefinition schema
ToolRegistry 服务
ActionService 通过 ToolRegistry 执行
/api/tools
客户端工具面板
工具注册表单元测试
```

结论：

```text
通过，形成可提交点 stage-2-tool-registry-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
ActionService 不再直接维护具体工具执行分支。
当前注册工具包括 reminder.create、memory.write、memory.confirm_candidate、idea.save、wardrobe.add。
未知工具会被 blocked，不会进入数据库写入。
ToolDefinition 暴露风险等级、是否需要确认、是否可回滚、是否启用。
```

提交记录：

```text
93cdbc8 stage 2 tool registry v1
```

## 2026-05-18 阶段 2 Reminder Center v1 评审

范围：

```text
ReminderService
/api/reminders
/api/reminders/{id}
PATCH /api/reminders/{id}
POST /api/reminders/{id}/complete
DELETE /api/reminders/{id}
ToolRegistry reminder.create 接入 ReminderService
```

结论：

```text
通过，形成可提交点 stage-2-reminder-center-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
提醒创建继续走 Action Gate 和 Tool Registry，不绕过确认链路。
提醒删除采用 status=deleted 软删除，避免 Red Zone 风险。
ReminderService 提供明确服务边界，后续可接 Scheduler 和系统通知。
```

提交记录：

```text
待提交：stage-2-reminder-center-v1
```
