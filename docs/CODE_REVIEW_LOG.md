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
bdabf9f stage 2 reminder center v1
```

## 2026-05-18 阶段 2 Wardrobe Center v1 评审

范围：

```text
wardrobe_items status 字段迁移
WardrobeService
/api/wardrobe
/api/wardrobe/{id}
PATCH /api/wardrobe/{id}
DELETE /api/wardrobe/{id}
ToolRegistry wardrobe.add 接入 WardrobeService
```

结论：

```text
通过，形成可提交点 stage-2-wardrobe-center-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
衣橱新增继续走 Action Gate 和 Tool Registry。
衣橱删除采用 status=archived 归档，不做物理删除。
数据库初始化包含 status 字段迁移，兼容已有 wardrobe_items 表。
WardrobeService 为后续图片识别、穿搭建议和 Scene 联动提供服务边界。
```

提交记录：

```text
ee3659d stage 2 wardrobe center v1
```

## 2026-05-18 阶段 3 Skill Runtime v1 评审

范围：

```text
skill_runs 数据表
SkillRuntime
POST /api/skills/{skill_id}/run
GET /api/skills/runs
HermesOrchestrator Skill 调用记录化
客户端技能运行面板
```

结论：

```text
通过，形成可提交点 stage-3-skill-runtime-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
Skill 调用现在有持久化运行记录。
Orchestrator 调用 document.summarize、work.todo_extract、content.list_generate 时会通过 SkillRuntime。
Skill Runtime 保留输入、输出、状态和创建时间，后续可接 Eval Center 和 Skill Curator。
未注册 Skill 返回 not_found 并记录，不会抛出未处理异常。
```

提交记录：

```text
b43fb37 stage 3 skill runtime v1
```

## 2026-05-18 阶段 3 File Upload v1 评审

范围：

```text
files 数据表
FileService
POST /api/files/upload
GET /api/files
GET /api/files/{id}
客户端文件面板
```

结论：

```text
通过，形成可提交点 stage-3-file-upload-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
上传文件保存到本地文件库，不依赖外部服务。
文件名经过安全清洗，避免路径穿越。
文件记录保留 content_type、size、storage_path、status 和 created_at。
该能力为后续 document.summarize 真实文件解析提供基础。
```

提交记录：

```text
ae947bb stage 3 file upload v1
```

## 2026-05-18 阶段 3 Image Upload v1 评审

范围：

```text
images 数据表
ImageService
POST /api/images/upload
GET /api/images
GET /api/images/{id}
客户端图片面板
```

结论：

```text
通过，形成可提交点 stage-3-image-upload-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
图片上传复用 FileService，同时写入独立 images 表。
ImageService 使用 Pillow 验证图片有效性并读取宽高。
非图片内容会返回 400，不会写入图片记录。
该能力为 image.clothing_recognition 和照片分类提供基础。
```

提交记录：

```text
3f5712b stage 3 image upload v1
```

## 2026-05-18 阶段 3 document.summarize 文本文件解析 v1 评审

范围：

```text
FileService.read_text
POST /api/files/{file_id}/summarize
SkillRuntime document.summarize 集成
```

结论：

```text
通过，形成可提交点 stage-3-document-summarize-text-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
v1 仅允许 text/plain、text/markdown、.txt、.md，避免误读二进制文件。
读取上限 200KB，避免桌面端一次性处理过大文件。
摘要调用走 SkillRuntime 并写入 skill_runs，后续可进入 Eval 和 Curator。
PDF/DOCX 解析仍是后续任务，未在本次范围内标记完成。
```

提交记录：

```text
5765d6d stage 3 document summarize text v1
```

## 2026-05-18 阶段 3 work.todo_extract v1 评审

范围：

```text
SkillRegistry work.todo_extract
SkillRuntime work.todo_extract 测试
```

结论：

```text
通过，形成可提交点 stage-3-work-todo-extract-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
待办提取从静态 mock 升级为规则提取。
支持按中文/英文分隔符切句。
识别待办、todo、需要、请、安排、跟进、确认、完成、处理、修复等动作信号。
无命中时返回低置信度 fallback，避免空结果造成 UI 断层。
```

提交记录：

```text
9831ab9 stage 3 work todo extract v1
```

## 2026-05-18 阶段 3 content.list_generate v1 评审

范围：

```text
SkillRegistry content.list_generate
SkillRuntime content.list_generate 测试
```

结论：

```text
通过，形成可提交点 stage-3-content-list-generate-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
清单生成从静态 mock 升级为主题模板。
当前支持 release、travel、shopping、general 四类。
输出 items 使用结构化对象，后续可直接进入待办或清单管理。
```

提交记录：

```text
1c6e89d stage 3 content list generate v1
```

## 2026-05-18 阶段 3 document.summarize PDF/DOCX 解析 v1 评审

范围：

```text
FileService.extract_text
pypdf PDF 解析
python-docx DOCX 解析
/api/files/{file_id}/summarize 统一接入
```

结论：

```text
通过，形成可提交点 stage-3-document-summarize-pdf-docx-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
TXT/MD/PDF/DOCX 使用统一 extract_text 入口。
DOCX 测试验证可提取段落文本。
PDF v1 使用 pypdf，支持文本层 PDF；扫描版 PDF OCR 不在本次范围。
摘要 API 不关心文件类型细节，只调用 FileService 提取文本后交给 SkillRuntime。
```

提交记录：

```text
c9f3503 stage 3 document summarize pdf docx v1
```

## 2026-05-18 阶段 3 image.clothing_recognition v1 评审

范围：

```text
ImageService.recognize_clothing
POST /api/images/{image_id}/recognize-clothing
wardrobe.add 待确认 Action
```

结论：

```text
通过，形成可提交点 stage-3-image-clothing-recognition-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
v1 使用本地像素颜色和文件名启发式识别，不调用云端视觉模型。
识别结果只生成衣橱候选，不直接写入衣橱。
加入衣橱必须通过 Action Gate 确认，符合 Yellow Zone 策略。
后续可替换为真实视觉模型或多模态 LLM。
```

提交记录：

```text
e3986ff stage 3 image clothing recognition v1
```

## 2026-05-18 阶段 4 Scene Registry v1 评审

范围：

```text
scenes 数据表
scene_runs 数据表
SceneService
GET/POST/PATCH /api/scenes
POST /api/scenes/{scene_id}/run
POST /api/scenes/{scene_id}/pause
GET /api/scenes/runs
Hermes 对话 create_scene
客户端场景面板
```

结论：

```text
通过，形成可提交点 stage-4-scene-registry-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
Scene v1 已具备注册、运行、暂停和运行日志。
对话可以创建基础场景草案。
Scene run 会生成结构化 output，并累计 effect_score。
暂停状态下运行会 skipped，不会继续输出推荐。
Context Signal、Opportunity Engine、Attention Policy 深化仍是后续任务。
```

提交记录：

```text
8af4950 stage 4 scene registry v1
```

## 2026-05-18 阶段 4 Context Signal Pipeline v1 评审

范围：

```text
context_signals 数据表
ContextSignalService
POST /api/context-signals
GET /api/context-signals
POST /api/context-signals/{id}/archive
客户端信号面板
```

结论：

```text
通过，形成可提交点 stage-4-context-signal-pipeline-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
Context Signal v1 支持收集、查询、过滤和归档。
信号 payload 以 JSON 保存，适配天气、文件、对话、用户行为等后续来源。
信号暂不自动触发 Scene，下一步进入 Opportunity Engine。
```

提交记录：

```text
4787665 stage 4 context signal pipeline v1
```

## 2026-05-18 阶段 4 Opportunity Engine v1 评审

范围：

```text
opportunities 数据表
OpportunityEngine
POST /api/opportunities/generate
GET /api/opportunities
POST /api/opportunities/{id}/close
客户端机会面板
```

结论：

```text
通过，形成可提交点 stage-4-opportunity-engine-v1。
```

已验证：

```text
python -m compileall hermes_app tests
python -m pytest -q
```

评审结论：

```text
Opportunity Engine v1 可从 active Context Signals 生成机会点。
weather.rain 高概率降雨信号生成带伞提醒机会。
file.uploaded 信号生成 document.summarize Skill 推荐机会。
机会点可关闭，避免长期干扰用户。
去重和 Attention Policy 联动仍是后续任务。
```

提交记录：

```text
3479a07 stage 4 opportunity engine v1
```

## 2026-05-18 阶段 4 Attention Policy + Recommendation Cards v1 评审

范围：

```text
recommendations 数据表
AttentionPolicy
RecommendationService
POST /api/recommendations/generate
GET /api/recommendations
POST /api/recommendations/{id}/dismiss
客户端推荐面板生成与忽略操作
推荐服务和 API 单元测试
```

结论：

```text
通过，形成可提交点 stage-4-attention-recommendations-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Attention Policy v1 按 opportunity priority 将推荐分流到 interrupt、summary、silent。
interrupt 通道会标记 requires_confirmation，后续可接入桌面通知和 Action Gate。
Recommendation Cards v1 会把 open opportunities 转为可查询、可忽略的推荐卡片。
生成逻辑对同一 open opportunity 幂等，避免重复点击产生重复 open 卡片。
客户端推荐面板已具备生成和忽略操作，满足当前阶段闭环。
```

提交记录：

```text
dbafd42 stage 4 attention recommendations v1
```

## 2026-05-18 阶段 4 Scene Feedback v1 评审

范围：

```text
scene_feedback 数据表
SceneService.record_feedback
SceneService.list_feedback
POST /api/scenes/{scene_id}/feedback
GET /api/scenes/{scene_id}/feedback
GET /api/scene-feedback
客户端场景面板有效/误触发反馈操作
客户端反馈面板
场景服务和 API 单元测试
```

结论：

```text
通过，形成可提交点 stage-4-scene-feedback-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Scene Feedback v1 已支持记录用户对场景的有效、误触发、负向、中性反馈。
反馈可绑定 scene_run，绑定错误 run 会返回 400，缺失 scene/run 会返回 404。
effect_score 会根据反馈自动调整，并统一做小数规整，避免浮点残差污染评分。
客户端可以在场景面板直接标记有效或误触发，反馈面板可集中查看记录。
该能力满足“Scene 误触发能反馈”的阶段验收要求。
```

提交记录：

```text
77ae698 stage 4 scene feedback v1
```

## 2026-05-18 阶段 5 Inspiration Agent / Idea Card v1 评审

范围：

```text
idea_cards 扩展字段和迁移
InspirationService 结构化 Idea Card 生成
ToolRegistry idea.save 结构化保存
GET /api/ideas
GET /api/ideas/{id}
灵感对话到保存动作的 API 流程测试
```

结论：

```text
通过，形成可提交点 stage-5-inspiration-idea-card-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Inspiration Agent v1 已从简单文本模板升级为结构化 Idea Card。
生成结果覆盖方向、目标用户、痛点、核心假设、反方挑战、跨域类比、MVP 方案、风险、下一步和评分。
Idea Library API 会解析 tags、risks、next_steps，避免客户端直接处理 *_json 字段。
idea_cards 表扩展使用兼容迁移，不破坏已有本地数据库。
Idea 保存仍经过 Action Gate，满足当前阶段“能保存 Idea Card”的验收要求。
```

提交记录：

```text
650fd6f stage 5 inspiration idea card v1
```

## 2026-05-18 阶段 5 Idea 转待办 v1 评审

范围：

```text
todo_items 数据表
TodoService
GET /api/todos
POST /api/todos/{id}/complete
POST /api/ideas/{id}/to-todo
客户端 Idea 面板转待办操作
客户端待办面板完成操作
Todo 和 API 测试
```

结论：

```text
通过，形成可提交点 stage-5-idea-to-todo-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Idea 转待办 v1 会把结构化 Idea Card 的 next_steps 转为本地 todo_items。
同一 Idea 的同一条 next_step 重复转换会返回已有待办，避免重复点击产生重复行动项。
待办项保留 source=idea 和 source_id，后续可从行动结果追溯回 Idea Card。
待办完成采用状态更新和 completed_at 记录，不做物理删除。
客户端已提供 Idea 面板转待办和待办面板完成入口，形成灵感到行动的最小闭环。
```

提交记录：

```text
9d6d4f4 stage 5 idea to todo v1
```

## 2026-05-18 阶段 5 Idea 转 PRD 草案 v1 评审

范围：

```text
prd_drafts 数据表
PrdDraftService
POST /api/ideas/{id}/to-prd
GET /api/prd-drafts
GET /api/prd-drafts/{id}
客户端 Idea 面板转 PRD 操作
客户端 PRD 草案面板
PRD Draft 和 API 测试
```

结论：

```text
通过，形成可提交点 stage-5-idea-to-prd-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Idea 转 PRD 草案 v1 会把结构化 Idea Card 转为 Markdown 风格 PRD。
草案覆盖背景、目标用户、核心假设、MVP 范围、反方挑战、风险和下一步。
同一 Idea 重复转换返回已有 PRD 草案，避免重复生成。
客户端已提供 Idea 面板转 PRD 和 PRD 草案面板查看入口。
```

提交记录：

```text
6164f3b stage 5 idea to prd v1
```

## 2026-05-18 阶段 5 Idea 转 Scene 草案 v1 评审

范围：

```text
SceneService.get_by_source_context
POST /api/ideas/{id}/to-scene
客户端 Idea 面板转场景操作
Idea 到 Scene 幂等转换测试
```

结论：

```text
通过，形成可提交点 stage-5-idea-to-scene-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Idea 转 Scene 草案 v1 复用现有 Scene Registry，不新增平行场景模型。
转换结果标记 source=idea，context_signal=idea:{id}，可从 Scene 追溯回 Idea Card。
同一 Idea 重复转换返回已有 Scene，避免重复创建。
客户端已提供 Idea 面板转场景入口，转换后跳转到场景面板。
```

提交记录：

```text
7eb185d stage 5 idea to scene v1
```

## 2026-05-18 阶段 5 灵感偏好写入确认 v1 评审

范围：

```text
POST /api/ideas/{id}/preference-candidate
Idea Card 到 Memory Candidate 转换
Action Gate memory.confirm_candidate 确认链路
客户端 Idea 面板记住偏好操作
API 确认链路测试
```

结论：

```text
通过，形成可提交点 stage-5-inspiration-preference-candidate-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
灵感偏好写入确认 v1 不直接写入长期记忆，而是先创建 memory_candidates。
写入长期记忆必须通过 Action Gate 的 memory.confirm_candidate 确认动作。
候选来源标记为 idea，key 为 inspiration_preference，便于后续过滤和审计。
客户端 Idea 面板已提供“记住偏好”入口，并展示确认卡。
该能力满足阶段 5 “灵感偏好写入必须确认”的验收要求。
```

提交记录：

```text
90b237f stage 5 inspiration preference candidate v1
```

## 2026-05-18 阶段 6 Autonomy Zone Classifier v1 评审

范围：

```text
AutonomyZoneClassifier
GET /api/autonomy/zones
POST /api/autonomy/classify
客户端自治规则面板
Autonomy Zone 服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-6-autonomy-zone-classifier-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Autonomy Zone Classifier v1 明确区分 Green、Yellow、Red 三类自主边界。
Green Zone 只允许低风险优化进入 Draft 或候选区。
Yellow Zone 对数据、偏好、提醒策略等影响用户体验的变更要求确认。
Red Zone 对高风险、敏感、外发或不可逆动作只允许 suggest_only，不允许自主执行。
该分类器将作为后续 Eval Runner、Growth Log 和自主优化确认页的安全基础。
```

提交记录：

```text
03ea6c3 stage 6 autonomy zone classifier v1
```

## 2026-05-18 阶段 6 Eval Runner v1 评审

范围：

```text
eval_runs 数据表
EvalRunner
autonomy.zone.basic 评测套件
GET /api/eval/suites
POST /api/eval/suites/{suite_id}/run
GET /api/eval/runs
客户端评测面板
Eval Runner 服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-6-eval-runner-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Eval Runner v1 已具备本地评测套件、运行记录和 API 查询能力。
首个内置套件 autonomy.zone.basic 覆盖 Green、Yellow、Red 三类自主边界。
评测结果持久化到 eval_runs，保留 score、status 和逐 case 结果。
客户端评测面板可触发运行并查看历史记录。
该能力为后续 Draft 启用前 Eval、Skill Patch Eval 和安全策略回归提供基础。
```

提交记录：

```text
e2b3163 stage 6 eval runner v1
```

## 2026-05-18 阶段 6 Growth Log v1 评审

范围：

```text
growth_logs 数据表
GrowthLogService
GET /api/growth-log
POST /api/growth-log
POST /api/growth-log/{id}/rollback
客户端成长记录面板
Growth Log 服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-6-growth-log-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Growth Log v1 让用户可以查看 Hermes 最近优化了什么。
记录保留 Zone、来源任务、影响范围和结构化 payload，便于后续审计。
回滚采用 status=rolled_back 和 rolled_back_at 标记，不物理删除历史。
客户端成长记录面板已提供查看和回滚入口。
```

提交记录：

```text
8dd90b7 stage 6 growth log v1
```

## 2026-05-18 阶段 6 Yellow Zone 确认页 v1 评审

范围：

```text
GET /api/yellow-zone/pending
客户端 Yellow Zone 确认面板
Action Gate 确认/拒绝复用
Yellow Zone API 测试
```

结论：

```text
通过，形成可提交点 stage-6-yellow-zone-queue-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Yellow Zone 确认页 v1 复用现有 Action Gate，不新增平行确认机制。
队列仅收集中风险 pending actions，避免把 Red Zone 或低风险记录混入确认页。
客户端确认面板可直接确认或拒绝，操作后走既有 ActionService 流程。
该能力满足阶段 6 “Yellow Zone 优化必须让用户感知”的基础要求。
```

提交记录：

```text
1e377b6 stage 6 yellow zone queue v1
```

## 2026-05-18 阶段 6 Red Zone 拦截强化 v1 评审

范围：

```text
SafetyService Red Zone blocked 分类
SafetyService.red_zone_check
POST /api/red-zone/check
GET /api/red-zone/rules
客户端红区规则面板
危险请求对话入口拦截测试
```

结论：

```text
通过，形成可提交点 stage-6-red-zone-blocking-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Red Zone 拦截强化 v1 将删除、清空、支付、转账、授权、导出/分享等动作直接归类为 blocked。
blocked 请求在 Hermes 对话入口不会继续创建 Action，避免进入确认或执行链路。
red-zone/check API 可供后续 Eval Runner 和安全策略页复用。
客户端红区面板可查看当前阻断规则，满足用户可见的安全边界要求。
```

提交记录：

```text
3328566 stage 6 red zone blocking v1
```

## 2026-05-18 阶段 6 安全策略设置 v1 评审

范围：

```text
app_settings 数据表
SettingsService
GET /api/settings
PATCH /api/settings/{key}
客户端设置面板和策略切换
Settings 服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-6-safety-settings-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
安全策略设置 v1 建立了本地 app_settings 表和默认策略初始化。
当前覆盖自主进化开关、Yellow Zone 确认策略、Red Zone 策略、Draft Eval 要求和通知开关。
设置更新会校验非法值，避免写入不可识别策略。
客户端设置面板支持布尔策略和 Red Zone 策略切换。
```

提交记录：

```text
826bfd5 stage 6 safety settings v1
```

## 2026-05-18 阶段 7 Provider Registry v1 评审

范围：

```text
providers 数据表
ProviderRegistry
GET /api/providers
POST /api/providers/{id}/connect
POST /api/providers/{id}/disconnect
客户端集成 Provider 面板
Provider Registry 服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-7-provider-registry-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
Provider Registry v1 建立了外部服务连接状态、权限和配置的统一入口。
默认包含 Open-Meteo Weather 已连接 Provider，以及日历、邮件、网盘占位 Provider。
连接和断开操作会更新本地状态，不依赖外部 OAuth，后续可平滑替换为真实授权流程。
客户端集成面板已支持查看、连接和断开 Provider。
```

提交记录：

```text
c2d829b stage 7 provider registry v1
```

## 2026-05-18 阶段 7 主动建议中心 v1 评审

范围：

```text
ProactiveSuggestionService
GET /api/proactive/suggestions
客户端主动建议面板
主动建议聚合服务和 API 测试
```

结论：

```text
通过，形成可提交点 stage-7-proactive-suggestions-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
主动建议中心 v1 聚合 open recommendations、open todos 和未连接 Provider。
建议卡统一为 type、title、priority、source_id、payload 结构，便于首页卡片和通知策略复用。
客户端主动面板已接入统一建议列表。
当前版本只做轻量聚合，不主动打扰用户，符合“不造成高频打扰”的阶段约束。
```

提交记录：

```text
cc5dcf2 stage 7 proactive suggestions v1
```

## 2026-05-18 阶段 7 轻量实时触发 v1 评审

范围：

```text
trigger_runs 数据表
TriggerService
POST /api/triggers/run
GET /api/triggers/history
客户端触发历史面板
Context Signal -> Opportunity -> Recommendation -> Proactive Suggestions 触发链路测试
```

结论：

```text
通过，形成可提交点 stage-7-lightweight-triggers-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：

```text
轻量实时触发 v1 将上下文信号、机会引擎、推荐卡和主动建议串成一条可运行链路。
每次触发都会写入 trigger_runs，保留输出快照，便于后续排查和复盘。
客户端触发面板可手动运行并查看历史记录。
当前版本只支持本地轻量触发，不引入后台高频轮询，避免打扰和资源浪费。
```

提交记录：

```text
5451de5 stage 7 lightweight triggers v1
```

## 2026-05-18 阶段 7 每周灵感复盘 v1 评审

范围：
```text
weekly_reviews 数据表
WeeklyReviewService
POST /api/weekly-reviews/generate
GET /api/weekly-reviews
客户端复盘面板
Weekly Review 服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-7-weekly-review-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
每周灵感复盘 v1 将最近 Idea Card 汇总为可持久化的周复盘记录，保留 week_start、summary、highlights 和 next_actions，便于后续首页卡片、通知摘要和长期成长日志复用。
生成接口不会修改原始 Idea Card，只新增 weekly_reviews 快照，风险边界较低。
空灵感库场景会给出下一步补充行动，避免客户端出现不可解释的空结果。
客户端新增复盘面板和生成按钮，形成查看历史与主动生成的闭环。
```

提交记录：
```text
e235bb9 stage 7 weekly review v1
```

## 2026-05-18 阶段 7 个性化首页卡片 v1 评审

范围：
```text
HomeCardService
GET /api/home/cards
客户端首页面板默认入口
首页卡片跳转控制
Home Cards 服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-7-personalized-home-cards-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
个性化首页卡片 v1 采用派生视图聚合已有状态，不新增冗余业务表，降低数据一致性风险。
卡片优先级覆盖待确认动作、记忆候选、最新周复盘和主动建议，能把当前最需要处理的事项放到首页。
每张卡片都保留 route 和 action_label，客户端可以从首页跳转到对应模块，而不是只展示静态摘要。
空状态提供创建提醒或灵感的引导，避免新用户首次打开首页时出现无解释空白。
```

提交记录：
```text
73075ce stage 7 personalized home cards v1
```

## 2026-05-18 阶段 7 新闻 Provider v1 评审

范围：
```text
news_articles 数据表
ProviderRegistry news.rss 默认 Provider
NewsService RSS/Atom 拉取、解析和缓存
POST /api/news/refresh
GET /api/news
GET /api/news/{id}
客户端新闻面板
新闻 Provider 服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-7-news-provider-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
新闻 Provider v1 采用公开 RSS/Atom 源作为默认实现，不引入付费 API Key 或 OAuth 依赖，适合当前桌面本地 MVP。
新闻内容只缓存标题、链接、摘要、发布时间、标签和来源，不抓取全文，降低版权和存储风险。
文章 ID 基于 URL 稳定生成，重复刷新会更新已有缓存，不会产生重复列表。
Provider 状态为 disconnected 时刷新会返回 disabled，不会继续访问外部网络。
客户端新闻面板只在用户点击刷新时拉取，避免高频后台请求。
```

提交记录：
```text
f6a7b8c stage 7 news provider v1
```

## 2026-05-18 阶段 7 地图 Provider v1 评审

范围：
```text
map_places 数据表
ProviderRegistry map.nominatim 默认 Provider
MapService 手动搜索、Nominatim 请求和本地缓存
POST /api/maps/search
GET /api/maps/places
GET /api/maps/places/{id}
客户端地图面板
地图 Provider 服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-7-map-provider-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
地图 Provider v1 默认断开，用户需要先在 Provider 面板连接后才能发起外部搜索，避免无意识调用公共地理编码服务。
搜索只由用户手动触发，不做自动补全、后台轮询或批量地理编码，符合当前桌面 MVP 的低频使用边界。
相同 query 优先使用本地 map_places 缓存，减少重复请求并满足 Nominatim 对客户端缓存的要求。
请求使用明确 User-Agent，Provider 配置保留 Nominatim usage_policy 链接，后续可切换到自建或商业地理编码端点。
地点缓存保留 display_name、坐标、地址、边界框和原始响应，足够支撑后续地图卡片、通勤场景和位置提醒。
```

资料来源：
```text
Nominatim Search API: https://nominatim.org/release-docs/latest/api/Search/
Nominatim Usage Policy: https://operations.osmfoundation.org/policies/nominatim/
```

提交记录：
```text
8eb78ac stage 7 map provider v1
```

## 2026-05-18 阶段 8 备份与恢复 v1 评审

范围：
```text
Database backup_to / restore_from
BackupService
GET /api/backups
POST /api/backups
POST /api/backups/{id}/restore
客户端备份面板
备份与恢复服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-8-backup-restore-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
备份与恢复 v1 使用 SQLite 官方 backup API 创建一致性快照，避免直接复制正在使用的数据库文件。
备份文件为 zip，包含 hermes.db 和 manifest.json，便于后续加入版本、加密和数据迁移信息。
备份清单从文件系统扫描，不依赖数据库内记录，恢复旧数据库后仍能看到备份文件。
恢复接口会校验 backup_id，拒绝路径穿越；客户端恢复前有确认提示。
API 测试覆盖创建和列表，服务测试覆盖恢复后数据回滚到备份状态。
```

提交记录：
```text
c8b2bc6 stage 8 backup restore v1
```

## 2026-05-18 阶段 8 数据库迁移 v1 评审

范围：
```text
schema_migrations 数据表
Database.MIGRATIONS
Database.list_migrations()
GET /api/database/migrations
客户端迁移面板
数据库迁移幂等测试
```

结论：
```text
通过，形成可提交点 stage-8-database-migrations-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
数据库迁移 v1 为本地 SQLite 增加 schema_migrations 账本，后续发布升级可以明确知道当前数据目录已经应用过哪些 schema 阶段。
迁移记录写入是幂等的，重复 Database.init() 不会产生重复记录。
测试验证重复初始化后已有 memory_items 数据仍然保留，满足“升级不丢数据”的基本约束。
迁移记录通过 API 和客户端面板可见，便于后续支持包、故障诊断和发布验收。
当前 v1 记录的是阶段性 schema 状态，后续复杂变更可扩展为逐条 migration runner。
```

提交记录：
```text
cdd072e stage 8 database migrations v1
```

## 2026-05-18 阶段 8 数据导出 v1 评审

范围：
```text
ExportService
GET /api/exports
POST /api/exports
客户端导出面板
数据导出服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-8-data-export-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
数据导出 v1 使用白名单表导出，避免用户通过 API 导出任意 SQLite 系统表或拼接 SQL。
导出文件为 zip，包含 manifest.json 和 tables/*.json，便于人工审计和后续导入流程复用。
导出目录独立于数据库，导出清单从文件系统扫描，不受数据库恢复影响。
API 测试覆盖指定表导出和列表，服务测试覆盖 zip 内容和未知表拒绝。
```

提交记录：
```text
5330923 stage 8 data export v1
```

## 2026-05-18 阶段 8 崩溃恢复 v1 评审

范围：
```text
RuntimeStateService
FastAPI lifespan clean shutdown
GET /api/runtime/recovery
客户端恢复面板
崩溃恢复服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-8-crash-recovery-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
崩溃恢复 v1 通过 runtime-state.json 记录进程 pid、启动时间、心跳和 clean_shutdown 状态。
新启动时如果发现上一状态仍为 running 且未 clean shutdown，会返回 recovered 状态，便于 UI 和支持日志明确提示异常退出。
FastAPI 使用 lifespan 在关闭阶段写入 clean shutdown，避免使用已弃用 on_event。
当前 v1 不自动回滚数据，只负责异常退出检测和可见化；后续可结合备份、迁移和日志做自动修复建议。
```

提交记录：
```text
7641b3b stage 8 crash recovery v1
```

## 2026-05-18 阶段 8 PyInstaller 打包 v1 评审

范围：
```text
requirements-desktop.txt
packaging/hermes_desktop.spec
scripts/build_desktop.ps1
docs/PACKAGING.md
打包配置测试
```

结论：
```text
通过，形成可提交点 stage-8-pyinstaller-packaging-v1。
```

已验证：

```text
python -m compileall hermes_app desktop tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
PyInstaller 打包 v1 明确以 desktop/main.py 作为桌面入口，并打包 hermes_app/web 本地 UI 资源。
spec 添加 uvicorn 相关 hiddenimports，降低嵌入式 FastAPI 服务在冻结环境中缺模块的风险。
构建脚本固定调用 packaging/hermes_desktop.spec，避免手工命令遗漏资源。
已在当前 Windows 环境完成一次实际 PyInstaller 构建，产物位于 dist/HermesDesktop/HermesDesktop.exe，且包含 _internal/hermes_app/web 本地 UI 资源。
构建日志仍提示全局环境 PySide6/NumPy 2.x 兼容 warning；requirements-desktop.txt 已固定 numpy<2，正式打包环境必须按该依赖安装。
当前验证覆盖配置、脚本和产物结构；安装器、签名和完整 GUI 冒烟测试会在后续发布任务中继续完成。
```

提交记录：
```text
f98a2ad stage 8 pyinstaller packaging v1
2953dec verify pyinstaller desktop build
```

## 2026-05-18 阶段 8 自动更新策略 v1 评审

范围：
```text
SettingsService 更新策略设置项
UpdateService
GET /api/updates/status
POST /api/updates/check
客户端更新面板
更新策略服务和 API 测试
```

结论：
```text
通过，形成可提交点 stage-8-update-strategy-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
自动更新策略 v1 建立了更新渠道、自动更新开关和 manifest URL 的本地设置项。
UpdateService 支持本地文件和远程 URL manifest，能比较版本并尊重 stable/beta 渠道。
当前版本只做检查和展示，不做静默下载、替换可执行文件或自动重启，避免在安全边界未完善前引入高风险写入。
后续可在签名校验、哈希校验和用户确认流程完成后接入真正安装器。
```

提交记录：
```text
acdfee4 stage 8 update strategy v1
```

## 2026-05-18 阶段 8 性能优化 v1 评审

范围：
```text
SQLite 常用查询索引
Database.list_indexes()
GET /api/performance/indexes
客户端性能面板
性能索引测试
```

结论：
```text
通过，形成可提交点 stage-8-performance-indexes-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
性能优化 v1 为 pending actions、memory candidates、reminders、todos、ideas、PRD、context signals、opportunities、recommendations、news 和 maps 的常用查询建立索引。
新增索引均使用 IF NOT EXISTS，重复初始化不会失败。
schema_migrations 增加 0005_performance_indexes，便于发布后确认数据目录是否具备性能索引。
API 和客户端面板可查看当前索引，方便发布支持和性能排查。
```

提交记录：
```text
b753ec1 stage 8 performance indexes v1
```

## 2026-05-18 阶段 8 端到端测试 v1 评审

范围：
```text
tests/test_e2e_release_flow.py
对话 -> Idea Card -> Action Gate -> Todo -> Weekly Review -> Home Cards
Backup / Export / Migrations / Performance / Runtime Recovery API
```

结论：
```text
通过，形成可提交点 stage-8-e2e-release-flow-v1。
```

已验证：

```text
python -m compileall hermes_app desktop tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
端到端测试 v1 覆盖了从用户对话到本地数据沉淀、行动转化、复盘和首页聚合的核心产品闭环。
发布稳定性能力覆盖备份、导出、迁移、性能索引和运行恢复状态接口。
测试使用临时备份/导出目录，避免污染仓库数据目录。
该测试作为阶段 8 后续打包后冒烟测试的基础用例。
```

提交记录：
```text
b35e163 stage 8 e2e release flow v1
```

## 2026-05-18 阶段 8 安全测试 v1 评审

范围：
```text
tests/test_security_release.py
Red Zone 危险请求
ExportService 表白名单
Update settings 渠道校验
Map Provider 默认断开边界
Backup restore backup_id 校验
```

结论：
```text
通过，形成可提交点 stage-8-security-release-tests-v1。
```

已验证：

```text
python -m compileall hermes_app desktop tests
node --check hermes_app/web/static/app.js
python -m pytest -q
```

评审结论：
```text
安全测试 v1 覆盖发布前必须持续回归的高风险边界。
Red Zone 测试确认危险请求不会进入 Action Gate。
导出测试确认 API 不能绕过白名单读取任意 SQLite 表。
地图测试确认 Provider 未连接时不会调用外部服务。
备份测试确认恢复入口拒绝路径穿越式 id。
更新测试确认非法发布渠道不能写入配置。
```

提交记录：
```text
5dc399a stage 8 security release tests v1
```

## 2026-05-18 阶段 9 OpenAI-compatible LLM Provider v1 评审

范围：
```text
llm_providers SQLite schema
LLMProviderService
LLMClient
PromptLibrary
HermesOrchestrator general_chat LLM 接入
SkillRuntime LLM Prompt 优先 + 本地规则 fallback
客户端模型 / 提示词 / 模型调用面板
API 与服务单元测试
```

结论：
```text
通过，形成可提交点 stage-9-llm-provider-prompts-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest tests\test_llm_providers.py tests\test_api.py -q
python -m pytest -q
```

评审结论：
```text
本次补齐了产品文档中缺失的真实大模型配置入口，不再只是本地规则 MVP。
LLM Provider 使用 OpenAI-compatible Chat Completions 协议，用户可配置 Base URL、模型 ID、API Key、温度、超时和输出 token。
API 响应不回显完整 API Key，只返回是否已设置和短 preview；当前实现为本地保护保存，不等同于 OS Keychain/SQLCipher 级强加密。
主智能体普通对话可调用默认模型；模型未配置、调用失败或 Skill LLM 输出异常时会回退本地规则能力，避免核心功能不可用。
Prompt Library 覆盖 Agent、Planner、Memory、Skill、Inspiration、Scene、Eval 和 Safety，强调内部深度分析但不输出隐藏推理过程。
LLM 仍不能直接写数据库或直接调用外部 API，执行类动作继续受 Tool Registry 与 Action Gate 约束。
```

测试结果：
```text
105 passed, 2 warnings
```

提交记录：
```text
06a5ae9 stage 9 llm provider and prompts v1
```

## 2026-05-18 阶段 10 功能符合度审计与云模型文件权限拦截 v1 评审

范围：
```text
docs/FUNCTIONAL_GAP_AUDIT.md
LLMClient contains_file_context policy
SkillRuntime metadata propagation
file summarize API file-context marking
LLM provider / API regression tests
```

结论：
```text
通过，形成可提交点 stage-10-gap-audit-cloud-file-guard-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest tests\test_llm_providers.py tests\test_api.py -q
python -m pytest -q
```

评审结论：
```text
功能符合度审计明确当前项目是可运行 MVP/技术底座，不是原始文档要求的完整商用版。
审计文档列出 P0/P1 缺口，后续开发应优先围绕 Personal Skill、完整 Skills、真实 OAuth Provider、完整 UI 和商用安全交付推进。
文件总结 API 现在会把上传文件文本标记为 contains_file_context。
云端 LLM Provider 处理文件内容必须同时满足全局设置和 Provider 配置双重授权，默认阻断。
本地 OpenAI-compatible Provider 不受云端文件限制，可作为隐私优先路径。
被策略阻断时不会调用 `_post_json`，SkillRuntime 会回退本地规则输出，避免泄漏和功能中断。
```

测试结果：
```text
107 passed, 2 warnings
```

提交记录：
```text
146a3e0 stage 10 gap audit and cloud file guard
```

## 2026-05-18 阶段 11 Personal Skill Draft v1 评审

范围：
```text
personal_skills schema
personal_skill_versions schema
PersonalSkillService
Personal Skill API
客户端个人技能面板
服务层与 API 测试
```

结论：
```text
通过，形成可提交点 stage-11-personal-skill-drafts-v1。
```

已验证：

```text
python -m compileall hermes_app tests
node --check hermes_app/web/static/app.js
python -m pytest tests\test_personal_skills.py tests\test_api.py -q
python -m pytest -q
```

评审结论：
```text
Personal Skill Draft v1 建立了个人技能从草案、评测、激活到归档的第一条可审计生命周期。
草案可手动创建，也可从历史 Skill Run 沉淀，保留来源输入和输出样例。
激活前必须通过基础评测门禁；Red Zone 技能不能自动激活。
版本表记录草案创建时的 Prompt、输出契约和评测报告，为后续 Skill Patch、版本对比和回滚打基础。
客户端个人技能面板已支持新建、评测、激活、归档，但 Skill Curator、自动 Patch 生成和运行时动态调用仍是后续 P0。
```

测试结果：
```text
110 passed, 2 warnings
```
