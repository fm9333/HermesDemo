# Hermes 架构设计

## 设计原则

Hermes 的服务端不让 LLM 直接写数据库或直接调用外部 API。LLM 或规则编排器只生成计划，后端通过 Tool Registry、Policy、Schema Validator 和 Action Gate 执行确定性动作。

当前 MVP 采用：

```text
Client
  -> FastAPI API
  -> HermesOrchestrator
  -> IntentRouter / SafetyService
  -> LLMClient / PromptLibrary / MemoryService / SkillRegistry / InspirationService
  -> ActionService
  -> SQLite
```

## 服务端分层

```text
API Layer
  负责 HTTP 输入输出，不承载业务判断。

Orchestration Layer
  负责意图路由、风险判断、调用 Memory/Skill/Action。

Domain Services
  MemoryService: 记忆候选、保存、删除、查询。
  ActionService: 创建待确认动作、确认执行、拒绝动作。
  SkillRegistry: 管理 Skill Capability Contract。
  LLMProviderService: 管理 OpenAI-compatible Provider、模型参数和本地 API Key 保护保存。
  LLMClient: 调用 `/v1/chat/completions` 兼容接口，只生成回复或草案。
  PromptLibrary: 管理 Hermes 主智能体、任务规划、Skill、Eval 和 Safety 提示词。
  PersonalSkillService: 管理 Personal Skill 草案、补丁、评测门禁、激活、版本、回滚和归档。
  SkillCuratorService: 检查重复技能、未评测草案、失败补丁、高频变更和来源弱追踪。
  InspirationService: 生成 Idea Card。
  SafetyService: 风险分级与 Autonomy Zone 判断。

Storage Layer
  SQLite 本地存储，后续可替换为 PostgreSQL。
```

## 客户端设计

客户端是一个控制台式 Web App，不做营销页：

```text
左侧：模块导航
中间：Hermes 主对话
右侧：状态检查器
```

右侧状态检查器用于查看：

```text
Memory
Reminders
Ideas
Wardrobe
Skills
Execution Logs
```

## 当前数据表

```text
memory_items
pending_actions
execution_logs
reminders
idea_cards
wardrobe_items
```

## MVP 行为闭环

创建提醒：

```text
用户输入
-> IntentRouter 识别 create_reminder
-> SafetyService 标记 medium risk
-> ActionService 创建 pending action
-> 用户确认
-> 写入 reminders
-> 记录 execution_logs
```

写入记忆：

```text
用户输入
-> MemoryService 提取 Memory Candidate
-> ActionService 创建 memory.write 待确认动作
-> 用户确认
-> 写入 memory_items
```

Skill 调用：

```text
用户输入
-> IntentRouter 选择 Skill intent
-> SkillRuntime 优先尝试 LLM Prompt
-> LLM 未配置或失败时回退 SkillRegistry 本地规则
-> Orchestrator 返回 skill_result card
```

普通对话：

```text
用户输入
-> IntentRouter 标记 general_chat
-> LLMClient 使用默认 LLM Provider 和 hermes.agent.core prompt
-> 记录 llm_calls 审计
-> LLM 不直接写数据库或调用外部 API
```

## 后续演进方向

1. 抽象 `LLMPlanner`，输入上下文、记忆和能力契约，输出结构化计划。
2. 增加 Responses API、工具调用和结构化输出适配。
3. 为每个 Skill 增加 `evals/` 样例与自动评测。
4. 将 Autonomy Zone 分类绑定 Skill Patch 生成、激活和回滚流程。
5. 增加用户系统、权限边界、审计查询和 OS Keychain/SQLCipher 密钥保护。
