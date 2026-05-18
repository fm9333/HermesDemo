# Hermes 产品方案：可扩展个人智能体与分区自主进化系统

归档日期：2026-05-18

## 1. 产品定位

Hermes 是一个面向 C 端用户的可扩展个人智能体系统。

它通过长期记忆理解用户，通过智能场景编排判断用户何时需要提醒、信息推荐或智能体协助，通过 App 工具安全完成确定性动作，通过 Skills 扩展文件、图片、工作和外部服务能力，通过灵感智能体帮助用户进行高强度思维碰撞，并在非敏感、低风险、可评测、可回滚的能力区域内实现自主进化。

Hermes 的目标不是做一个普通聊天助手，而是成为用户的个人智能体操作系统：

```text
记得住用户
能理解需求
能规划任务
能安全执行
能扩展能力
能激发灵感
能在低风险场景越用越会干活
```

核心原则：

```text
LLM 负责理解、生成草案、规划和低风险经验沉淀
后端负责校验、授权、执行、审计和回滚
用户保留最终控制权
非敏感能力允许自主进化
敏感能力必须受控进化
高风险操作禁止自主执行
```

## 2. 产品目标

1. 为每个用户提供一个长期陪伴的个人智能体。
2. 管理用户的记忆、偏好、提醒、家庭成员、新闻、天气、私人衣橱。
3. 支持用户通过自然语言创建任务和自动化场景。
4. 支持 App 内操作任务的安全规划与执行。
5. 通过 Skills 扩展文件、图片、工作、内容、数据和第三方服务能力。
6. 提供灵感智能体，帮助用户进行创新 idea 的碰撞、沉淀和推进。
7. 在不涉及敏感个人信息和高风险操作时，让 Hermes 能自主沉淀经验、优化 Skills 和工作流。
8. 让用户清楚知道 Hermes 记住了什么、创建了什么、执行了什么、优化了什么。

## 3. 总体产品定义

Hermes 可以被定义为：

```text
Hermes = 个人智能体 + 长期记忆 + 智能场景编排 + 受控 App 执行 + Skills 扩展 + 灵感智能体 + 分区自主进化
```

系统由 8 个核心模块组成：

```text
Hermes 主智能体
记忆系统 Memory
智能场景编排系统 Scene
受控执行系统 Action
Skills 扩展系统
灵感智能体 Inspiration
分区自主进化系统 Autonomy Zone
安全、审计与评测系统
```

## 4. 分区自主进化设计

### 4.1 为什么需要分区

Hermes 需要具备“越用越会干活”的能力，但 C 端系统涉及用户生活、家庭、位置、文件、图片、工作资料和隐私数据，不能全局放权。

因此系统采用分区自主策略：

```text
低风险通用能力：允许自主进化
中风险个人偏好：生成候选，轻量确认
高风险敏感能力：只允许建议，不允许自主执行
```

### 4.2 Autonomy Zone

| 区域 | 内容 | 自主进化权限 |
|---|---|---|
| Green Zone | 通用知识、文件格式处理、图片分类流程、工作流模板、灵感方法论、内容结构模板 | 可自主进化 |
| Yellow Zone | 用户偏好、衣橱建议、提醒策略、场景优化、个人工作流偏好 | 生成候选，需轻量确认或可撤销提示 |
| Red Zone | 家庭、健康、财务、身份、位置、删除、共享、批量修改、敏感文件 | 不允许自主执行，只允许建议或请求确认 |

### 4.3 Green Zone 可自主进化内容

Hermes 可以在 Green Zone 中自主优化：

```text
文件总结模板
会议纪要格式
待办提取流程
图片分类流程
衣物识别提示词
灵感碰撞方法
PRD 生成结构
周报生成格式
表格分析步骤
新闻摘要模板
通用内容生成模板
```

例如用户多次要求会议纪要按“结论、待办、风险、待确认问题”输出，Hermes 可以自动沉淀为个人 Skill。

### 4.4 Yellow Zone 候选进化内容

Yellow Zone 可以自动生成优化建议，但需要用户可感知、可修改、可撤销。

示例：

```text
我发现你经常希望会议记录按“结论-待办-风险”整理。以后我会默认用这个格式。
[知道了] [修改格式] [不要这样]
```

### 4.5 Red Zone 禁止自主进化内容

Red Zone 中 Hermes 不得自主修改策略或直接执行。

包括：

```text
健康报告长期记忆
家庭成员信息变更
财务文件保存和分析偏好
位置触发规则
删除衣橱或提醒
共享私人文件摘要
批量修改用户数据
代表用户对外发送消息
```

## 5. 自主进化闭环

Hermes 的自主进化流程：

```text
任务执行
→ 记录过程、输入、输出、用户反馈和成功信号
→ 判断是否属于 Green Zone
→ 判断是否存在可复用经验
→ 生成 Skill Patch 或 New Personal Skill
→ 自动安全检查
→ 自动 Eval
→ 通过后进入个人技能库
→ 后续自动调用
→ 持续统计效果
→ 表现下降时自动回滚或进入 Curator
```

必要门禁：

```text
Risk Classifier
Capability Contract
Skill Validator
Eval Runner
Rollback Manager
Skill Curator
Audit Log
```

## 6. Capability Contract

每个 Skill 都必须声明能力契约，确保 Hermes 可以进化能力，但不能扩大权限。

示例：

```json
{
  "skill_id": "work.todo_extract_from_meeting",
  "autonomy_zone": "green",
  "allowed_inputs": ["text", "docx", "pdf"],
  "allowed_outputs": ["summary", "todo_candidates"],
  "can_write_memory": false,
  "can_call_tools": ["todo.create_candidate"],
  "cannot_call_tools": ["reminder.create_without_confirmation", "file.share"],
  "requires_eval_before_activation": true,
  "rollback_supported": true
}
```

核心要求：

```text
Skill 可以变得更会处理任务
Skill 不能自动获得新权限
Skill 不能绕过用户确认
Skill 不能直接写入敏感长期记忆
Skill 不能调用 Red Zone Tool
```

## 7. 记忆系统 Memory

记忆系统用于保存用户长期信息、短期偏好、任务上下文和灵感偏好。

记忆类型：

| 类型 | 示例 | 策略 |
|---|---|---|
| 用户画像 | 生日、城市、职业 | 稳定保存 |
| 偏好记忆 | 喜欢科技新闻、不吃香菜 | 可自动写入或轻量提示 |
| 临时偏好 | 最近少吃辣 | 设置有效期 |
| 家庭记忆 | 妈妈生日、孩子年龄 | 建议确认 |
| 敏感记忆 | 健康、财务、身份信息 | 必须确认 |
| 任务记忆 | 当前任务上下文 | 任务结束后归档 |
| 灵感偏好 | 喜欢反方挑战、游戏化视角 | 用户确认后保存 |
| 工作流偏好 | 会议纪要默认格式 | Green/Yellow Zone 判断后保存 |

记忆写入流程：

```text
用户输入 / Skill 输出 / 灵感输出 / 自主进化建议
→ 提取 Memory Candidate
→ 分类
→ 去重
→ 冲突检测
→ 敏感性判断
→ 置信度评分
→ 写入短期/长期/待确认区
```

用户侧提供 Hermes 记忆中心：

```text
查看 Hermes 记住了什么
修改记忆
删除记忆
设为临时记忆
禁止某类记忆
确认待写入记忆
查看由自主进化产生的偏好
```

## 8. Skills 扩展系统

Skills 用于扩展 Hermes 对文件、图片、工作内容、内容生成、数据分析和外部服务的支持。

Skill 类型：

| Skill 类型 | 能力 |
|---|---|
| 文件类 | PDF 总结、合同提取、账单分析、文件归档 |
| 图片类 | 图片识别、衣物识别、穿搭分析、照片分类 |
| 工作类 | 待办提取、会议纪要、周报生成、日程规划 |
| 内容类 | 清单生成、PRD 生成、文案生成、旅行计划 |
| 数据类 | 表格分析、消费统计、预算整理 |
| 外部服务 | 天气、新闻、地图、日历、邮件、网盘 |
| 灵感类 | 反方挑战、跨域类比、第一性原理、MVP 收敛 |

Skill 分层：

```text
System Skill：平台官方提供，经过测试和审核
Personal Skill：用户个人使用，由自主进化或用户配置生成
Draft Skill：Hermes 根据经验生成的草案，未激活
Archived Skill：长期不用或效果下降，被归档但可恢复
```

Skill 调用流程：

```text
用户输入或事件触发
→ 判断是否需要 Skill
→ Skill Router 选择 Skill
→ 校验输入类型和权限
→ 查询 Skill 使用知识
→ 生成调用计划
→ 执行 Skill
→ 校验输出
→ 判断是否需要调用 Tool
→ 用户确认或自动执行
→ 返回结果
```

## 9. Skill 自主进化

Hermes 可以在满足条件时自动创建或优化 Personal Skill。

自动创建 Skill 的条件：

```text
任务不涉及敏感个人信息
不需要写入长期敏感记忆
不调用高风险 Tool
不涉及删除、共享、支付、授权
任务流程重复出现
用户对结果有正反馈
执行过程有明确成功信号
可以用测试样例验证
```

允许自动创建的例子：

```text
document.meeting_minutes_cn
image.wardrobe_tagging_basic
work.todo_extract_from_chat
inspiration.reverse_assumption_challenge
content.prd_mvp_outline
sheet.monthly_expense_summary
```

不允许自动创建后直接生效的例子：

```text
family_member_update
health_report_memory
delete_old_wardrobe_items
share_private_file_summary
location_based_monitoring
```

## 10. Skill Curator

Skill Curator 用于治理自主进化后产生的 Personal Skills。

职责：

```text
统计 Skill 使用频次
统计成功率和失败原因
识别重复或过窄 Skill
提出合并、修补、归档建议
自动归档低使用且低价值 Skill
禁止自动删除
支持恢复和版本回滚
```

Skill 生命周期：

```text
Draft
→ Eval Passed
→ Active
→ Stale
→ Archived
→ Restored / Removed by User
```

## 11. 智能场景编排系统 Scene

Scene 不是简单的自动化任务系统，也不只是用户明确创建的规则。

在 Hermes 中，Scene 的核心职责是：

```text
由 Hermes 持续理解用户所处情境
判断用户此刻或未来可能需要什么
决定是否提醒、推荐信息、推荐智能体、推荐 Skill 或生成可执行计划
管理用户注意力，避免无意义打扰
```

也就是说，Scene 是 Hermes 的“情境智能和主动推荐系统”，而不是传统意义上的任务列表。

### 11.1 Scene 的输出类型

一个场景被触发后，不一定执行 App 操作，可能产生多种输出：

| 输出类型 | 示例 | 说明 |
|---|---|---|
| 用户提醒 | 明天降雨，今晚提醒带伞 | Hermes 管理何时提醒用户 |
| 信息推荐 | 推荐天气、新闻、穿搭、家庭事项 | 用户可能需要的信息被主动送达 |
| 智能体推荐 | 推荐进入灵感智能体、衣橱智能体、工作智能体 | 用户可能需要一个专门智能体协助 |
| Skill 推荐 | 推荐使用文档总结、图片识别、待办提取 | 用户可能需要一个能力扩展 |
| App 操作建议 | 建议创建提醒、加入衣橱、生成场景 | 先建议，必要时确认后执行 |
| 静默沉淀 | 更新候选记忆、场景信号、用户偏好信号 | 不打扰用户，只增强后续判断 |

### 11.2 Hermes 管理提醒，而不是提醒系统管理 Hermes

提醒不应该只是用户设置的定时闹钟。

Hermes 需要决定：

```text
是否真的需要提醒
什么时候提醒最合适
是否合并到摘要里
是否只在 App 首页展示
是否延后提醒
是否不打扰用户
是否需要推荐信息或智能体，而不是直接提醒
```

示例：

```text
明天有雨 + 用户明早通勤 + 用户常忘带伞
→ 今晚 21:00 轻提醒
→ 明早出门前如果仍有雨，再二次提醒

明天有雨 + 用户没有出行安排
→ 不推送
→ 只在首页天气卡展示
```

### 11.3 Scene 的结构

Scene 不再只由 Trigger、Condition、Action 组成，而是由更完整的情境决策结构组成：

```text
Context Signal：场景信号，来自时间、天气、日程、位置、行为、文件、图片、对话等
User State：用户状态，包括偏好、免打扰、近期行为、任务上下文
Opportunity：Hermes 识别出的机会点，例如提醒、推荐、建议、智能体介入
Decision Policy：是否打扰用户、如何呈现、是否需要确认
Output：提醒、信息推荐、智能体推荐、Skill 推荐、App 操作建议或静默沉淀
Feedback：用户点击、忽略、关闭、修改后的反馈
```

### 11.4 Scene 创建来源

Scene 可以来自三类来源：

```text
用户显式表达：以后下雨前提醒我带伞
Hermes 主动发现：你经常在下雨前问穿搭，要不要开启雨天穿搭建议
系统内置场景：生日、天气、新闻、衣橱、灵感复盘、文件处理建议
```

### 11.5 Scene 运行流程

```text
定时触发 / 实时事件 / 用户行为 / 对话上下文
→ 收集 Context Signal
→ Precheck Gate 判断是否值得唤醒 Hermes
→ 读取必要记忆和用户状态
→ 识别 Opportunity
→ Attention Policy 判断是否打扰用户
→ 生成推荐、提醒、智能体建议或执行草案
→ 风险和权限校验
→ 用户反馈或静默沉淀
→ 更新场景效果评分
```

### 11.6 Scene 的成功标准

Scene 的目标不是“执行了多少任务”，而是：

```text
用户是否在正确时间获得了有用信息
用户是否减少了遗忘和决策成本
Hermes 是否少打扰但更有帮助
推荐的智能体或 Skill 是否被用户接受
场景是否能随着用户反馈变得更准
```

## 12. 受控执行系统 Action

Action 不再被定义为独立的“App 操作系统”，而是 Hermes 在完成场景判断、用户请求或智能体规划后，用来安全改变 App 状态的受控执行层。

它的职责是：

```text
不负责判断用户需要什么
不负责决定什么时候提醒
不负责做主动推荐
只负责在 Hermes 决策明确后，安全、可验证地执行 App 内动作
```

典型 Action：

```text
创建提醒
更新偏好
创建衣橱草案
加入衣橱
创建信息推荐卡
创建智能体推荐卡
保存 Idea Card
生成待办候选
暂停或更新场景
删除或批量修改数据
```

Action 执行流程：

```text
Hermes / Scene / Skill / Inspiration 生成执行意图
→ 查询 Tool Registry 和 App 能力知识库
→ 生成结构化执行计划
→ 参数校验
→ 权限校验
→ 风险校验
→ 必要时用户确认
→ 调用 Tool 执行
→ 验证结果
→ 记录 Execution Log
→ 将结果反馈给 Hermes 和用户
```

原则：

```text
Hermes 负责判断和编排
Action 负责确定性执行
所有工具必须注册在 Tool Registry
LLM 不能直接写数据库
LLM 不能自由调用 API
高风险操作必须用户确认
批量操作优先 Dry Run
所有执行必须记录日志
自主进化不能扩大 Tool 权限
```

## 13. 灵感智能体 Inspiration Agent

灵感智能体是 Hermes 内的创新思维模块。

用户可以和灵感智能体进行开放式讨论、激烈碰撞、反方挑战、跨域类比和方案推演，最终形成新的创新 idea。

支持模式：

| 模式 | 作用 |
|---|---|
| 发散模式 | 快速生成大量 idea |
| 反方挑战 | 挑战用户假设，指出盲区 |
| 第一性原理 | 拆解底层需求和真实动机 |
| 跨域类比 | 从其他领域迁移灵感 |
| 场景推演 | 放入真实用户场景中测试 |
| 收敛评估 | 从价值、可行性、差异化筛选 |

灵感交互流程：

```text
用户提出方向
→ 澄清目标
→ 发散生成 idea
→ 反方挑战
→ 跨域类比
→ 场景推演
→ 收敛筛选
→ 生成 Idea Card
→ 保存 / 转任务 / 转场景 / 继续碰撞
```

灵感智能体也可以自主进化，但仅限 Green Zone：

```text
优化提问方式
优化反方挑战框架
优化 Idea Card 结构
优化 MVP 收敛模板
```

如果涉及用户长期偏好，例如“以后都用更激进的挑战方式”，则进入 Yellow Zone，需用户确认或可撤销提示。

## 14. 触发机制

Hermes 支持三类触发。

### 14.1 被动触发

用户主动输入：

```text
聊天
创建提醒
上传文件
上传图片
创建场景
调用灵感智能体
处理工作内容
```

### 14.2 定时触发

系统按时间唤醒：

```text
提醒到期
每日天气
新闻摘要
穿搭建议
生日提醒
记忆整理
灵感复盘
场景条件检查
Skill Curator 检查
```

### 14.3 实时触发

事件发生后唤醒：

```text
天气突变
用户上传衣物
用户打开 App
日程变化
位置变化
重要新闻
文件上传完成
```

所有触发统一进入 Event Gateway，再由 Intent Router 分流。

## 15. 用户体验设计

Hermes 统一使用五种反馈状态。

### 15.1 已完成

```text
已为你创建明天早上 8 点的带伞提醒。
```

### 15.2 待确认

```text
我可以为你开启“雨天通勤提醒”。
它会每天晚上检查天气和通勤安排，满足条件时提醒你带伞。

[确认开启] [修改条件] [取消]
```

### 15.3 需补充

```text
你想让我什么时候检查天气？前一晚、当天早上，还是出门前 1 小时？
```

### 15.4 已沉淀

```text
我把这次碰撞沉淀成一张 idea 卡片了。

[保存到灵感库] [转成待办] [继续挑战] [生成产品方案]
```

### 15.5 已优化

用于展示 Hermes 的自主成长。

```text
我发现你常把会议记录整理成“结论-待办-风险”格式。
以后处理会议记录时，我会默认使用这个结构。

[知道了] [修改格式] [恢复默认]
```

用户侧新增“成长记录”：

```text
Hermes 最近优化了什么
新增了哪些个人 Skills
哪些优化正在生效
哪些优化被回滚
关闭自主优化
恢复默认设置
```

## 16. 系统架构

```text
C 端 App
  ↓
Conversation / Event Gateway
  ↓
Intent Router
  ↓
Task Decomposer
  ↓
--------------------------------------------------------
| Hermes Agent | Inspiration Agent | Skill Pipeline |
--------------------------------------------------------
  ↓
--------------------------------------------------------
| Memory Pipeline | Context Signal Pipeline | Scene Orchestration |
--------------------------------------------------------
  ↓
Opportunity Engine / Attention Policy
  ↓
--------------------------------------------------------
| Recommendation Pipeline | Reminder Decision | Action Planning |
--------------------------------------------------------
  ↓
Autonomy Zone Classifier
  ↓
Knowledge Base / Skill Registry / Tool Registry
  ↓
Validator + Policy Engine
  ↓
User Confirmation / Auto Execution Gate
  ↓
Skill Runtime / Tool Executor
  ↓
Result Verifier
  ↓
Memory Store / Scene Registry / Idea Library / Execution Log
  ↓
Eval Center / Skill Curator / Growth Log
```

## 17. 安全与权限设计

风险等级：

| 风险等级 | 示例 | 处理方式 |
|---|---|---|
| 低风险 | 查询天气、生成灵感、通用文件摘要、推荐穿搭 | 可直接执行 |
| 中风险 | 创建提醒、更新普通偏好、优化个人工作流偏好 | 执行后反馈或轻确认 |
| 高风险 | 删除数据、修改家庭成员、批量操作 | 必须确认 |
| 敏感风险 | 健康、财务、身份、私密文件、位置 | 必须确认并限制记忆 |
| 禁止执行 | 越权访问、未知工具、导出隐私、绕过确认 | 拒绝执行 |

安全机制：

```text
Autonomy Zone Classifier
Capability Contract
Policy Engine
Schema Validator
Tool Registry
Skill Registry
Execution Log
Dry Run
Idempotency Key
Result Verifier
Memory Candidate
User Confirmation
Eval Runner
Rollback Manager
Skill Curator
```

## 18. Eval Center

Hermes 的自主进化必须绑定评测。

评测类型：

```text
Intent Eval
Memory Eval
Skill Selection Eval
Skill Patch Eval
Scene Generation Eval
Tool Plan Eval
Safety Eval
Inspiration Eval
Autonomy Zone Eval
```

Skill Patch 自动评测流程：

```text
输入样例
→ 旧 Skill 输出
→ 新 Skill 输出
→ 规则评测
→ LLM Judge
→ 安全检查
→ 输出结构校验
→ 回归测试
→ 通过后启用
```

评测维度：

```text
输出是否符合 schema
是否遗漏关键信息
是否引入敏感记忆
是否请求了不该有的权限
是否比旧版本更稳定
是否能处理边界输入
用户是否更少修改结果
```

## 19. MVP 范围

第一阶段 MVP 建议包含：

```text
Hermes 主对话入口
基础意图识别
任务拆解
Memory Candidate Pipeline
记忆中心
提醒创建
天气查询
衣橱基础管理
App Tool 白名单
用户确认卡
定时提醒触发
执行日志
```

Skills MVP：

```text
document.summarize：文档总结
image.clothing_recognition：衣物识别
work.todo_extract：待办提取
content.list_generate：清单生成
```

灵感 MVP：

```text
灵感对话入口
发散模式
反方挑战模式
Idea Card 生成
灵感库保存
Idea 转待办
Idea 转 PRD 草案
```

自主进化 MVP：

```text
Autonomy Zone Classifier v1
Personal Skill Draft
Skill Patch Eval v1
Green Zone 自动优化
Growth Log 成长记录
Rollback v1
Skill Curator v1
```

暂缓：

```text
复杂实时触发
跨 App 操作
自动删除类操作
任意第三方 Skill
复杂家庭权限协作
全自动主动推送
Red Zone 自主进化
平台级 Skill 自动发布
```

## 20. 阶段规划

### 20.1 第一阶段：基础 Hermes

```text
对话
记忆
提醒
天气
衣橱
基础 App 操作
执行日志
```

### 20.2 第二阶段：Skills 扩展

```text
文件总结
图片识别
待办提取
清单生成
Skill Registry
Skill Permission
Capability Contract
```

### 20.3 第三阶段：智能场景编排

```text
Context Signal Pipeline
Opportunity Engine
Attention Policy
提醒决策
信息推荐
智能体推荐
Precheck Gate
Scene Registry
场景中心
```

### 20.4 第四阶段：灵感智能体

```text
灵感入口
Idea Card
灵感库
反方挑战
Idea 转任务/文档/场景
```

### 20.5 第五阶段：分区自主进化

```text
Autonomy Zone
Personal Skill 自动生成
Skill Patch 自动评测
Growth Log
Skill Curator
Rollback
```

### 20.6 第六阶段：主动智能

```text
主动建议
轻量实时触发
每周灵感复盘
个性化首页卡片
复杂 App 操作
跨模块协作
```

## 21. 成功指标

产品指标：

```text
7 日留存
30 日留存
用户主动对话频次
提醒创建成功率
衣橱录入完成率
灵感保存率
Idea 转任务率
用户关闭率
用户投诉率
```

智能体质量指标：

```text
意图识别准确率
任务拆解准确率
记忆写入准确率
记忆冲突率
场景生成成功率
场景误触发率
App 操作成功率
Skill 选择准确率
Skill 输出可用率
高风险确认命中率
重复执行率
```

自主进化指标：

```text
Personal Skill 创建数
Skill Patch 通过率
Skill 回滚率
用户接受优化率
用户撤销优化率
优化后结果修改率下降幅度
Green Zone 误判率
Yellow/Red Zone 拦截率
```

## 22. 最终定义

Hermes 是一个面向 C 端用户的可扩展个人智能体系统。它通过长期记忆理解用户，通过智能场景编排判断用户何时需要提醒、信息推荐或智能体协助，通过 App 工具安全完成确定性动作，通过 Skills 扩展文件、图片、工作和外部服务能力，通过灵感智能体帮助用户进行高强度思维碰撞，并通过分区自主进化机制在低风险非敏感场景中越用越会干活。

它不是完全自由行动的 agent，而是一个具备成长能力的受控型个人智能体：

```text
Green Zone 自主进化
Yellow Zone 候选确认
Red Zone 严格受控
所有能力可评测、可审计、可回滚、可关闭
```

这使 Hermes 同时具备开源 Hermes Agent 的成长性，以及 C 端产品所需要的安全性、可解释性和用户信任。
