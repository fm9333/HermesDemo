from __future__ import annotations

import re

from hermes_app.schemas import SkillContract


class SkillRegistry:
    def __init__(self):
        self._contracts = [
            SkillContract(
                skill_id="document.summarize",
                title="文档总结",
                autonomy_zone="green",
                allowed_inputs=["text", "pdf", "docx"],
                allowed_outputs=["summary"],
                can_write_memory=False,
                can_call_tools=[],
                cannot_call_tools=["file.share", "memory.write_sensitive"],
                requires_eval_before_activation=True,
                rollback_supported=True,
            ),
            SkillContract(
                skill_id="image.clothing_recognition",
                title="衣物识别",
                autonomy_zone="yellow",
                allowed_inputs=["image"],
                allowed_outputs=["wardrobe_candidate"],
                can_write_memory=False,
                can_call_tools=["wardrobe.add"],
                cannot_call_tools=["wardrobe.delete", "file.share"],
                requires_eval_before_activation=True,
                rollback_supported=True,
            ),
            SkillContract(
                skill_id="work.todo_extract",
                title="待办提取",
                autonomy_zone="green",
                allowed_inputs=["text", "docx", "pdf"],
                allowed_outputs=["todo_candidates"],
                can_write_memory=False,
                can_call_tools=["todo.create_candidate"],
                cannot_call_tools=["reminder.create_without_confirmation"],
                requires_eval_before_activation=True,
                rollback_supported=True,
            ),
            SkillContract(
                skill_id="content.list_generate",
                title="清单生成",
                autonomy_zone="green",
                allowed_inputs=["text"],
                allowed_outputs=["list"],
                can_write_memory=False,
                can_call_tools=[],
                cannot_call_tools=["file.share", "payment.send"],
                requires_eval_before_activation=True,
                rollback_supported=True,
            ),
        ]

    def list(self) -> list[SkillContract]:
        return self._contracts

    def run(self, skill_id: str, text: str) -> dict:
        if skill_id == "document.summarize":
            return {
                "title": "文档总结草案",
                "summary": text[:180],
                "structure": ["结论", "关键信息", "待确认问题"],
            }
        if skill_id == "work.todo_extract":
            return self._extract_todos(text)
        if skill_id == "content.list_generate":
            return {
                "title": "清单草案",
                "items": ["目标", "约束", "步骤", "风险", "下一步"],
            }
        return {"title": "Skill 未注册", "message": f"{skill_id} is not available."}

    def _extract_todos(self, text: str) -> dict:
        chunks = [
            chunk.strip(" \t\r\n，。；;：:")
            for chunk in re.split(r"[\n。；;]", text)
            if chunk.strip(" \t\r\n，。；;：:")
        ]
        keywords = ("待办", "todo", "需要", "请", "安排", "跟进", "确认", "完成", "处理", "修复")
        todos = []
        for chunk in chunks:
            lower = chunk.lower()
            if any(keyword in lower for keyword in keywords):
                title = re.sub(r"^(待办|todo)[:：\-\s]*", "", chunk, flags=re.IGNORECASE).strip()
                todos.append({"title": title[:120], "source": "message", "confidence": 0.78})

        if not todos:
            todos.append({"title": "确认是否存在待办事项", "source": "fallback", "confidence": 0.42})

        return {
            "title": "待办候选",
            "todos": todos,
            "count": len(todos),
        }
