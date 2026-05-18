from __future__ import annotations

import csv
import io
import re

from hermes_app.schemas import SkillContract


class SkillRegistry:
    def __init__(self):
        self._contracts = [
            self._contract(
                "document.summarize",
                "文档总结",
                ["text", "pdf", "docx"],
                ["summary"],
                cannot_call_tools=["file.share", "memory.write_sensitive"],
            ),
            self._contract(
                "document.contract_extract",
                "合同要点提取",
                ["text", "pdf", "docx"],
                ["contract_brief"],
                cannot_call_tools=["file.share", "external.send", "payment.send"],
            ),
            self._contract(
                "document.bill_analyze",
                "账单票据分析",
                ["text", "pdf", "image"],
                ["bill_analysis"],
                cannot_call_tools=["payment.send", "external.send", "file.share"],
            ),
            self._contract(
                "image.clothing_recognition",
                "衣物识别",
                ["image"],
                ["wardrobe_candidate"],
                autonomy_zone="yellow",
                can_call_tools=["wardrobe.add"],
                cannot_call_tools=["wardrobe.delete", "file.share"],
            ),
            self._contract(
                "image.photo_classify",
                "照片分类",
                ["image", "metadata", "text"],
                ["photo_category"],
                cannot_call_tools=["file.share", "face.identify"],
            ),
            self._contract(
                "work.todo_extract",
                "待办提取",
                ["text", "docx", "pdf"],
                ["todo_candidates"],
                can_call_tools=["todo.create_candidate"],
                cannot_call_tools=["reminder.create_without_confirmation"],
            ),
            self._contract(
                "work.meeting_minutes",
                "会议纪要生成",
                ["text", "docx", "pdf"],
                ["meeting_minutes"],
                can_call_tools=["todo.create_candidate"],
                cannot_call_tools=["external.send", "calendar.write_without_confirmation"],
            ),
            self._contract(
                "work.weekly_report",
                "周报生成",
                ["text"],
                ["weekly_report"],
                cannot_call_tools=["external.send", "file.share"],
            ),
            self._contract(
                "content.list_generate",
                "清单生成",
                ["text"],
                ["list"],
                cannot_call_tools=["file.share", "payment.send"],
            ),
            self._contract(
                "content.prd_generate",
                "PRD 草案生成",
                ["text"],
                ["prd"],
                cannot_call_tools=["external.send", "file.share"],
            ),
            self._contract(
                "content.copy_generate",
                "文案生成",
                ["text"],
                ["copy"],
                cannot_call_tools=["external.send", "ad.publish_without_confirmation"],
            ),
            self._contract(
                "content.travel_plan",
                "旅行计划生成",
                ["text"],
                ["travel_plan"],
                cannot_call_tools=["payment.send", "booking.create_without_confirmation"],
            ),
            self._contract(
                "data.table_analyze",
                "表格数据分析",
                ["text", "csv", "xlsx"],
                ["table_analysis"],
                cannot_call_tools=["file.share", "external.send"],
            ),
            self._contract(
                "file.archive_plan",
                "文件归档方案",
                ["text", "path", "metadata"],
                ["archive_plan"],
                cannot_call_tools=["file.delete", "file.share"],
            ),
            self._contract(
                "calendar.schedule_plan",
                "日程安排草案",
                ["text"],
                ["schedule_plan"],
                can_call_tools=["calendar.create_candidate"],
                cannot_call_tools=["calendar.write_without_confirmation", "external.send"],
            ),
            self._contract(
                "email.reply_draft",
                "邮件回复草案",
                ["text", "email"],
                ["email_draft"],
                cannot_call_tools=["email.send_without_confirmation", "external.send"],
            ),
        ]

    def list(self) -> list[SkillContract]:
        return self._contracts

    def run(self, skill_id: str, text: str) -> dict:
        handlers = {
            "document.summarize": self._summarize_document,
            "document.contract_extract": self._extract_contract,
            "document.bill_analyze": self._analyze_bill,
            "image.photo_classify": self._classify_photo,
            "work.todo_extract": self._extract_todos,
            "work.meeting_minutes": self._generate_meeting_minutes,
            "work.weekly_report": self._generate_weekly_report,
            "content.list_generate": self._generate_list,
            "content.prd_generate": self._generate_prd,
            "content.copy_generate": self._generate_copy,
            "content.travel_plan": self._generate_travel_plan,
            "data.table_analyze": self._analyze_table,
            "file.archive_plan": self._plan_archive,
            "calendar.schedule_plan": self._plan_schedule,
            "email.reply_draft": self._draft_email_reply,
        }
        handler = handlers.get(skill_id)
        if not handler:
            return {"title": "Skill 未注册", "message": f"{skill_id} is not available."}
        return handler(text)

    def _contract(
        self,
        skill_id: str,
        title: str,
        allowed_inputs: list[str],
        allowed_outputs: list[str],
        autonomy_zone: str = "green",
        can_call_tools: list[str] | None = None,
        cannot_call_tools: list[str] | None = None,
    ) -> SkillContract:
        return SkillContract(
            skill_id=skill_id,
            title=title,
            autonomy_zone=autonomy_zone,
            allowed_inputs=allowed_inputs,
            allowed_outputs=allowed_outputs,
            can_write_memory=False,
            can_call_tools=can_call_tools or [],
            cannot_call_tools=cannot_call_tools or [],
            requires_eval_before_activation=True,
            rollback_supported=True,
        )

    def _summarize_document(self, text: str) -> dict:
        sentences = self._sentences(text, limit=8)
        return {
            "title": "文档总结草案",
            "summary": "；".join(sentences[:3]) or text[:180],
            "key_points": sentences[:5],
            "structure": ["结论", "关键信息", "待确认问题"],
            "open_questions": self._keyword_sentences(text, ("待确认", "问题", "是否", "能否"), limit=3),
        }

    def _extract_todos(self, text: str) -> dict:
        chunks = self._sentences(text, limit=30)
        keywords = ("待办", "todo", "需要", "请", "安排", "跟进", "确认", "完成", "处理", "修复")
        todos = []
        for chunk in chunks:
            lower = chunk.lower()
            if any(keyword in lower for keyword in keywords):
                title = re.sub(r"^(待办|todo)[:：\-\s]*", "", chunk, flags=re.IGNORECASE).strip()
                todos.append(
                    {
                        "title": title[:120],
                        "owner": self._extract_owner(title),
                        "due_at_text": self._extract_due_text(title),
                        "source": "message",
                        "confidence": 0.78,
                    }
                )

        if not todos:
            todos.append(
                {
                    "title": "确认是否存在待办事项",
                    "owner": "unknown",
                    "due_at_text": "unknown",
                    "source": "fallback",
                    "confidence": 0.42,
                }
            )

        return {
            "title": "待办候选",
            "todos": todos,
            "count": len(todos),
        }

    def _generate_list(self, text: str) -> dict:
        normalized = text.lower()
        if any(word in normalized for word in ("上线", "发布", "release", "deploy")):
            items = ["确认发布范围", "完成回归测试", "准备回滚方案", "通知相关人员", "发布后监控指标"]
            list_type = "release"
        elif any(word in normalized for word in ("旅行", "出行", "行程", "旅游")):
            items = ["证件与票据", "天气与衣物", "住宿与交通", "预算与支付", "紧急联系人"]
            list_type = "travel"
        elif any(word in normalized for word in ("采购", "购物", "买")):
            items = ["必买项", "可选项", "预算上限", "购买渠道", "到货检查"]
            list_type = "shopping"
        else:
            items = ["目标", "约束", "步骤", "风险", "下一步"]
            list_type = "general"

        return {
            "title": "清单草案",
            "list_type": list_type,
            "items": [{"title": item, "checked": False} for item in items],
        }

    def _generate_meeting_minutes(self, text: str) -> dict:
        sentences = self._sentences(text, limit=20)
        decisions = self._keyword_sentences(text, ("决定", "确认", "同意", "通过", "结论"), limit=6)
        risks = self._keyword_sentences(text, ("风险", "阻塞", "延期", "依赖", "问题"), limit=5)
        open_questions = self._keyword_sentences(text, ("待确认", "是否", "能否", "问题", "?"), limit=5)
        action_items = self._extract_todos(text)["todos"]
        return {
            "title": "会议纪要草案",
            "summary": "；".join(sentences[:3]) or "会议内容不足，需要补充原始记录。",
            "decisions": decisions or ["暂无明确决策"],
            "action_items": action_items,
            "risks": risks,
            "open_questions": open_questions,
            "sections": ["会议结论", "行动项", "风险", "待确认问题"],
        }

    def _generate_weekly_report(self, text: str) -> dict:
        completed = self._keyword_sentences(text, ("完成", "已", "上线", "发布", "修复", "交付"), limit=8)
        next_items = self._keyword_sentences(text, ("下周", "下一步", "计划", "继续", "需要", "准备"), limit=8)
        risks = self._keyword_sentences(text, ("风险", "阻塞", "延期", "依赖", "问题"), limit=5)
        return {
            "title": "周报草案",
            "completed": completed or ["本周完成事项需要补充"],
            "next_week": next_items or ["下周计划需要补充"],
            "risks": risks,
            "support_needed": ["请确认是否需要补充资源、排期或跨团队协作"],
        }

    def _generate_prd(self, text: str) -> dict:
        feature = self._compact_title(text, fallback="新功能")
        return {
            "title": "PRD 草案",
            "feature": feature,
            "background": text[:220],
            "target_users": ["核心用户", "运营/管理用户"],
            "problem_statement": "当前需求仍需通过用户场景和业务目标进一步收敛。",
            "goals": ["形成可测试闭环", "明确页面、数据、权限和验收标准", "降低上线后的返工风险"],
            "non_goals": ["不在未确认外部权限前自动发送或写入第三方系统"],
            "mvp_scope": ["入口与导航", "核心创建/编辑流程", "结果预览", "权限确认", "运行日志"],
            "pages": ["列表页", "详情页", "编辑页", "配置页", "评审页"],
            "data_model": ["id", "title", "status", "source", "payload_json", "created_at", "updated_at"],
            "acceptance_criteria": [
                "用户可以完成核心流程并看到结果",
                "失败状态有明确提示和可重试路径",
                "关键操作写入审计日志",
            ],
            "open_questions": ["目标用户优先级是什么？", "哪些字段必须配置？", "是否需要外部系统集成？"],
        }

    def _generate_copy(self, text: str) -> dict:
        subject = self._compact_title(text, fallback="产品能力")
        return {
            "title": "文案草案",
            "headline": f"{subject}，让复杂工作更快落地",
            "subheadline": "把需求、计划、执行和验证组织成可追踪的工作流。",
            "bullets": ["减少重复整理", "输出结构化结果", "保留风险和待确认项"],
            "cta": "开始配置",
            "variants": [
                {"tone": "专业", "headline": f"{subject}的可执行工作台"},
                {"tone": "直接", "headline": f"用 {subject} 完成下一步"},
            ],
        }

    def _generate_travel_plan(self, text: str) -> dict:
        destination = self._extract_destination(text)
        return {
            "title": "旅行计划草案",
            "destination": destination,
            "itinerary": [
                {"day": 1, "focus": "抵达、入住、熟悉交通和周边"},
                {"day": 2, "focus": "核心景点或核心事务安排"},
                {"day": 3, "focus": "备用行程、购物/会友、返程准备"},
            ],
            "checklist": ["证件", "交通票据", "住宿确认", "天气与衣物", "支付方式", "紧急联系人"],
            "budget_notes": ["拆分交通、住宿、餐饮、门票和备用金", "高额预订需要用户确认后执行"],
            "risks": ["天气变化", "交通延误", "证件或预订信息遗漏"],
        }

    def _extract_contract(self, text: str) -> dict:
        amounts = self._find_amounts(text)
        dates = self._find_dates(text)
        obligations = self._keyword_sentences(text, ("应", "需", "负责", "交付", "付款", "验收"), limit=8)
        risks = self._keyword_sentences(text, ("违约", "赔偿", "解除", "保密", "逾期", "争议"), limit=8)
        parties = {
            "party_a": self._extract_after_label(text, "甲方"),
            "party_b": self._extract_after_label(text, "乙方"),
        }
        open_questions = []
        if not parties["party_a"] or not parties["party_b"]:
            open_questions.append("甲乙方信息不完整")
        if not dates:
            open_questions.append("缺少明确日期或履约期限")
        if not amounts:
            open_questions.append("缺少明确金额或付款条款")
        return {
            "title": "合同要点草案",
            "parties": parties,
            "key_terms": {"amounts": amounts, "dates": dates},
            "obligations": obligations,
            "risks": risks,
            "open_questions": open_questions,
            "disclaimer": "该输出为信息提取结果，不构成法律意见。",
        }

    def _analyze_bill(self, text: str) -> dict:
        amounts = self._find_amounts(text)
        dates = self._find_dates(text)
        anomalies = self._keyword_sentences(text, ("逾期", "滞纳金", "异常", "重复", "欠费", "未支付"), limit=6)
        return {
            "title": "账单分析草案",
            "summary": f"识别到 {len(amounts)} 个金额和 {len(dates)} 个日期。",
            "detected_amounts": amounts,
            "due_dates": dates,
            "anomalies": anomalies,
            "next_actions": ["核对账单主体和周期", "确认金额是否已支付", "如涉及自动扣款，先由用户确认"],
        }

    def _analyze_table(self, text: str) -> dict:
        rows = self._parse_table(text)
        header = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        missing_cells = sum(1 for row in data_rows for cell in row if not cell.strip())
        numeric_columns = self._numeric_column_summaries(header, data_rows)
        return {
            "title": "表格分析草案",
            "row_count": len(data_rows),
            "columns": header,
            "numeric_columns": numeric_columns,
            "insights": [
                f"共有 {len(data_rows)} 行数据、{len(header)} 个字段。",
                "已生成基础质量检查，复杂统计需要更完整数据。",
            ],
            "quality_issues": [f"发现 {missing_cells} 个空单元格"] if missing_cells else [],
        }

    def _plan_archive(self, text: str) -> dict:
        normalized = text.lower()
        if any(word in normalized for word in ("合同", "contract")):
            category = "contract"
            folder = "Documents/Contracts"
        elif any(word in normalized for word in ("发票", "账单", "invoice", "bill")):
            category = "finance"
            folder = "Documents/Finance"
        elif any(word in normalized for word in ("照片", "图片", "image", "photo")):
            category = "media"
            folder = "Pictures/Sorted"
        else:
            category = "general"
            folder = "Documents/Inbox"
        return {
            "title": "文件归档方案",
            "category": category,
            "suggested_folder": folder,
            "tags": self._derive_tags(text),
            "retention": "保留原文件，不自动删除；移动或删除必须再次确认。",
            "risk": "可能误分类，建议用户确认后执行批量移动。",
        }

    def _classify_photo(self, text: str) -> dict:
        normalized = text.lower()
        if any(word in normalized for word in ("发票", "票据", "receipt", "invoice")):
            category = "receipt"
        elif any(word in normalized for word in ("旅行", "景点", "travel", "trip")):
            category = "travel"
        elif any(word in normalized for word in ("会议", "白板", "work", "meeting")):
            category = "work"
        else:
            category = "general_photo"
        return {
            "title": "照片分类草案",
            "category": category,
            "tags": self._derive_tags(text),
            "confidence": 0.62,
            "safety_notes": ["不做人脸身份识别", "不自动共享照片"],
        }

    def _plan_schedule(self, text: str) -> dict:
        dates = self._find_dates(text)
        return {
            "title": "日程安排草案",
            "subject": self._compact_title(text, fallback="待安排事项"),
            "time_candidates": dates or [self._extract_due_text(text)],
            "attendees": self._extract_people(text),
            "agenda": self._sentences(text, limit=5) or [text[:120]],
            "confirmation_required": True,
        }

    def _draft_email_reply(self, text: str) -> dict:
        return {
            "title": "邮件回复草案",
            "subject": self._compact_title(text, fallback="邮件回复"),
            "body": [
                "您好，",
                "我已收到并理解当前事项。以下是我的确认和下一步安排：",
                "1. 我会先核对关键事实和时间节点。",
                "2. 如需我执行外发或确认操作，请您再次确认。",
                "谢谢。",
            ],
            "tone": "professional",
            "requires_confirmation_before_send": True,
        }

    def _sentences(self, text: str, limit: int = 10) -> list[str]:
        chunks = [
            chunk.strip(" \t\r\n，。；;：:")
            for chunk in re.split(r"[\n。；;!?！？]+", text)
            if chunk.strip(" \t\r\n，。；;：:")
        ]
        return chunks[:limit]

    def _keyword_sentences(self, text: str, keywords: tuple[str, ...], limit: int = 5) -> list[str]:
        lowered_keywords = tuple(keyword.lower() for keyword in keywords)
        matches = []
        for chunk in self._sentences(text, limit=40):
            lower = chunk.lower()
            if any(keyword in lower for keyword in lowered_keywords):
                matches.append(chunk[:160])
            if len(matches) >= limit:
                break
        return matches

    def _find_amounts(self, text: str) -> list[str]:
        pattern = r"(?:¥|￥|\$)?\s?\d+(?:,\d{3})*(?:\.\d{1,2})?\s?(?:元|人民币|美元|usd|rmb)?"
        return [match.group(0).strip() for match in re.finditer(pattern, text, re.IGNORECASE)][:12]

    def _find_dates(self, text: str) -> list[str]:
        patterns = [
            r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?",
            r"\d{1,2}月\d{1,2}日",
            r"(?:今天|明天|后天|下周|本周|月底|年底)",
        ]
        dates = []
        for pattern in patterns:
            dates.extend(match.group(0) for match in re.finditer(pattern, text))
        return dates[:12]

    def _extract_after_label(self, text: str, label: str) -> str:
        match = re.search(label + r"[:：\s]*([^，。；;\n]{2,60})", text)
        return match.group(1).strip() if match else "unknown"

    def _extract_owner(self, text: str) -> str:
        match = re.search(r"请([\u4e00-\u9fa5A-Za-z0-9_]{1,12})", text)
        return match.group(1) if match else "unknown"

    def _extract_due_text(self, text: str) -> str:
        dates = self._find_dates(text)
        if dates:
            return dates[0]
        match = re.search(r"\d{1,2}[点:：]\d{0,2}", text)
        return match.group(0) if match else "unknown"

    def _extract_destination(self, text: str) -> str:
        match = re.search(r"去([^，。；;\n]{2,20})(?:旅行|旅游|出行|玩|$)", text)
        if match:
            return match.group(1).strip()
        return "待确认目的地"

    def _extract_people(self, text: str) -> list[str]:
        names = re.findall(r"(?:和|与|请|邀请)([\u4e00-\u9fa5A-Za-z0-9_]{1,12})", text)
        return names[:8]

    def _compact_title(self, text: str, fallback: str) -> str:
        title = re.sub(r"^(帮我|请|生成|写|整理|分析|一个|一份)\s*", "", text.strip(), flags=re.IGNORECASE)
        title = title.strip(" ，。；;：:")
        return title[:32] or fallback

    def _derive_tags(self, text: str) -> list[str]:
        tags = []
        for keyword in ("合同", "账单", "发票", "会议", "周报", "旅行", "照片", "PRD", "邮件", "日程"):
            if keyword.lower() in text.lower():
                tags.append(keyword.lower())
        return tags or ["inbox"]

    def _parse_table(self, text: str) -> list[list[str]]:
        sample = text.strip()
        if not sample:
            return []
        delimiter = "\t" if "\t" in sample and sample.count("\t") >= sample.count(",") else ","
        reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
        return [[cell.strip() for cell in row] for row in reader if row]

    def _numeric_column_summaries(self, header: list[str], rows: list[list[str]]) -> list[dict]:
        summaries = []
        for index, name in enumerate(header):
            values = []
            for row in rows:
                if index >= len(row):
                    continue
                value = row[index].replace(",", "")
                try:
                    values.append(float(value))
                except ValueError:
                    continue
            if values:
                summaries.append(
                    {
                        "column": name or f"column_{index + 1}",
                        "count": len(values),
                        "sum": round(sum(values), 2),
                        "avg": round(sum(values) / len(values), 2),
                    }
                )
        return summaries
