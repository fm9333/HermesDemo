# Hermes 功能符合度审计

审计日期：2026-05-18  
审计范围：原始产品方案、桌面一体化开发计划、当前代码、API、测试和进度台账。

## 总结论

当前项目不是完整商用版 Hermes，而是：

```text
可运行的桌面一体化 MVP / 技术底座
+ 本地服务
+ 本地数据
+ Action Gate
+ MVP Skills
+ Scene / Inspiration / Autonomy 基础
+ OpenAI-compatible LLM Provider v1
```

如果验收标准是“可以演示、可以本地运行、可以继续迭代”，当前符合。

如果验收标准是“完全实现原始文档里所有功能、可直接商用发布”，当前不符合。

## 当前已满足

| 模块 | 当前状态 | 说明 |
|---|---|---|
| 桌面壳 | 基本完成 | PySide6 + QtWebEngine + 本地服务 + token |
| 本地服务 | 基本完成 | FastAPI + SQLite + 本地 API |
| 本地数据 | 基本完成 | SQLite、迁移、备份、导出、性能索引 |
| 主对话 | MVP 完成 | 支持意图路由、计划、LLM 普通对话 |
| LLM Provider | v1 完成 | OpenAI-compatible Chat Completions |
| Prompt Library | v1 完成 | Agent、Planner、Skill、Eval、Safety 提示词 |
| Action Gate | v1 完成 | 提醒、记忆、衣橱等变更需确认 |
| Memory | MVP 完成 | 候选、确认、拒绝、删除 |
| Reminder | MVP 完成 | 创建、列表、更新、完成、删除 |
| Wardrobe | MVP 完成 | 基础条目管理和图片识别候选 |
| Skills | MVP 完成 | document、image、todo、list 四类 |
| Personal Skill Draft | v1 完成 | 草案、来源 Skill Run、评测门禁、激活、归档、版本记录 |
| Inspiration | v1 完成 | Idea Card、转 Todo/PRD/Scene |
| Scene | v1 完成 | Scene、Signal、Opportunity、Recommendation、Feedback |
| Autonomy / Eval | 基础完成 | Zone、Eval Runner、Growth Log、Red Zone |
| Provider | 部分完成 | 天气、新闻、地图；日历/邮件/网盘仍占位 |
| 打包 | v1 完成 | PyInstaller 产物已验证 |

## 关键未满足

| 缺口 | 严重度 | 原因 |
|---|---:|---|
| Skill Patch / Skill Curator 未闭环 | P0 | Personal Skill Draft 已有 v1，但自动 Patch、治理和回滚仍缺 |
| 完整 Skills 清单未实现 | P0 | 合同、账单、归档、照片分类、日程、邮件、表格等缺失 |
| 云模型处理文件权限刚补 v1，还需 UI 策略完善 | P0 | 商用必须默认阻断敏感文件外发 |
| API Key 不是 OS Keychain/SQLCipher 级加密 | P0 | 当前只是本地保护保存 |
| 日历、邮件、网盘没有真实 OAuth Provider | P1 | 仍是本地占位 Provider |
| UI 不是完整模块化产品界面 | P1 | 当前是控制台式面板，不是完整页面/详情/向导 |
| 没有真实 Scheduler / Windows 通知闭环 | P1 | 提醒存在数据层，未形成系统通知产品闭环 |
| 没有 Responses API / 工具调用 / 流式输出 | P1 | LLM 能力仍是 Chat Completions v1 |
| 没有安装器、签名、自动更新安装链路 | P1 | PyInstaller 产物不是正式商用交付 |
| 没有真实 GUI 冒烟、性能、压力、长稳测试 | P1 | 当前主要是 API/服务层自动化测试 |

## 已发现并修复的风险

| 风险 | 修复状态 |
|---|---|
| 配置云模型后，文件总结可能把文件内容发给云端模型 | 已修复 v1 |
| API Key 接口可能泄漏完整密钥 | 已防止回显 |
| LLM 调用失败可能导致核心功能不可用 | 已 fallback 到本地规则 |

## 当前测试状态

最新全量测试命令：

```powershell
python -m compileall hermes_app tests
node --check hermes_app\web\static\app.js
python -m pytest -q
```

最新结果：

```text
110 passed, 2 warnings
```

## 下一步开发顺序

1. 完成云模型文件权限 UI 和策略审计。
2. 实现 Skill Patch 生成、Eval、激活、版本和回滚。
3. 实现 Skill Curator。
4. 补全完整 Skills 清单中的高价值技能。
5. 接入日历、邮件、网盘真实 Provider。
6. 升级密钥存储到 OS Keychain 或 SQLCipher。
7. 补正式安装器、签名、更新校验和 GUI 冒烟测试。
