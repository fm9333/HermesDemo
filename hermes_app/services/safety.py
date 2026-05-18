from __future__ import annotations

from hermes_app.schemas import RiskLevel


class SafetyService:
    sensitive_keywords = ("健康", "病历", "财务", "银行卡", "身份证", "位置", "定位", "私密", "隐私")
    high_risk_keywords = ("删除", "清空", "批量", "共享", "发送给", "授权", "支付", "转账")

    def classify(self, message: str, intent: str) -> RiskLevel:
        if any(keyword in message for keyword in self.high_risk_keywords):
            return "high"
        if any(keyword in message for keyword in self.sensitive_keywords):
            return "sensitive"
        if intent in {"create_reminder", "memory_update", "wardrobe_add"}:
            return "medium"
        return "low"

    def autonomy_zone_for_skill(self, skill_id: str) -> str:
        if skill_id.startswith(("document.", "work.", "content.", "sheet.", "inspiration.")):
            return "green"
        if skill_id.startswith(("image.wardrobe", "scene.", "preference.")):
            return "yellow"
        return "red"

