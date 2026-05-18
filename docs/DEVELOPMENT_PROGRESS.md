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
- [x] Task Decomposer 占位
- [x] Memory Candidate Pipeline v1 原型
- [x] 记忆中心原型
- [x] 提醒创建原型
- [x] 衣橱基础管理原型
- [x] Action Gate v1 原型
- [x] 用户确认卡原型
- [x] Execution Log 原型
- [ ] 天气 Provider v1

## GitHub / SVN 同步状态

- [x] 当前目录初始化 Git 仓库
- [x] 绑定远程仓库 `https://github.com/fm9333/HermesDemo.git`
- [x] 首次提交
  - commit：`f3e3241 stage 1 desktop shell and local service`
- [x] 推送 GitHub `main`
  - 远程：`origin/main`
- [x] 每个已验证小功能单独提交
  - 当前提交点：`stage-1-desktop-shell-local-service`
  - 当前提交点：`stage-1-desktop-logging`

备注：当前工作目录已经绑定到 GitHub 仓库。后续每个验证通过的小功能继续按“开发 -> 测试 -> 评审 -> 勾选 -> commit -> push”的流程推进。
