from __future__ import annotations


class InspirationService:
    def generate_card(self, message: str) -> dict:
        seed = message.strip()
        return {
            "title": "Idea Card",
            "body": "\n".join(
                [
                    f"方向：{seed}",
                    "反方挑战：这个想法是否解决了高频痛点，而不是只展示智能感？",
                    "跨域类比：把它当作个人操作系统的控制台，而不是聊天窗口。",
                    "MVP 收敛：优先验证记忆、提醒、受控执行三件事。",
                ]
            ),
            "tags": ["inspiration", "mvp", "challenge"],
        }

