# Hermes 桌面一体化产品开发计划

版本：v1  
日期：2026-05-18  
目标形态：可直接在桌面运行的个人智能体程序，客户端、嵌入式服务端、本地数据、模型配置、日志、技能与用户资产全部在一个应用内完成管理。

## 1. 产品结论

Hermes 最终要做成一个“受控型个人智能体桌面操作台”，不是普通聊天窗口。

它需要同时满足：

```text
能聊天理解需求
能记住用户
能管理提醒、天气、新闻、衣橱、文件、图片、工作内容
能通过 Skills 扩展能力
能通过 Scene 主动判断是否提醒或推荐
能通过 Action 安全执行 App 内动作
能通过 Inspiration Agent 做灵感碰撞
能在 Green Zone 低风险区域自主进化
能让用户看到、确认、回滚、关闭所有重要变化
```

桌面版的核心产品形态：

```text
Hermes Desktop
  = Desktop Shell
  + Embedded Python Service
  + Local Client UI
  + Local Database
  + Local File Store
  + Model / Tool / Skill / Eval 管理
```

## 2. 桌面一体化架构

### 2.1 推荐技术路线

第一版以 Windows 桌面为主，保留跨平台空间。

```text
桌面壳：PySide6 + QtWebEngine
本地服务：FastAPI + Uvicorn embedded server
本地数据库：SQLite，后续可升级 SQLCipher 加密
本地文件库：AppData/Hermes/files
向量索引：sqlite-vec 或 Chroma 本地模式
任务调度：APScheduler
打包：PyInstaller
前端 UI：本地 Web UI，运行在 QtWebEngine 内
模型适配：LLM Adapter，支持云模型和本地模型
系统通知：Windows Toast Notification
系统托盘：PySide6 Tray
```

### 2.2 运行方式

用户启动 `Hermes.exe` 后：

```text
1. Desktop Shell 启动
2. 检查本地数据目录和配置
3. 启动 Embedded FastAPI 服务
4. 自动选择 localhost 随机端口
5. 生成一次性本地访问 token
6. QtWebEngine 加载本地客户端
7. Scheduler 启动定时任务
8. Tray 常驻，负责提醒和后台任务
```

本地服务只监听：

```text
127.0.0.1
```

所有请求都带本地 token，避免其他本机进程随意访问 Hermes API。

### 2.3 进程结构

MVP 先采用单进程多线程：

```text
Hermes.exe
  Main Thread: PySide6 Desktop Shell
  Service Thread: FastAPI/Uvicorn
  Scheduler Thread: reminder / scene / curator jobs
  Worker Pool: file parsing / image analysis / eval jobs
```

正式版可升级为主进程加服务子进程：

```text
Hermes Desktop Process
Hermes Local Service Process
Hermes Worker Process
```

### 2.4 本地目录

```text
%APPDATA%/Hermes/
  config/settings.json
  data/hermes.db
  data/vector.index
  files/uploads/
  files/generated/
  files/exports/
  logs/app.log
  logs/execution.log
  skills/system/
  skills/personal/
  skills/draft/
  evals/
  backups/
```

开发环境继续使用当前项目目录：

```text
D:\Work\FMDemo\hermes
```

## 3. 服务端模块设计

服务端是产品核心，不只是 API。

### 3.1 Conversation / Event Gateway

职责：

```text
接收用户聊天输入
接收文件、图片、事件、定时触发
统一标准化为 Hermes Event
写入事件日志
转发给 Intent Router
```

输入来源：

```text
聊天框
快捷命令
文件上传
图片上传
提醒到期
天气变化
日程变化
用户打开 App
Skill Curator 定时检查
```

### 3.2 Intent Router

职责：

```text
识别用户意图
判断是否需要任务拆解
判断是否需要 Skill
判断是否需要 Scene
判断是否需要 Action
```

必须支持的意图：

```text
普通对话
创建提醒
查询天气
新闻摘要
记忆写入
记忆查询
记忆修改
记忆删除
衣橱录入
穿搭建议
上传文件处理
上传图片处理
待办提取
会议纪要
清单生成
PRD 生成
灵感碰撞
创建场景
修改场景
暂停场景
Skill 调用
Skill 创建建议
自主优化确认
高风险操作确认
```

### 3.3 Task Decomposer

职责：

```text
将复杂请求拆成可执行步骤
为每一步标记输入、输出、依赖、风险等级、需要的 Skill 或 Tool
生成计划预览
交给用户确认或进入自动执行 Gate
```

示例：

```text
“帮我把这个会议记录总结成待办，并明天提醒我跟进”
  1. 调用 document.summarize
  2. 调用 work.todo_extract
  3. 生成 reminder.create 候选
  4. 因创建提醒属于中风险，展示确认卡
```

### 3.4 Hermes Agent

职责：

```text
理解用户上下文
协调 Memory、Scene、Skill、Action、Inspiration
生成自然语言回复
生成结构化计划
不直接写数据库
不直接调用外部 API
```

### 3.5 Memory Pipeline

功能：

```text
Memory Candidate 提取
分类
去重
冲突检测
敏感性判断
置信度评分
写入短期记忆
写入长期记忆
进入待确认区
回滚和删除
禁止某类记忆
```

记忆类型：

```text
用户画像
偏好记忆
临时偏好
家庭记忆
敏感记忆
任务记忆
灵感偏好
工作流偏好
自主进化产生的偏好
```

### 3.6 Context Signal Pipeline

职责：

```text
收集场景信号
归一化信号
计算有效期
判断是否值得唤醒 Hermes
```

信号来源：

```text
时间
天气
日程
位置，默认关闭
用户行为
文件上传
图片上传
对话上下文
提醒历史
用户反馈
```

### 3.7 Scene Orchestration

职责：

```text
理解用户处境
识别 Opportunity
决定是否打扰用户
生成提醒、信息推荐、智能体推荐、Skill 推荐、App 操作建议或静默沉淀
```

Scene 结构：

```text
Context Signal
User State
Opportunity
Decision Policy
Output
Feedback
Effect Score
```

### 3.8 Action Planning / Action Gate

职责：

```text
接收 Hermes、Scene、Skill、Inspiration 生成的执行意图
查询 Tool Registry
生成结构化执行计划
参数校验
权限校验
风险校验
必要时用户确认
执行 Tool
验证结果
写 Execution Log
```

原则：

```text
LLM 不直接写数据库
LLM 不自由调用 API
所有 Tool 必须注册
高风险操作必须确认
批量操作必须 Dry Run
所有执行必须可审计
```

### 3.9 Skills 系统

Skill 分层：

```text
System Skill
Personal Skill
Draft Skill
Archived Skill
```

MVP Skills：

```text
document.summarize
image.clothing_recognition
work.todo_extract
content.list_generate
```

完整 Skills：

```text
PDF 总结
合同提取
账单分析
文件归档
图片识别
衣物识别
穿搭分析
照片分类
待办提取
会议纪要
周报生成
日程规划
清单生成
PRD 生成
文案生成
旅行计划
表格分析
消费统计
预算整理
天气查询
新闻摘要
地图查询
日历读取
邮件摘要
网盘文件处理
反方挑战
跨域类比
第一性原理
MVP 收敛
```

### 3.10 Inspiration Agent

模式：

```text
发散模式
反方挑战
第一性原理
跨域类比
场景推演
收敛评估
```

输出：

```text
Idea Card
任务候选
PRD 草案
Scene 草案
继续碰撞问题
```

### 3.11 Autonomy Zone

分区：

```text
Green Zone: 可自主进化
Yellow Zone: 候选确认或可撤销提示
Red Zone: 严格受控，只能建议或请求确认
```

必须实现的门禁：

```text
Risk Classifier
Capability Contract
Skill Validator
Eval Runner
Rollback Manager
Skill Curator
Audit Log
```

### 3.12 Eval Center

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

每次 Skill Patch 启用前必须经过：

```text
输入样例
旧 Skill 输出
新 Skill 输出
规则评测
LLM Judge
安全检查
输出结构校验
回归测试
通过后启用
```

## 4. 客户端页面设计

桌面客户端不是网页后台，而是用户每天打开的个人智能体工作台。

### 4.1 主窗口布局

```text
顶部栏：
  App 名称
  当前模型状态
  同步/本地状态
  全局搜索
  通知入口
  设置入口

左侧主导航：
  首页
  Hermes 对话
  记忆中心
  提醒与场景
  Action 中心
  Skills
  灵感工作室
  文件与图片
  衣橱
  Eval Center
  成长记录
  设置

中间内容区：
  当前页面主体

右侧上下文面板：
  当前对话上下文
  待确认操作
  相关记忆
  相关 Skill
  最近执行日志
```

### 4.2 首页 Dashboard

页面目标：

```text
让用户打开应用后立即知道今天 Hermes 认为重要的事情。
```

模块：

```text
今日摘要
待确认 Action
即将到期提醒
天气与通勤建议
新闻摘要
衣橱/穿搭建议
最近 Idea Card
最近成长记录
异常或失败任务
```

跳转逻辑：

```text
点击待确认 Action -> Action 中心详情
点击提醒 -> 提醒详情
点击天气建议 -> Scene 输出详情
点击 Idea -> 灵感工作室详情
点击成长记录 -> Growth Log 详情
```

### 4.3 Hermes 对话页

页面目标：

```text
所有用户自然语言请求的主入口。
```

组件：

```text
消息列表
输入框
附件上传
模式选择：普通 / 工作 / 灵感 / 文件 / 场景
上下文选择：使用哪些记忆、文件、场景
计划预览卡
确认卡
补充问题卡
结果卡
```

状态：

```text
已完成
待确认
需补充
已沉淀
已优化
执行失败
```

跳转逻辑：

```text
确认创建提醒 -> 写入提醒并跳转提醒详情
确认写入记忆 -> 写入记忆并跳转记忆详情
保存 Idea -> 进入 Idea Card 详情
调用 Skill -> 打开 Skill 结果详情
高风险操作 -> 打开 Action Dry Run 详情
```

### 4.4 记忆中心

页面目标：

```text
让用户清楚知道 Hermes 记住了什么，以及为什么记住。
```

Tab：

```text
全部记忆
待确认
用户画像
偏好
临时偏好
家庭
敏感
任务上下文
灵感偏好
工作流偏好
自主优化产生的记忆
已归档
```

列表字段：

```text
记忆内容
类型
来源
置信度
敏感等级
创建时间
有效期
最近使用时间
状态
```

详情页操作：

```text
编辑
删除
设为临时
延长有效期
禁止同类记忆
查看来源对话
查看使用记录
回滚修改
```

跳转逻辑：

```text
来源对话 -> Hermes 对话页定位消息
使用记录 -> Execution Log
自主优化来源 -> Growth Log
```

### 4.5 提醒与场景中心

页面目标：

```text
管理提醒、主动推荐、Scene 和 Attention Policy。
```

一级 Tab：

```text
提醒
场景
推荐
触发历史
静默沉淀
```

提醒页：

```text
日历视图
列表视图
即将到期
已完成
已暂停
重复提醒
```

场景页字段：

```text
Scene 名称
来源：用户创建 / Hermes 主动发现 / 系统内置
Context Signal
User State
Opportunity
Decision Policy
Output 类型
风险等级
效果评分
状态
```

Scene 创建向导：

```text
选择触发来源
设置条件
设置打扰策略
设置输出类型
设置确认要求
预览运行结果
保存 Scene
```

跳转逻辑：

```text
Scene 输出提醒 -> 提醒详情
Scene 输出推荐 -> 推荐详情
Scene 输出 Skill 推荐 -> Skill 详情
Scene 误触发 -> Feedback 面板
```

### 4.6 Action 中心

页面目标：

```text
集中管理所有会改变 App 状态的动作。
```

Tab：

```text
待确认
执行中
已完成
失败
已拒绝
Dry Run
高风险
```

每个 Action 显示：

```text
动作类型
来源模块
风险等级
执行计划
参数
影响范围
是否可回滚
确认按钮
拒绝按钮
修改参数
查看日志
```

高风险规则：

```text
删除数据
修改家庭成员
批量操作
共享文件
代表用户发送消息
位置触发规则
健康财务身份相关操作
```

跳转逻辑：

```text
执行成功 -> 对应资源详情页
执行失败 -> 错误日志详情
可回滚 -> 回滚确认页
```

### 4.7 Skills 中心

页面目标：

```text
管理 Hermes 的能力扩展。
```

Tab：

```text
System Skills
Personal Skills
Draft Skills
Archived Skills
Skill Curator
Capability Contracts
```

Skill 详情：

```text
Skill ID
名称
类型
Autonomy Zone
输入类型
输出类型
可调用 Tool
禁止调用 Tool
是否可写记忆
是否需要 Eval
版本列表
使用次数
成功率
失败原因
最近输出样例
回滚按钮
归档按钮
```

Skill Curator 页面：

```text
重复 Skill 建议
低价值 Skill 建议归档
表现下降 Skill
待合并 Skill
待修补 Skill
自动回滚记录
```

跳转逻辑：

```text
Draft Skill -> Eval Center 创建测试
Eval 通过 -> 激活 Personal Skill
表现下降 -> Curator 详情
回滚 -> Skill 版本详情
```

### 4.8 灵感工作室

页面目标：

```text
支持高强度 idea 碰撞、沉淀和推进。
```

布局：

```text
左侧：Idea 库
中间：灵感对话
右侧：Idea Card / 方法模式 / 收敛评分
```

模式：

```text
发散模式
反方挑战
第一性原理
跨域类比
场景推演
收敛评估
```

Idea Card 字段：

```text
标题
方向
目标用户
痛点
核心假设
反方挑战
跨域类比
MVP 方案
风险
下一步
标签
状态
```

操作：

```text
保存到灵感库
转成待办
转成 PRD 草案
转成 Scene 草案
继续挑战
归档
```

### 4.9 文件与图片中心

页面目标：

```text
管理上传文件、图片处理、摘要、归档和工作内容提取。
```

Tab：

```text
最近上传
文档
图片
处理结果
待办候选
文件归档
```

功能：

```text
拖拽上传
PDF 总结
合同提取
账单分析
会议纪要
待办提取
图片识别
照片分类
衣物识别
```

跳转逻辑：

```text
文档总结 -> Skill Result
待办候选 -> Action 中心确认
衣物识别 -> 衣橱草案
敏感文件 -> 权限确认
```

### 4.10 衣橱中心

页面目标：

```text
管理私人衣橱、穿搭建议和天气场景联动。
```

页面：

```text
衣物列表
添加衣物
分类管理
标签管理
穿搭建议
天气联动
衣橱场景
```

衣物字段：

```text
名称
分类
颜色
季节
场合
材质
图片
标签
使用频率
是否归档
```

跳转逻辑：

```text
上传衣物图片 -> image.clothing_recognition
穿搭建议 -> Scene 输出或 Skill 输出
删除衣物 -> 高风险确认
雨天穿搭建议 -> Scene 详情
```

### 4.11 Eval Center

页面目标：

```text
为自主进化、Skill Patch、场景生成和安全策略提供可见评测。
```

Tab：

```text
Eval Suites
Eval Runs
失败样例
LLM Judge
Safety Eval
Regression
```

Eval Run 显示：

```text
评测对象
版本
测试样例数
通过率
失败原因
安全拦截
是否允许启用
```

跳转逻辑：

```text
Skill Patch -> Eval Run
Eval 失败 -> Patch 详情
Eval 通过 -> 激活 Skill
```

### 4.12 成长记录 Growth Log

页面目标：

```text
让用户知道 Hermes 最近优化了什么。
```

内容：

```text
新增 Personal Skill
优化的模板
优化的工作流偏好
已回滚优化
待确认优化
表现下降提醒
关闭自主优化入口
恢复默认设置入口
```

每条记录显示：

```text
优化内容
所属 Zone
来源任务
评测结果
影响范围
生效状态
撤销按钮
```

### 4.13 设置中心

页面目标：

```text
管理模型、隐私、安全、本地数据、通知和集成。
```

设置分组：

```text
账号与用户画像
模型 Provider
本地数据目录
数据库备份
导入导出
隐私与敏感记忆
通知策略
权限管理
Tool Registry
Skill 管理
Scene 默认策略
自主进化开关
Eval 策略
日志与审计
关于与版本更新
```

重要配置：

```text
默认 LLM Provider
API Key 本地加密保存
是否允许云模型处理文件
是否允许位置权限
是否允许主动推送
是否允许 Green Zone 自主进化
Yellow Zone 确认策略
Red Zone 拦截策略
自动备份频率
日志保留天数
```

## 5. 本地数据模型

核心表：

```text
users
settings
model_providers
memory_items
memory_candidates
memory_events
reminders
scenes
scene_runs
context_signals
opportunities
recommendations
actions
execution_logs
tools
tool_permissions
skills
skill_versions
skill_contracts
skill_runs
skill_patches
skill_curator_reports
eval_suites
eval_cases
eval_runs
eval_results
idea_cards
idea_links
files
file_artifacts
images
wardrobe_items
wardrobe_tags
news_cache
weather_cache
notifications
audit_logs
growth_logs
backups
```

数据分区：

```text
结构化数据：SQLite
大文件：本地文件库
向量索引：本地向量库
密钥：系统 Keyring
日志：滚动文件 + SQLite 索引
备份：压缩包，可加密
```

## 6. API 设计

客户端调用本地 API。

```text
POST /api/chat
POST /api/events

GET  /api/memory
POST /api/memory/candidates
POST /api/memory/{id}/confirm
PATCH /api/memory/{id}
DELETE /api/memory/{id}

GET  /api/reminders
POST /api/reminders
PATCH /api/reminders/{id}
DELETE /api/reminders/{id}

GET  /api/scenes
POST /api/scenes
POST /api/scenes/{id}/run
PATCH /api/scenes/{id}
POST /api/scenes/{id}/pause

GET  /api/actions
POST /api/actions/{id}/confirm
POST /api/actions/{id}/reject
POST /api/actions/{id}/dry-run
POST /api/actions/{id}/rollback

GET  /api/skills
POST /api/skills/{id}/run
POST /api/skills/{id}/patch
POST /api/skills/{id}/archive
POST /api/skills/{id}/rollback

GET  /api/inspiration/ideas
POST /api/inspiration/session
POST /api/inspiration/ideas/{id}/to-task
POST /api/inspiration/ideas/{id}/to-prd
POST /api/inspiration/ideas/{id}/to-scene

POST /api/files/upload
POST /api/files/{id}/process
GET  /api/files/{id}/artifacts

GET  /api/wardrobe
POST /api/wardrobe
PATCH /api/wardrobe/{id}
DELETE /api/wardrobe/{id}

GET  /api/evals
POST /api/evals/run
GET  /api/evals/runs/{id}

GET  /api/growth-log
POST /api/growth-log/{id}/rollback

GET  /api/settings
PATCH /api/settings
POST /api/backups/create
POST /api/backups/restore
```

## 7. 开发阶段计划

完整产品建议按 8 个阶段推进，总周期约 22 到 28 周。每阶段都要可运行、可验收。

### 阶段 0：产品与工程基线，1 周

目标：

```text
冻结桌面版产品范围
确定技术路线
确定数据目录
确定打包方式
确定 UI 信息架构
```

交付：

```text
桌面版架构文档
页面信息架构
数据模型 v1
开发环境脚本
基础 CI 测试
```

验收：

```text
能一键启动开发环境
能运行当前 FastAPI MVP
核心页面线框完成
```

### 阶段 1：桌面壳与本地服务，2 周

功能：

```text
PySide6 桌面窗口
QtWebEngine 加载本地 UI
Embedded FastAPI 生命周期管理
随机端口与本地 token
系统托盘
应用退出和后台常驻
本地数据目录初始化
日志系统
```

页面：

```text
启动页
首页 Dashboard 空状态
设置页基础版
服务状态页
```

验收：

```text
双击启动 Hermes Desktop
无命令行也能打开窗口
服务异常时客户端能提示并重启
关闭窗口后可选择托盘常驻
```

### 阶段 2：基础 Hermes MVP，3 周

功能：

```text
主对话入口
Intent Router v1
Task Decomposer v1
Memory Candidate Pipeline v1
记忆中心
提醒创建
天气查询占位或真实 Provider v1
衣橱基础管理
Action Gate v1
用户确认卡
Execution Log
```

页面：

```text
Hermes 对话页
记忆中心
提醒页
衣橱基础页
Action 中心
日志详情
```

验收：

```text
用户能创建提醒并确认执行
用户能让 Hermes 记住偏好
用户能查看、修改、删除记忆
用户能添加衣橱条目
所有 App 状态改变都有 Action Log
```

### 阶段 3：Skills 扩展，3 周

功能：

```text
Skill Registry
Capability Contract
Skill Permission
document.summarize
image.clothing_recognition
work.todo_extract
content.list_generate
文件上传
图片上传
Skill Result
```

页面：

```text
Skills 中心
Skill 详情
文件与图片中心
Skill 运行结果页
Capability Contract 详情
```

验收：

```text
上传文档可生成摘要
上传图片可生成识别结果
会议内容可提取待办
每个 Skill 都有能力契约
Skill 不能越权调用 Tool
```

### 阶段 4：智能场景编排，3 周

功能：

```text
Context Signal Pipeline
Scene Registry
Opportunity Engine
Attention Policy
Reminder Decision
信息推荐
智能体推荐
Skill 推荐
Scene Feedback
```

页面：

```text
提醒与场景中心
Scene 创建向导
Scene 详情
推荐卡详情
触发历史
```

验收：

```text
用户可以创建“下雨前提醒带伞”场景
Hermes 可以根据天气和通勤偏好生成提醒建议
用户可以关闭、修改、暂停场景
Scene 误触发能反馈
```

### 阶段 5：灵感智能体，2 周

功能：

```text
灵感对话入口
发散模式
反方挑战
第一性原理
跨域类比
场景推演
收敛评估
Idea Card
Idea Library
Idea 转待办
Idea 转 PRD 草案
Idea 转 Scene 草案
```

页面：

```text
灵感工作室
Idea Card 详情
灵感库
PRD 草案页
```

验收：

```text
用户能完成一次灵感碰撞
能保存 Idea Card
能将 Idea 转成待办或 PRD
灵感偏好写入必须确认
```

### 阶段 6：安全、Eval、自主进化，4 周

功能：

```text
Autonomy Zone Classifier v1
Risk Classifier v2
Skill Patch
Personal Skill Draft
Skill Patch Eval
Rollback Manager
Skill Curator
Growth Log
Yellow Zone 确认
Red Zone 拦截
```

页面：

```text
Eval Center
Growth Log
Skill Curator
自主优化确认页
回滚详情页
安全策略设置
```

验收：

```text
Green Zone 优化可以自动进入 Draft
Draft 必须 Eval 通过才能启用
Yellow Zone 优化必须让用户感知
Red Zone 不允许自主执行
用户能查看 Hermes 最近优化了什么
用户能回滚优化
```

### 阶段 7：主动智能与外部集成，4 周

功能：

```text
主动建议
轻量实时触发
每周灵感复盘
个性化首页卡片
复杂 App 操作
日历集成
邮件集成
网盘集成
新闻 Provider
天气 Provider
地图 Provider
```

页面：

```text
Provider 设置
权限授权页
主动建议中心
每周复盘页
外部服务状态页
```

验收：

```text
用户可连接或断开外部服务
所有外部权限可查看和撤销
主动建议不造成高频打扰
敏感数据默认不进入长期记忆
```

### 阶段 8：打包、稳定性和正式发布，2 到 4 周

功能：

```text
PyInstaller 打包
自动更新策略
崩溃恢复
数据库迁移
备份与恢复
数据导出
性能优化
端到端测试
安全测试
```

验收：

```text
安装包可安装
桌面快捷方式可启动
离线可打开本地数据
升级不丢数据
异常退出后可恢复
核心流程端到端通过
```

## 8. 里程碑

```text
M0 第 1 周：桌面产品方案冻结
M1 第 3 周：桌面壳可运行
M2 第 6 周：基础 Hermes 可用
M3 第 9 周：Skills 可用
M4 第 12 周：Scene 可用
M5 第 14 周：Inspiration 可用
M6 第 18 周：自主进化闭环可用
M7 第 22 周：主动智能和外部集成可用
M8 第 24 到 28 周：正式桌面版发布
```

## 9. 优先级

P0 必须先做：

```text
桌面壳
本地服务生命周期
本地数据库
主对话
Action Gate
记忆中心
提醒
执行日志
设置中心
```

P1 第二优先级：

```text
Skills
文件与图片
衣橱
灵感工作室
Scene 中心
```

P2 第三优先级：

```text
Eval Center
Autonomy Zone
Skill Curator
Growth Log
主动推荐
外部服务集成
```

P3 后期增强：

```text
复杂实时触发
跨 App 操作
平台级 Skill 发布
复杂家庭权限协作
```

## 10. 测试计划

自动化测试：

```text
API 单元测试
服务层单元测试
数据迁移测试
Action 权限测试
Memory 分类测试
Skill Contract 测试
Scene 决策测试
Eval Runner 测试
桌面启动测试
打包后冒烟测试
```

人工验收场景：

```text
创建提醒
写入偏好记忆
删除记忆
上传文件总结
上传衣物图片
创建雨天通勤场景
保存灵感卡片
Idea 转 PRD
Skill Patch 回滚
Red Zone 操作拦截
备份和恢复
```

## 11. 安全与隐私策略

默认策略：

```text
本地优先
敏感记忆必须确认
Red Zone 不自主执行
API Key 加密保存
本地服务只监听 127.0.0.1
客户端请求必须携带本地 token
所有执行写审计日志
删除和批量操作必须二次确认
外部 Provider 默认关闭
```

敏感类别：

```text
健康
财务
身份
位置
家庭成员
私密文件
对外发送消息
删除与批量修改
```

## 12. 当前代码如何演进

当前仓库已有 FastAPI MVP，可作为服务端原型继续演进。

下一步改造顺序：

```text
1. 新增 desktop/ PySide6 桌面壳
2. 将当前 Web UI 作为 QtWebEngine 页面加载
3. 将 uvicorn 启动逻辑封装成 DesktopServiceManager
4. 增加本地 token 认证
5. 将 data/hermes.db 迁移到 AppData/Hermes/data/hermes.db
6. 扩展数据库 schema
7. 按阶段补页面和服务
```

建议目录：

```text
desktop/
  main.py
  shell.py
  service_manager.py
  tray.py
  notifications.py

hermes_app/
  api/
  core/
  services/
  domain/
  repositories/
  workers/
  web/

tests/
  api/
  services/
  desktop/
  e2e/
```

## 13. 完成定义

真正可用的 Hermes Desktop 必须达到：

```text
用户能双击启动
用户不需要理解服务端
所有数据默认保存在本机
用户能看到 Hermes 记住了什么
用户能控制 Hermes 执行了什么
用户能撤销 Hermes 优化了什么
用户能关闭自主进化
高风险操作不会自动执行
低风险能力可以越用越顺手
核心流程崩溃后可恢复
升级后数据不丢失
```

