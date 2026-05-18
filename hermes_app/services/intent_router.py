from __future__ import annotations


class IntentRouter:
    def route(self, message: str) -> str:
        normalized = message.strip().lower()

        if any(word in normalized for word in ("提醒", "闹钟", "叫我")):
            return "create_reminder"
        if any(word in normalized for word in ("记住", "以后", "默认", "偏好")):
            return "memory_update"
        if any(word in normalized for word in ("天气", "下雨", "降雨", "气温")):
            return "weather_query"
        if any(word in normalized for word in ("衣橱", "衣服", "穿搭", "外套", "衬衫")):
            return "wardrobe_add"
        if any(word in normalized for word in ("灵感", "创意", "idea", "挑战", "发散")):
            return "inspiration"
        if any(word in normalized for word in ("总结", "文档", "pdf", "合同")):
            return "document_summarize"
        if any(word in normalized for word in ("待办", "todo", "任务")):
            return "todo_extract"
        if any(word in normalized for word in ("清单", "列表", "计划")):
            return "list_generate"
        return "general_chat"

