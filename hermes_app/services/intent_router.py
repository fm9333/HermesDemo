from __future__ import annotations


class IntentRouter:
    def route(self, message: str) -> str:
        normalized = message.strip().lower()

        if "场景" in normalized or "scene" in normalized:
            return "create_scene"
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
        if any(word in normalized for word in ("会议纪要", "会议记录", "meeting minutes", "会议总结")):
            return "meeting_minutes"
        if any(word in normalized for word in ("周报", "weekly report", "本周总结")):
            return "weekly_report"
        if any(word in normalized for word in ("prd", "产品需求", "需求文档", "需求说明")):
            return "prd_generate"
        if any(word in normalized for word in ("文案", "广告语", "slogan", "营销", "宣传语")):
            return "copy_generate"
        if any(word in normalized for word in ("旅行计划", "旅游计划", "行程规划", "出行计划")):
            return "travel_plan"
        if any(word in normalized for word in ("合同", "协议", "contract")):
            return "contract_extract"
        if any(word in normalized for word in ("账单", "发票", "票据", "bill", "invoice")):
            return "bill_analyze"
        if any(word in normalized for word in ("表格", "csv", "excel", "xlsx", "数据分析")):
            return "table_analyze"
        if any(word in normalized for word in ("照片分类", "图片分类", "photo classify", "相册整理")):
            return "photo_classify"
        if any(word in normalized for word in ("归档", "整理文件", "文件分类", "archive")):
            return "file_archive"
        if any(word in normalized for word in ("日程", "安排会议", "约会", "calendar")):
            return "schedule_plan"
        if any(word in normalized for word in ("邮件回复", "回邮件", "回复邮件", "email reply")):
            return "email_reply"
        if any(word in normalized for word in ("总结", "文档", "pdf")):
            return "document_summarize"
        if any(word in normalized for word in ("待办", "todo", "任务")):
            return "todo_extract"
        if any(word in normalized for word in ("清单", "列表", "计划")):
            return "list_generate"
        return "general_chat"
