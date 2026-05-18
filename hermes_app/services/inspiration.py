from __future__ import annotations


class InspirationService:
    def generate_card(self, message: str) -> dict:
        seed = self._clean_seed(message)
        mode = self._detect_mode(message)
        card = {
            "title": self._title(seed, mode),
            "direction": seed,
            "target_user": "需要把想法快速收敛成行动的人",
            "pain_point": f"{seed} 目前还停留在想法层，缺少可验证的最小闭环。",
            "core_assumption": f"只要把 {seed} 压缩成一个可测试场景，就能更快判断价值。",
            "counter_challenge": self._counter_challenge(seed),
            "analogy": self._analogy(seed, mode),
            "mvp_plan": self._mvp_plan(seed),
            "risks": self._risks(mode),
            "next_steps": self._next_steps(seed),
            "score": self._score(mode),
            "tags": ["inspiration", mode, "idea-card"],
            "mode": mode,
            "status": "draft",
        }
        card["body"] = self._compose_body(card)
        return card

    def _clean_seed(self, message: str) -> str:
        seed = message.strip()
        for token in ("灵感", "创意", "idea", "帮我", "发散", "挑战", "反方", "第一性原理", "类比", "收敛", "评估"):
            seed = seed.replace(token, "")
        return seed.strip(" ，。？?：:") or "一个值得验证的新想法"

    def _detect_mode(self, message: str) -> str:
        normalized = message.lower()
        if "反方" in message or "挑战" in message:
            return "challenge"
        if "第一性原理" in message:
            return "first_principles"
        if "类比" in message:
            return "analogy"
        if "收敛" in message or "评估" in message:
            return "convergence"
        if "scenario" in normalized or "场景" in message:
            return "scenario"
        return "divergent"

    def _title(self, seed: str, mode: str) -> str:
        labels = {
            "challenge": "反方挑战",
            "first_principles": "第一性原理",
            "analogy": "跨域类比",
            "convergence": "收敛评估",
            "scenario": "场景推演",
            "divergent": "灵感发散",
        }
        return f"{labels.get(mode, '灵感')}：{seed}"

    def _counter_challenge(self, seed: str) -> str:
        return f"如果 {seed} 只是展示智能感而没有降低用户决策成本，它就不是高价值功能。"

    def _analogy(self, seed: str, mode: str) -> str:
        if mode == "analogy":
            return f"把 {seed} 当作一个个人操作系统的控制台，而不是单次聊天结果。"
        return f"可以参考任务看板的做法，把 {seed} 拆成输入、判断、输出和反馈四段。"

    def _mvp_plan(self, seed: str) -> str:
        return f"先做一个只服务单一用户场景的版本：输入 {seed}，生成建议，保存结果，并收集一次反馈。"

    def _risks(self, mode: str) -> list[str]:
        risks = ["价值表达过宽，导致 MVP 无法验收", "缺少反馈数据，难以判断是否继续投入"]
        if mode == "divergent":
            risks.append("发散过多，短期无法转成行动")
        if mode == "convergence":
            risks.append("过早收敛，可能错过更有价值的方向")
        return risks

    def _next_steps(self, seed: str) -> list[str]:
        return [
            f"写下 {seed} 的目标用户和触发场景",
            "定义一个 30 分钟内可验证的输出样例",
            "把验证结果保存为 Idea Card 反馈",
        ]

    def _score(self, mode: str) -> float:
        scores = {
            "challenge": 0.72,
            "first_principles": 0.76,
            "analogy": 0.7,
            "convergence": 0.8,
            "scenario": 0.74,
            "divergent": 0.68,
        }
        return scores.get(mode, 0.65)

    def _compose_body(self, card: dict) -> str:
        return "\n".join(
            [
                f"方向：{card['direction']}",
                f"目标用户：{card['target_user']}",
                f"痛点：{card['pain_point']}",
                f"核心假设：{card['core_assumption']}",
                f"反方挑战：{card['counter_challenge']}",
                f"跨域类比：{card['analogy']}",
                f"MVP 方案：{card['mvp_plan']}",
                "风险：" + "；".join(card["risks"]),
                "下一步：" + "；".join(card["next_steps"]),
            ]
        )
