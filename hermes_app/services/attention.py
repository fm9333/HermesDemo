from __future__ import annotations


class AttentionPolicy:
    def decide(self, opportunity: dict) -> dict:
        priority = float(opportunity.get("priority", 0))
        if priority >= 0.8:
            channel = "interrupt"
            reason = "高优先级机会，允许轻提醒。"
        elif priority >= 0.5:
            channel = "summary"
            reason = "中优先级机会，放入摘要或首页卡片。"
        else:
            channel = "silent"
            reason = "低优先级机会，静默沉淀。"

        return {
            "channel": channel,
            "requires_confirmation": channel == "interrupt",
            "reason": reason,
        }

