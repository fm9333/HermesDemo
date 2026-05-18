from __future__ import annotations

from hermes_app.schemas import RiskLevel


class SafetyService:
    sensitive_keywords = ("健康", "病历", "财务", "银行卡", "身份证", "位置", "定位", "私密", "隐私")
    high_risk_keywords = (
        "删除",
        "清空",
        "批量",
        "共享",
        "分享",
        "发送给",
        "导出",
        "授权",
        "支付",
        "转账",
        "delete",
        "export",
        "share",
        "pay",
        "transfer",
    )

    def classify(self, message: str, intent: str) -> RiskLevel:
        normalized = message.lower()
        if any(keyword in normalized for keyword in self.high_risk_keywords):
            return "blocked"
        if any(keyword in normalized for keyword in self.sensitive_keywords):
            return "sensitive"
        if intent in {"create_reminder", "memory_update", "wardrobe_add", "create_scene"}:
            return "medium"
        return "low"

    def red_zone_check(self, message: str, intent: str) -> dict:
        risk_level = self.classify(message, intent)
        blocked = risk_level == "blocked"
        return {
            "risk_level": risk_level,
            "blocked": blocked,
            "reason": "命中 Red Zone，不允许自主执行。" if blocked else "未命中 Red Zone 阻断规则。",
        }

    def autonomy_zone_for_skill(self, skill_id: str) -> str:
        if skill_id.startswith(("document.", "work.", "content.", "sheet.", "inspiration.")):
            return "green"
        if skill_id.startswith(("image.wardrobe", "scene.", "preference.")):
            return "yellow"
        return "red"
