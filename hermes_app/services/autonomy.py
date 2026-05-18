from __future__ import annotations


class AutonomyZoneClassifier:
    red_keywords = ("删除", "清空", "支付", "转账", "授权", "分享", "导出", "隐私", "身份证", "银行")
    yellow_types = {"memory_write", "scene_change", "preference_update", "notification", "tool_plan"}
    green_types = {"template_tuning", "skill_draft", "workflow_hint", "idea_scoring", "formatting"}

    def classify(self, proposal: dict) -> dict:
        proposal_type = str(proposal.get("proposal_type", "general"))
        risk_level = str(proposal.get("risk_level", "low"))
        summary = str(proposal.get("summary", ""))

        if risk_level in {"high", "sensitive", "blocked"} or self._contains_red_keyword(summary):
            zone = "red"
            reason = "高风险或敏感变更不能自主执行。"
            allowed_actions = ["suggest_only"]
        elif risk_level == "medium" or proposal_type in self.yellow_types:
            zone = "yellow"
            reason = "会影响用户数据或打扰策略，需要用户确认。"
            allowed_actions = ["create_candidate", "request_confirmation"]
        elif proposal_type in self.green_types:
            zone = "green"
            reason = "低风险优化，可自动进入 Draft 或候选区。"
            allowed_actions = ["create_draft", "record_growth_log"]
        else:
            zone = "yellow"
            reason = "未知类型按 Yellow Zone 处理。"
            allowed_actions = ["request_confirmation"]

        return {
            "zone": zone,
            "requires_confirmation": zone != "green",
            "requires_eval": proposal_type in {"skill_draft", "tool_plan"} or zone == "red",
            "allowed_actions": allowed_actions,
            "reason": reason,
        }

    def list_zones(self) -> list[dict]:
        return [
            {
                "zone": "green",
                "description": "低风险优化，可自动进入 Draft 或候选区。",
                "examples": sorted(self.green_types),
            },
            {
                "zone": "yellow",
                "description": "影响用户数据、偏好或提醒策略，必须让用户感知并确认。",
                "examples": sorted(self.yellow_types),
            },
            {
                "zone": "red",
                "description": "高风险、敏感、外发或不可逆动作，不允许自主执行。",
                "examples": list(self.red_keywords),
            },
        ]

    def _contains_red_keyword(self, summary: str) -> bool:
        return any(keyword in summary for keyword in self.red_keywords)
