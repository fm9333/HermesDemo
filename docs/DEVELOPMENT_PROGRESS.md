# Hermes 开发进度台账

更新时间：2026-05-18

状态说明：

```text
[x] 已开发、已测试、已评审
[~] 开发中
[ ] 未开始
```

## 已完成基线

- [x] 产品原始方案读取与需求拆解
  - 验证：已读取 `hermes-product-plan-autonomous-evolution-2026-05-18.md`
  - 评审：功能边界覆盖 Memory、Scene、Action、Skills、Inspiration、Autonomy Zone、Eval

- [x] 桌面一体化完整开发计划
  - 文档：`docs/HERMES_DESKTOP_PRODUCT_DEVELOPMENT_PLAN.md`
  - 验证：章节覆盖架构、页面、数据模型、API、阶段计划、验收标准

- [x] FastAPI 服务端 MVP 原型
  - 代码：`hermes_app/`
  - 验证：`python -m compileall hermes_app tests` 通过
  - 验证：`python -m pytest -q` 通过，3 passed

- [x] Web 客户端控制台原型
  - 代码：`hermes_app/web/`
  - 验证：首页 `/` 返回 HTTP 200，静态资源 `/static/styles.css` 返回 HTTP 200

## 阶段 1：桌面壳与本地服务

- [x] PySide6 桌面窗口
  - 验证：非交互式构造 `HermesDesktopWindow` 成功，窗口标题为 `Hermes Desktop`
- [x] QtWebEngine 加载本地 UI
  - 验证：`QWebEngineView` 成功构造，加载 URL 为本地服务 `/?token=...`
- [x] Embedded FastAPI 生命周期管理
  - 验证：`DesktopServiceManager.start()` 可启动服务，`stop()` 可关闭服务
- [x] 随机端口与本地 token
  - 验证：随机端口不占用 8000；无 token 访问 `/api/skills` 返回 401；带 token 返回 200
- [x] 系统托盘
  - 验证：当前系统 `QSystemTrayIcon.isSystemTrayAvailable()` 返回 True；托盘菜单代码已编译
- [x] 应用退出和后台常驻
  - 验证：关闭事件逻辑已实现；退出动作会停止本地服务
- [x] 本地数据目录初始化
  - 验证：临时桌面数据目录自动创建，数据库目录存在
- [x] 桌面日志系统
  - 验证：`desktop.log` 可写入；日志文件使用 2MB 滚动、保留 5 份

## 阶段 2：基础 Hermes MVP

- [x] 主对话入口原型
- [x] Intent Router v1 原型
- [x] Task Decomposer v1
  - 验证：`/api/decompose` 可返回结构化计划；`/api/chat` 响应包含 `task_plan`
  - 测试：`python -m pytest -q` 通过，11 passed
- [x] Memory Candidate Pipeline v1
  - 验证：候选记忆可创建、列表查询、确认、拒绝
  - 验证：Action Gate 通过 `memory.confirm_candidate` 写入长期记忆
  - 测试：`python -m pytest -q` 通过，13 passed
- [x] 记忆中心原型
- [x] Reminder Center v1
  - 验证：提醒可创建、查询详情、更新、完成、删除归档
  - 验证：创建仍通过 Action Gate 和 Tool Registry
  - 测试：`python -m pytest -q` 通过，17 passed
- [x] Wardrobe Center v1
  - 验证：衣橱条目可创建、查询详情、更新、归档
  - 验证：创建仍通过 Action Gate 和 Tool Registry
  - 测试：`python -m pytest -q` 通过，19 passed
- [x] Action Gate v1 原型
- [x] 用户确认卡原型
- [x] App Tool 白名单 / Tool Registry v1
  - 验证：`/api/tools` 可列出注册工具；未知工具执行会被 blocked
  - 验证：ActionService 通过 ToolRegistry 执行，不再直接硬编码执行分支
  - 测试：`python -m pytest -q` 通过，16 passed
- [x] Execution Log 原型
- [x] 天气 Provider v1
  - 验证：Open-Meteo Geocoding + Forecast 可真实查询，`北京` 返回 `ok` 和 3 天预报
  - 测试：`python -m pytest -q` 通过，8 passed

## 阶段 3：Skills 扩展

- [x] Skill Registry v1
  - 验证：`/api/skills` 可列出 MVP Skill Capability Contract
- [x] Skill Runtime v1
  - 验证：`POST /api/skills/{skill_id}/run` 可运行 Skill 并写入 `skill_runs`
  - 验证：`GET /api/skills/runs` 可查看运行历史
  - 测试：`python -m pytest -q` 通过，21 passed
- [x] 文件上传 v1
  - 验证：`POST /api/files/upload` 可保存文件到本地文件库并写入 `files`
  - 验证：`GET /api/files` 可查看上传记录
  - 测试：`python -m pytest -q` 通过，23 passed
- [x] 图片上传 v1
  - 验证：`POST /api/images/upload` 仅接受有效图片，保存文件并写入 `images`
  - 验证：记录图片宽高、content_type、file_id、status
  - 测试：`python -m pytest -q` 通过，25 passed
- [x] document.summarize 文本文件解析 v1
  - 验证：上传 `.txt/.md` 后可调用 `/api/files/{file_id}/summarize`
  - 验证：摘要通过 SkillRuntime 写入 `skill_runs`
  - 测试：`python -m pytest -q` 通过，26 passed
- [x] document.summarize PDF/DOCX 解析 v1
  - 验证：`FileService.extract_text` 支持 PDF/DOCX
  - 验证：`/api/files/{file_id}/summarize` 统一走 TXT/MD/PDF/DOCX 提取
  - 测试：`python -m pytest -q` 通过，30 passed
- [x] image.clothing_recognition v1
  - 验证：可基于图片像素颜色和文件名生成衣橱候选
  - 验证：识别结果通过 `wardrobe.add` 创建待确认 Action
  - 测试：`python -m pytest -q` 通过，31 passed
- [x] work.todo_extract v1
  - 验证：可从中文文本中提取“请、需要、确认、修复”等待办候选
  - 测试：`python -m pytest -q` 通过，27 passed
- [x] content.list_generate v1
  - 验证：支持上线、旅行、采购和通用清单模板
  - 测试：`python -m pytest -q` 通过，28 passed

## 阶段 4：智能场景编排

- [x] Scene Registry v1
  - 验证：`/api/scenes` 可创建、列表、详情、更新、暂停
  - 验证：`/api/scenes/{scene_id}/run` 可生成场景输出并写入 `scene_runs`
  - 验证：对话输入“创建...场景”可进入 `create_scene`
  - 测试：`python -m pytest -q` 通过，33 passed
- [x] Context Signal Pipeline v1
  - 验证：`/api/context-signals` 可收集、查询、归档上下文信号
  - 验证：支持按 `signal_type` 和 `status` 过滤
  - 测试：`python -m pytest -q` 通过，35 passed
- [x] Opportunity Engine v1
  - 验证：可从 `weather.rain` 信号生成带伞提醒机会
  - 验证：可从 `file.uploaded` 信号生成文档总结 Skill 推荐机会
  - 测试：`python -m pytest -q` 通过，37 passed
- [x] Attention Policy v1
  - 验证：`AttentionPolicy` 可按机会优先级输出 `interrupt`、`summary`、`silent`
  - 验证：高优先级机会会标记 `requires_confirmation=true`
  - 测试：`python -m pytest -q` 通过，41 passed
- [x] Recommendation Cards v1
  - 验证：`POST /api/recommendations/generate` 可基于 open opportunities 生成推荐卡片
  - 验证：同一 open opportunity 重复生成不会产生重复 open 推荐
  - 验证：`GET /api/recommendations` 可查询，`POST /api/recommendations/{id}/dismiss` 可忽略
  - 验证：客户端推荐面板可触发生成推荐，并可忽略 open 推荐
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过
- [x] Scene Feedback v1
  - 验证：`scene_feedback` 可记录 scene/run 反馈、rating、reason、payload
  - 验证：正向反馈提升 `effect_score`，误触发反馈降低评分且不低于 0
  - 验证：`POST /api/scenes/{scene_id}/feedback`、`GET /api/scenes/{scene_id}/feedback`、`GET /api/scene-feedback` 可用
  - 验证：客户端场景面板可标记“有效/误触发”，反馈面板可查看记录
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，41 passed

## 阶段 5：灵感智能体

- [x] Inspiration Agent v1 / Idea Card v1
  - 验证：灵感对话可生成结构化 Idea Card
  - 验证：支持 `divergent`、`challenge`、`first_principles`、`analogy`、`convergence`、`scenario` 模式识别
  - 验证：Idea Card 覆盖方向、目标用户、痛点、核心假设、反方挑战、跨域类比、MVP 方案、风险、下一步、评分
  - 验证：`idea.save` 可将结构化字段保存到 `idea_cards`
  - 验证：`GET /api/ideas`、`GET /api/ideas/{id}` 返回解析后的 `tags`、`risks`、`next_steps`
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，43 passed
- [x] Idea 转待办 v1
  - 验证：`todo_items` 可创建、查询、完成
  - 验证：`POST /api/ideas/{id}/to-todo` 可将 Idea Card 的 `next_steps` 转为待办
  - 验证：同一 Idea 重复转待办不会重复创建相同 `next_steps`
  - 验证：`GET /api/todos` 可查看待办，`POST /api/todos/{id}/complete` 可完成待办
  - 验证：客户端 Idea 面板可转待办，待办面板可完成条目
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，44 passed
- [x] Idea 转 PRD 草案 v1
  - 验证：`prd_drafts` 可保存 Idea 生成的 PRD 草案
  - 验证：`POST /api/ideas/{id}/to-prd` 可生成 PRD 草案，重复转换返回已有草案
  - 验证：`GET /api/prd-drafts`、`GET /api/prd-drafts/{id}` 可查询
  - 验证：客户端 Idea 面板可转 PRD，PRD 面板可查看草案
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，45 passed
- [x] Idea 转 Scene 草案 v1
  - 验证：`POST /api/ideas/{id}/to-scene` 可将 Idea Card 转为 Scene 草案
  - 验证：转换结果写入 Scene Registry，`source=idea`、`context_signal=idea:{id}`
  - 验证：同一 Idea 重复转换返回已有 Scene，不重复创建
  - 验证：客户端 Idea 面板可转场景，转换后跳转到场景面板
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，45 passed
- [x] 灵感偏好写入确认 v1
  - 验证：`POST /api/ideas/{id}/preference-candidate` 只生成记忆候选，不直接写长期记忆
  - 验证：生成的 Action 为 `memory.confirm_candidate`，确认后才写入 `memory_items`
  - 验证：客户端 Idea 面板可生成“记住偏好”确认卡
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，45 passed

## 阶段 6：安全、Eval、自主进化

- [x] Autonomy Zone Classifier v1
  - 验证：Green Zone 低风险优化可自动进入 Draft 或候选区
  - 验证：Yellow Zone 影响数据/偏好/提醒策略时必须确认
  - 验证：Red Zone 高风险、敏感、外发或不可逆动作只能建议，不能自主执行
  - 验证：`GET /api/autonomy/zones`、`POST /api/autonomy/classify` 可用
  - 验证：客户端自治面板可查看 Green/Yellow/Red 规则
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，47 passed
- [x] Eval Runner v1
  - 验证：`eval_runs` 可记录评测套件运行结果
  - 验证：内置 `autonomy.zone.basic` 套件覆盖 Green/Yellow/Red 三类边界
  - 验证：`GET /api/eval/suites`、`POST /api/eval/suites/{suite_id}/run`、`GET /api/eval/runs` 可用
  - 验证：客户端评测面板可运行并查看评测记录
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，49 passed
- [x] Growth Log v1
  - 验证：`growth_logs` 可记录优化内容、Zone、来源、影响范围和 payload
  - 验证：`GET /api/growth-log`、`POST /api/growth-log`、`POST /api/growth-log/{id}/rollback` 可用
  - 验证：回滚采用 `status=rolled_back` 和 `rolled_back_at` 记录，不物理删除
  - 验证：客户端成长面板可查看和回滚优化记录
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，51 passed
- [x] Yellow Zone 确认页 v1
  - 验证：`GET /api/yellow-zone/pending` 仅返回中风险待确认 Action
  - 验证：确认页复用 Action Gate 的确认/拒绝链路
  - 验证：客户端确认面板可查看 Yellow Zone 队列并确认/拒绝
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，52 passed
- [x] Red Zone 拦截强化 v1
  - 验证：删除、清空、支付、转账、授权、导出/分享等高风险请求会被标记 `blocked`
  - 验证：被 blocked 的对话不会创建 Action
  - 验证：`POST /api/red-zone/check` 和 `GET /api/red-zone/rules` 可用
  - 验证：客户端红区面板可查看阻断规则
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，54 passed
- [x] 安全策略设置 v1
  - 验证：`app_settings` 可保存本地安全/自主/Eval 策略
  - 验证：默认策略包含 `autonomy_enabled`、`yellow_zone_requires_confirmation`、`red_zone_policy`、`eval_required_for_drafts`
  - 验证：`GET /api/settings`、`PATCH /api/settings/{key}` 可用并校验非法值
  - 验证：客户端设置面板可切换布尔策略和 Red Zone 策略
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，56 passed

## 阶段 7：主动智能与外部集成

- [x] Provider Registry v1
  - 验证：`providers` 可记录外部服务状态、权限和配置
  - 验证：默认 Provider 包含 Open-Meteo 天气、日历、邮件、网盘占位
  - 验证：`GET /api/providers`、`POST /api/providers/{id}/connect`、`POST /api/providers/{id}/disconnect` 可用
  - 验证：客户端集成面板可连接/断开 Provider
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，58 passed
- [x] 主动建议中心 v1
  - 验证：`GET /api/proactive/suggestions` 可聚合 open 推荐、open 待办和未连接 Provider
  - 验证：建议卡包含 `type`、`title`、`priority`、`source_id`、`payload`
  - 验证：客户端主动面板可查看统一建议列表
  - 测试：`python -m compileall hermes_app tests`、`node --check hermes_app/web/static/app.js`、`python -m pytest -q` 通过，60 passed
- [ ] 轻量实时触发
- [ ] 每周灵感复盘
- [ ] 个性化首页卡片
- [ ] 新闻 Provider
- [ ] 地图 Provider

## GitHub / SVN 同步状态

- [x] 当前目录初始化 Git 仓库
- [x] 绑定远程仓库 `https://github.com/fm9333/HermesDemo.git`
- [x] 首次提交
  - commit：`f3e3241 stage 1 desktop shell and local service`
- [x] 推送 GitHub `main`
  - 远程：`origin/main`
- [x] 每个已验证小功能单独提交
  - 当前提交点：`stage-1-desktop-shell-local-service`
  - commit：`91aeb74 stage 1 desktop logging`
  - commit：`c67d12c stage 2 weather provider v1`
  - commit：`3a76b06 stage 2 task decomposer v1`
  - commit：`827b28f stage 2 memory candidate pipeline`
  - commit：`93cdbc8 stage 2 tool registry v1`
  - commit：`bdabf9f stage 2 reminder center v1`
  - commit：`ee3659d stage 2 wardrobe center v1`
  - commit：`b43fb37 stage 3 skill runtime v1`
  - commit：`ae947bb stage 3 file upload v1`
  - commit：`3f5712b stage 3 image upload v1`
  - commit：`5765d6d stage 3 document summarize text v1`
  - commit：`9831ab9 stage 3 work todo extract v1`
  - commit：`1c6e89d stage 3 content list generate v1`
  - commit：`c9f3503 stage 3 document summarize pdf docx v1`
  - commit：`e3986ff stage 3 image clothing recognition v1`
  - commit：`8af4950 stage 4 scene registry v1`
  - commit：`4787665 stage 4 context signal pipeline v1`
  - commit：`3479a07 stage 4 opportunity engine v1`
  - commit：`dbafd42 stage 4 attention recommendations v1`
  - commit：`77ae698 stage 4 scene feedback v1`
  - commit：`650fd6f stage 5 inspiration idea card v1`
  - commit：`9d6d4f4 stage 5 idea to todo v1`
  - commit：`6164f3b stage 5 idea to prd v1`
  - commit：`7eb185d stage 5 idea to scene v1`
  - commit：`90b237f stage 5 inspiration preference candidate v1`
  - commit：`03ea6c3 stage 6 autonomy zone classifier v1`
  - commit：`e2b3163 stage 6 eval runner v1`
  - commit：`8dd90b7 stage 6 growth log v1`
  - commit：`1e377b6 stage 6 yellow zone queue v1`
  - commit：`3328566 stage 6 red zone blocking v1`
  - commit：`826bfd5 stage 6 safety settings v1`
  - commit：`c2d829b stage 7 provider registry v1`
  - commit：`cc5dcf2 stage 7 proactive suggestions v1`

备注：当前工作目录已经绑定到 GitHub 仓库。后续每个验证通过的小功能继续按“开发 -> 测试 -> 评审 -> 勾选 -> commit -> push”的流程推进。
