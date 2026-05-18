from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, UploadFile

from hermes_app.schemas import ChatRequest, ChatResponse, ConfirmActionResponse, MemoryCandidate
from hermes_app.services.actions import ActionService
from hermes_app.services.autonomy import AutonomyZoneClassifier
from hermes_app.services.backups import BackupService
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.evals import EvalRunner
from hermes_app.services.exports import ExportService
from hermes_app.services.files import FileService
from hermes_app.services.growth import GrowthLogService
from hermes_app.services.home_cards import HomeCardService
from hermes_app.services.images import ImageService
from hermes_app.services.llm_client import LLMClient
from hermes_app.services.llm_providers import LLMProviderService
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.maps import MapService
from hermes_app.services.memory import MemoryService
from hermes_app.services.news import NewsService
from hermes_app.services.orchestrator import HermesOrchestrator
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.personal_skills import PersonalSkillService
from hermes_app.services.prd_drafts import PrdDraftService
from hermes_app.services.proactive import ProactiveSuggestionService
from hermes_app.services.prompt_library import PromptLibrary
from hermes_app.services.providers import ProviderRegistry
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.reminders import ReminderService
from hermes_app.services.runtime_state import RuntimeStateService
from hermes_app.services.scenes import SceneService
from hermes_app.services.settings import SettingsService
from hermes_app.services.skill_curator import SkillCuratorService
from hermes_app.services.skill_runtime import SkillRuntime
from hermes_app.services.skills import SkillRegistry
from hermes_app.services.todos import TodoService
from hermes_app.services.triggers import TriggerService
from hermes_app.services.updates import UpdateService
from hermes_app.services.wardrobe import WardrobeService
from hermes_app.services.weather import WeatherService
from hermes_app.services.weekly_reviews import WeeklyReviewService


def _decode_json_list(value: str | None) -> list:
    try:
        data = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _deserialize_idea(row: dict) -> dict:
    row["tags"] = _decode_json_list(row.pop("tags_json", "[]"))
    row["risks"] = _decode_json_list(row.pop("risks_json", "[]"))
    row["next_steps"] = _decode_json_list(row.pop("next_steps_json", "[]"))
    return row


def create_api_router(
    orchestrator: HermesOrchestrator,
    autonomy: AutonomyZoneClassifier,
    eval_runner: EvalRunner,
    growth_logs: GrowthLogService,
    settings: SettingsService,
    providers: ProviderRegistry,
    llm_providers: LLMProviderService,
    llm_client: LLMClient,
    prompts: PromptLibrary,
    backups: BackupService,
    exports: ExportService,
    runtime_state: RuntimeStateService,
    updates: UpdateService,
    proactive: ProactiveSuggestionService,
    triggers: TriggerService,
    weekly_reviews: WeeklyReviewService,
    home_cards: HomeCardService,
    memory: MemoryService,
    actions: ActionService,
    skills: SkillRegistry,
    skill_runtime: SkillRuntime,
    personal_skills: PersonalSkillService,
    skill_curator: SkillCuratorService,
    todos: TodoService,
    prd_drafts: PrdDraftService,
    weather: WeatherService,
    news: NewsService,
    maps: MapService,
    files: FileService,
    images: ImageService,
    scenes: SceneService,
    context_signals: ContextSignalService,
    opportunities: OpportunityEngine,
    recommendations: RecommendationService,
    logs: ExecutionLogService,
) -> APIRouter:
    reminder_service = ReminderService(actions.db)
    wardrobe_service = WardrobeService(actions.db)
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "hermes"}

    @router.get("/database/migrations")
    def list_database_migrations() -> list[dict]:
        return actions.db.list_migrations()

    @router.get("/performance/indexes")
    def list_performance_indexes() -> list[dict]:
        return actions.db.list_indexes()

    @router.get("/runtime/recovery")
    def runtime_recovery_status() -> dict:
        return runtime_state.heartbeat()

    @router.get("/updates/status")
    def update_status() -> dict:
        return updates.status()

    @router.post("/updates/check")
    def check_updates(payload: dict | None = None) -> dict:
        return updates.check(manifest_url=(payload or {}).get("manifest_url"))

    @router.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return orchestrator.handle_chat(request)

    @router.post("/decompose")
    def decompose(request: ChatRequest) -> dict:
        intent = orchestrator.intent_router.route(request.message)
        risk_level = orchestrator.safety.classify(request.message, intent)
        return orchestrator.task_decomposer.decompose(request.message, intent, risk_level).model_dump()

    @router.get("/autonomy/zones")
    def list_autonomy_zones() -> list[dict]:
        return autonomy.list_zones()

    @router.post("/autonomy/classify")
    def classify_autonomy_zone(payload: dict) -> dict:
        return autonomy.classify(payload)

    @router.post("/red-zone/check")
    def check_red_zone(request: ChatRequest) -> dict:
        intent = orchestrator.intent_router.route(request.message)
        result = orchestrator.safety.red_zone_check(request.message, intent)
        return {"intent": intent, **result}

    @router.get("/red-zone/rules")
    def list_red_zone_rules() -> list[dict]:
        return [
            {
                "rule": "blocked_keywords",
                "risk_level": "blocked",
                "keywords": list(orchestrator.safety.high_risk_keywords),
            },
            {
                "rule": "sensitive_keywords",
                "risk_level": "sensitive",
                "keywords": list(orchestrator.safety.sensitive_keywords),
            },
        ]

    @router.get("/eval/suites")
    def list_eval_suites() -> list[dict]:
        return eval_runner.list_suites()

    @router.get("/eval/runs")
    def list_eval_runs(suite_id: str | None = None) -> list[dict]:
        return eval_runner.list_runs(suite_id=suite_id)

    @router.post("/eval/suites/{suite_id}/run")
    def run_eval_suite(suite_id: str) -> dict:
        try:
            return eval_runner.run(suite_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/growth-log")
    def list_growth_logs(status: str | None = None) -> list[dict]:
        return growth_logs.list(status=status)

    @router.post("/growth-log")
    def create_growth_log(payload: dict) -> dict:
        return growth_logs.create(
            title=payload.get("title", ""),
            zone=payload.get("zone", "green"),
            source_task=payload.get("source_task", "manual"),
            impact=payload.get("impact", ""),
            payload=payload.get("payload", {}),
        )

    @router.post("/growth-log/{log_id}/rollback")
    def rollback_growth_log(log_id: str) -> dict:
        try:
            return growth_logs.rollback(log_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/settings")
    def list_settings() -> list[dict]:
        return settings.list()

    @router.patch("/settings/{key}")
    def update_setting(key: str, payload: dict) -> dict:
        try:
            return settings.update(key, payload.get("value"))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/providers")
    def list_providers() -> list[dict]:
        return providers.list()

    @router.get("/llm/providers")
    def list_llm_providers() -> list[dict]:
        return llm_providers.list()

    @router.post("/llm/providers")
    def create_llm_provider(payload: dict) -> dict:
        try:
            return llm_providers.create(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/llm/providers/{provider_id}")
    def get_llm_provider(provider_id: str) -> dict:
        provider = llm_providers.get(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="LLM provider not found.")
        return provider

    @router.patch("/llm/providers/{provider_id}")
    def update_llm_provider(provider_id: str, payload: dict) -> dict:
        try:
            return llm_providers.update(provider_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/llm/providers/{provider_id}")
    def delete_llm_provider(provider_id: str) -> dict:
        try:
            return llm_providers.delete(provider_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/llm/providers/{provider_id}/default")
    def set_default_llm_provider(provider_id: str) -> dict:
        try:
            return llm_providers.set_default(provider_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/llm/providers/{provider_id}/test")
    def test_llm_provider(provider_id: str) -> dict:
        try:
            return llm_client.test_provider(provider_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/llm/chat")
    def llm_chat(payload: dict) -> dict:
        message = str(payload.get("message", "")).strip()
        if not message:
            raise HTTPException(status_code=400, detail="message is required.")
        return llm_client.chat(
            message,
            provider_id=payload.get("provider_id"),
            prompt_id=payload.get("prompt_id", "hermes.agent.core"),
            context=payload.get("context") or {},
            contains_file_context=bool(payload.get("contains_file_context", False)),
        )

    @router.get("/llm/calls")
    def list_llm_calls(limit: int = 80) -> list[dict]:
        return llm_providers.list_calls(limit=limit)

    @router.get("/llm/file-policy")
    def get_llm_file_policy() -> dict:
        global_setting = settings.get("llm_allow_cloud_file_context")
        providers_payload = []
        for provider in llm_providers.list():
            is_local = provider["provider_type"] == "local_openai_compatible"
            providers_payload.append(
                {
                    "provider_id": provider["provider_id"],
                    "name": provider["name"],
                    "provider_type": provider["provider_type"],
                    "status": provider["status"],
                    "is_default": provider["is_default"],
                    "allow_file_context": provider["allow_file_context"],
                    "effective_file_context_allowed": is_local
                    or (bool(global_setting and global_setting["value"]) and provider["allow_file_context"]),
                    "reason": "local_provider"
                    if is_local
                    else "requires_global_and_provider_allowance",
                }
            )
        return {
            "global_allow_cloud_file_context": bool(global_setting and global_setting["value"]),
            "default_policy": "block_cloud_file_context",
            "secret_protection": llm_providers.secret_status(),
            "providers": providers_payload,
        }

    @router.get("/llm/secret-policy")
    def get_llm_secret_policy() -> dict:
        return llm_providers.secret_status()

    @router.post("/llm/secret-policy/rotate")
    def rotate_llm_legacy_secrets() -> dict:
        return llm_providers.rotate_legacy_secrets()

    @router.get("/prompts")
    def list_prompts() -> list[dict]:
        return prompts.list()

    @router.get("/prompts/{prompt_id:path}")
    def get_prompt(prompt_id: str) -> dict:
        try:
            return prompts.get(prompt_id).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/providers/{provider_id}/connect")
    def connect_provider(provider_id: str, payload: dict | None = None) -> dict:
        try:
            return providers.connect(provider_id, config=(payload or {}).get("config", {}))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/providers/{provider_id}/disconnect")
    def disconnect_provider(provider_id: str) -> dict:
        try:
            return providers.disconnect(provider_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/backups")
    def list_backups() -> list[dict]:
        return backups.list()

    @router.post("/backups")
    def create_backup(payload: dict | None = None) -> dict:
        return backups.create(note=(payload or {}).get("note", "manual"))

    @router.post("/backups/{backup_id}/restore")
    def restore_backup(backup_id: str) -> dict:
        try:
            return backups.restore(backup_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/exports")
    def list_exports() -> list[dict]:
        return exports.list()

    @router.post("/exports")
    def create_export(payload: dict | None = None) -> dict:
        try:
            return exports.create(
                tables=(payload or {}).get("tables"),
                note=(payload or {}).get("note", "manual"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/proactive/suggestions")
    def list_proactive_suggestions(limit: int = 20) -> list[dict]:
        return proactive.list(limit=limit)

    @router.post("/triggers/run")
    def run_trigger(payload: dict | None = None) -> dict:
        return triggers.run(trigger_type=(payload or {}).get("trigger_type", "manual"))

    @router.get("/triggers/history")
    def list_trigger_runs() -> list[dict]:
        return triggers.list_runs()

    @router.post("/weekly-reviews/generate")
    def generate_weekly_review() -> dict:
        return weekly_reviews.generate()

    @router.get("/weekly-reviews")
    def list_weekly_reviews() -> list[dict]:
        return weekly_reviews.list()

    @router.get("/home/cards")
    def list_home_cards(limit: int = 12) -> list[dict]:
        return home_cards.list(limit=limit)

    @router.get("/memory")
    def list_memory() -> list[dict]:
        return memory.list()

    @router.get("/memory/candidates")
    def list_memory_candidates(status: str | None = None) -> list[dict]:
        return memory.list_candidates(status=status)

    @router.post("/memory/candidates/{candidate_id}/confirm")
    def confirm_memory_candidate(candidate_id: str) -> dict:
        try:
            return memory.confirm_candidate(candidate_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/memory/candidates/{candidate_id}/reject")
    def reject_memory_candidate(candidate_id: str) -> dict:
        try:
            return memory.reject_candidate(candidate_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/memory/{memory_id}")
    def delete_memory(memory_id: str) -> dict:
        return {"deleted": memory.delete(memory_id)}

    @router.get("/actions/pending")
    def list_pending_actions() -> list[dict]:
        return [action.model_dump() for action in actions.list_pending()]

    @router.get("/yellow-zone/pending")
    def list_yellow_zone_pending() -> list[dict]:
        return [
            action.model_dump()
            for action in actions.list_pending()
            if action.risk_level == "medium"
        ]

    @router.get("/tools")
    def list_tools() -> list[dict]:
        return [tool.model_dump() for tool in actions.tool_registry.list()]

    @router.post("/actions/{action_id}/confirm", response_model=ConfirmActionResponse)
    def confirm_action(action_id: str) -> ConfirmActionResponse:
        try:
            action, result = actions.confirm(action_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ConfirmActionResponse(action=action, result=result)

    @router.post("/actions/{action_id}/reject")
    def reject_action(action_id: str) -> dict:
        try:
            action = actions.reject(action_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return action.model_dump()

    @router.get("/reminders")
    def list_reminders(status: str | None = None) -> list[dict]:
        return reminder_service.list(status=status)

    @router.get("/reminders/{reminder_id}")
    def get_reminder(reminder_id: str) -> dict:
        item = reminder_service.get(reminder_id)
        if not item:
            raise HTTPException(status_code=404, detail="Reminder not found.")
        return item

    @router.patch("/reminders/{reminder_id}")
    def update_reminder(reminder_id: str, payload: dict) -> dict:
        try:
            return reminder_service.update(
                reminder_id,
                title=payload.get("title"),
                due_at_text=payload.get("due_at_text"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/reminders/{reminder_id}/complete")
    def complete_reminder(reminder_id: str) -> dict:
        try:
            return reminder_service.set_status(reminder_id, "completed")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/reminders/{reminder_id}")
    def delete_reminder(reminder_id: str) -> dict:
        try:
            return reminder_service.set_status(reminder_id, "deleted")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/ideas")
    def list_ideas() -> list[dict]:
        rows = orchestrator.actions.db.query("SELECT * FROM idea_cards ORDER BY created_at DESC LIMIT 80")
        return [_deserialize_idea(row) for row in rows]

    @router.get("/ideas/{idea_id}")
    def get_idea(idea_id: str) -> dict:
        row = orchestrator.actions.db.query_one("SELECT * FROM idea_cards WHERE id = ?", (idea_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found.")
        return _deserialize_idea(row)

    @router.post("/ideas/{idea_id}/to-todo")
    def convert_idea_to_todo(idea_id: str) -> dict:
        row = orchestrator.actions.db.query_one("SELECT * FROM idea_cards WHERE id = ?", (idea_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found.")
        idea = _deserialize_idea(row)
        titles = idea["next_steps"] or [idea.get("mvp_plan") or idea["title"]]
        created = []
        for title in titles:
            existing = todos.get_by_source_title("idea", idea_id, title)
            created.append(existing or todos.create(title, source="idea", source_id=idea_id))
        return {"idea_id": idea_id, "todos": created}

    @router.post("/ideas/{idea_id}/to-prd")
    def convert_idea_to_prd(idea_id: str) -> dict:
        row = orchestrator.actions.db.query_one("SELECT * FROM idea_cards WHERE id = ?", (idea_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found.")
        idea = _deserialize_idea(row)
        return prd_drafts.create_from_idea(idea)

    @router.post("/ideas/{idea_id}/to-scene")
    def convert_idea_to_scene(idea_id: str) -> dict:
        row = orchestrator.actions.db.query_one("SELECT * FROM idea_cards WHERE id = ?", (idea_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found.")
        idea = _deserialize_idea(row)
        context_signal = f"idea:{idea_id}"
        existing = scenes.get_by_source_context("idea", context_signal)
        if existing:
            return existing
        return scenes.create(
            name=f"Idea 场景：{idea['title']}",
            source="idea",
            context_signal=context_signal,
            user_state="idea_review",
            opportunity=idea.get("direction") or idea["title"],
            decision_policy="confirm_before_interrupt",
            output_type="recommendation",
            status="active",
        )

    @router.post("/ideas/{idea_id}/preference-candidate")
    def create_idea_preference_candidate(idea_id: str) -> dict:
        row = orchestrator.actions.db.query_one("SELECT * FROM idea_cards WHERE id = ?", (idea_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Idea not found.")
        idea = _deserialize_idea(row)
        mode = next((tag for tag in idea["tags"] if tag not in {"inspiration", "idea-card"}), "general")
        value = f"灵感偏好：关注 {idea['direction'] or idea['title']}，适合使用 {mode} 模式推进。"
        existing = orchestrator.actions.db.query_one(
            """
            SELECT * FROM memory_candidates
            WHERE key = ? AND value = ? AND status = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            ("inspiration_preference", value, "pending"),
        )
        candidate = existing or memory.create_candidate(
            MemoryCandidate(
                memory_type="preference",
                key="inspiration_preference",
                value=value,
                sensitivity="normal",
                confidence=0.68,
            ),
            source="idea",
            reason="从已保存 Idea Card 中提取灵感工作偏好，需用户确认后写入长期记忆。",
        )
        action = actions.create_pending(
            "memory.confirm_candidate",
            {"candidate_id": candidate["id"]},
            "medium",
            "灵感偏好会影响后续建议，需要确认后写入长期记忆。",
        )
        return {"candidate": candidate, "action": action.model_dump()}

    @router.get("/prd-drafts")
    def list_prd_drafts(status: str | None = None) -> list[dict]:
        return prd_drafts.list(status=status)

    @router.get("/prd-drafts/{draft_id}")
    def get_prd_draft(draft_id: str) -> dict:
        draft = prd_drafts.get(draft_id)
        if not draft:
            raise HTTPException(status_code=404, detail="PRD draft not found.")
        return draft

    @router.get("/todos")
    def list_todos(status: str | None = None) -> list[dict]:
        return todos.list(status=status)

    @router.post("/todos/{todo_id}/complete")
    def complete_todo(todo_id: str) -> dict:
        try:
            return todos.complete(todo_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/wardrobe")
    def list_wardrobe(status: str | None = None) -> list[dict]:
        return wardrobe_service.list(status=status)

    @router.get("/wardrobe/{item_id}")
    def get_wardrobe_item(item_id: str) -> dict:
        item = wardrobe_service.get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Wardrobe item not found.")
        return item

    @router.patch("/wardrobe/{item_id}")
    def update_wardrobe_item(item_id: str, payload: dict) -> dict:
        try:
            return wardrobe_service.update(
                item_id,
                name=payload.get("name"),
                category=payload.get("category"),
                color=payload.get("color"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/wardrobe/{item_id}")
    def archive_wardrobe_item(item_id: str) -> dict:
        try:
            return wardrobe_service.set_status(item_id, "archived")
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/weather")
    def lookup_weather(location: str) -> dict:
        return weather.lookup(location)

    @router.get("/weather/cache")
    def list_weather_cache() -> list[dict]:
        return weather.list_cache()

    @router.get("/news")
    def list_news(limit: int = 50) -> list[dict]:
        return news.list(limit=limit)

    @router.post("/news/refresh")
    def refresh_news(limit: int = 20) -> dict:
        return news.refresh(limit=limit)

    @router.get("/news/{article_id}")
    def get_news_article(article_id: str) -> dict:
        item = news.get(article_id)
        if not item:
            raise HTTPException(status_code=404, detail="News article not found.")
        return item

    @router.get("/maps/places")
    def list_map_places(limit: int = 50) -> list[dict]:
        return maps.list(limit=limit)

    @router.post("/maps/search")
    def search_maps(payload: dict) -> dict:
        try:
            return maps.search(payload.get("query", ""), limit=payload.get("limit", 5))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/maps/places/{place_id}")
    def get_map_place(place_id: str) -> dict:
        item = maps.get(place_id)
        if not item:
            raise HTTPException(status_code=404, detail="Map place not found.")
        return item

    @router.get("/skills")
    def list_skills() -> list[dict]:
        return [skill.model_dump() for skill in skills.list()]

    @router.get("/personal-skills")
    def list_personal_skills(status: str | None = None) -> list[dict]:
        return personal_skills.list(status=status)

    @router.post("/personal-skills/drafts")
    def create_personal_skill_draft(payload: dict) -> dict:
        try:
            if payload.get("source_run_id"):
                return personal_skills.create_from_skill_run(
                    payload["source_run_id"],
                    title=payload.get("title"),
                )
            return personal_skills.create_draft(
                title=payload.get("title", ""),
                description=payload.get("description", ""),
                prompt_template=payload.get("prompt_template", ""),
                output_contract=payload.get("output_contract", {}),
                autonomy_zone=payload.get("autonomy_zone", "green"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/personal-skills/{skill_id}")
    def get_personal_skill(skill_id: str) -> dict:
        skill = personal_skills.get(skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Personal skill not found.")
        return skill

    @router.get("/personal-skills/{skill_id}/versions")
    def list_personal_skill_versions(skill_id: str) -> list[dict]:
        if not personal_skills.get(skill_id):
            raise HTTPException(status_code=404, detail="Personal skill not found.")
        return personal_skills.versions(skill_id)

    @router.post("/personal-skills/{skill_id}/evaluate")
    def evaluate_personal_skill(skill_id: str) -> dict:
        try:
            return personal_skills.evaluate(skill_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/personal-skills/{skill_id}/activate")
    def activate_personal_skill(skill_id: str) -> dict:
        try:
            return personal_skills.activate(skill_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/personal-skills/{skill_id}/archive")
    def archive_personal_skill(skill_id: str) -> dict:
        try:
            return personal_skills.archive(skill_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/personal-skills/{skill_id}/rollback")
    def rollback_personal_skill(skill_id: str) -> dict:
        try:
            return personal_skills.rollback(skill_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/personal-skill-patches")
    def list_personal_skill_patches(
        skill_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        return personal_skills.list_patches(skill_id=skill_id, status=status)

    @router.post("/personal-skills/{skill_id}/patches")
    def create_personal_skill_patch(skill_id: str, payload: dict) -> dict:
        try:
            return personal_skills.create_patch(
                skill_id,
                reason=payload.get("reason", ""),
                proposed_prompt_template=payload.get("proposed_prompt_template"),
                proposed_output_contract=payload.get("proposed_output_contract"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/personal-skills/{skill_id}/patches")
    def list_personal_skill_patches_for_skill(skill_id: str) -> list[dict]:
        if not personal_skills.get(skill_id):
            raise HTTPException(status_code=404, detail="Personal skill not found.")
        return personal_skills.list_patches(skill_id=skill_id)

    @router.post("/personal-skill-patches/{patch_id}/evaluate")
    def evaluate_personal_skill_patch(patch_id: str) -> dict:
        try:
            return personal_skills.evaluate_patch(patch_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/personal-skill-patches/{patch_id}/apply")
    def apply_personal_skill_patch(patch_id: str) -> dict:
        try:
            return personal_skills.apply_patch(patch_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/skill-curator/suggestions")
    def list_skill_curator_suggestions() -> list[dict]:
        return skill_curator.suggest()

    @router.post("/skill-curator/run")
    def run_skill_curator() -> dict:
        return skill_curator.run()

    @router.get("/skill-curator/runs")
    def list_skill_curator_runs(limit: int = 50) -> list[dict]:
        return skill_curator.list_runs(limit=limit)

    @router.post("/skills/{skill_id}/run")
    def run_skill(skill_id: str, request: ChatRequest) -> dict:
        return skill_runtime.run(skill_id, request.message)

    @router.get("/skills/runs")
    def list_skill_runs(skill_id: str | None = None) -> list[dict]:
        return skill_runtime.list_runs(skill_id=skill_id)

    @router.post("/files/upload")
    async def upload_file(file: UploadFile = File(...)) -> dict:
        data = await file.read()
        return files.save_upload(file.filename or "upload.bin", file.content_type or "application/octet-stream", data)

    @router.get("/files")
    def list_files() -> list[dict]:
        return files.list()

    @router.get("/files/{file_id}")
    def get_file(file_id: str) -> dict:
        item = files.get(file_id)
        if not item:
            raise HTTPException(status_code=404, detail="File not found.")
        return item

    @router.post("/files/{file_id}/summarize")
    def summarize_file(file_id: str) -> dict:
        try:
            text = files.extract_text(file_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return skill_runtime.run(
            "document.summarize",
            text,
            metadata={"source": "file", "file_id": file_id, "contains_file_context": True},
        )

    @router.post("/images/upload")
    async def upload_image(file: UploadFile = File(...)) -> dict:
        data = await file.read()
        try:
            return images.save_upload(file.filename or "image.bin", file.content_type or "application/octet-stream", data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/images")
    def list_images() -> list[dict]:
        return images.list()

    @router.get("/images/{image_id}")
    def get_image(image_id: str) -> dict:
        item = images.get(image_id)
        if not item:
            raise HTTPException(status_code=404, detail="Image not found.")
        return item

    @router.post("/images/{image_id}/recognize-clothing")
    def recognize_clothing(image_id: str) -> dict:
        try:
            candidate = images.recognize_clothing(image_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        action = actions.create_pending(
            "wardrobe.add",
            candidate["wardrobe_payload"],
            "medium",
            "图片衣物识别结果需要确认后加入衣橱。",
        )
        return {"candidate": candidate, "action": action.model_dump()}

    @router.get("/logs")
    def list_logs() -> list[dict]:
        return logs.list()

    @router.get("/scenes")
    def list_scenes(status: str | None = None) -> list[dict]:
        return scenes.list(status=status)

    @router.post("/scenes")
    def create_scene(payload: dict) -> dict:
        return scenes.create(**payload)

    @router.get("/scenes/runs")
    def list_scene_runs(scene_id: str | None = None) -> list[dict]:
        return scenes.list_runs(scene_id=scene_id)

    @router.get("/scene-feedback")
    def list_all_scene_feedback(scene_id: str | None = None) -> list[dict]:
        return scenes.list_feedback(scene_id=scene_id)

    @router.post("/scenes/{scene_id}/feedback")
    def record_scene_feedback(scene_id: str, payload: dict) -> dict:
        try:
            return scenes.record_feedback(
                scene_id,
                rating=payload.get("rating", "negative"),
                reason=payload.get("reason", ""),
                run_id=payload.get("run_id"),
                payload=payload.get("payload", {}),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/scenes/{scene_id}/feedback")
    def list_scene_feedback(scene_id: str) -> list[dict]:
        if not scenes.get(scene_id):
            raise HTTPException(status_code=404, detail="Scene not found.")
        return scenes.list_feedback(scene_id=scene_id)

    @router.post("/context-signals")
    def collect_context_signal(payload: dict) -> dict:
        return context_signals.collect(
            source=payload.get("source", "manual"),
            signal_type=payload.get("signal_type", "manual"),
            payload=payload.get("payload", {}),
            expires_at=payload.get("expires_at"),
        )

    @router.get("/context-signals")
    def list_context_signals(status: str | None = None, signal_type: str | None = None) -> list[dict]:
        return context_signals.list(status=status, signal_type=signal_type)

    @router.post("/context-signals/{signal_id}/archive")
    def archive_context_signal(signal_id: str) -> dict:
        try:
            return context_signals.archive(signal_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/opportunities/generate")
    def generate_opportunities() -> list[dict]:
        return opportunities.generate()

    @router.get("/opportunities")
    def list_opportunities(status: str | None = None) -> list[dict]:
        return opportunities.list(status=status)

    @router.post("/opportunities/{opportunity_id}/close")
    def close_opportunity(opportunity_id: str) -> dict:
        try:
            return opportunities.close(opportunity_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/recommendations/generate")
    def generate_recommendations() -> list[dict]:
        return recommendations.generate()

    @router.get("/recommendations")
    def list_recommendations(status: str | None = None) -> list[dict]:
        return recommendations.list(status=status)

    @router.post("/recommendations/{recommendation_id}/dismiss")
    def dismiss_recommendation(recommendation_id: str) -> dict:
        try:
            return recommendations.dismiss(recommendation_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/scenes/{scene_id}")
    def get_scene(scene_id: str) -> dict:
        scene = scenes.get(scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found.")
        return scene

    @router.patch("/scenes/{scene_id}")
    def update_scene(scene_id: str, payload: dict) -> dict:
        try:
            return scenes.update(scene_id, **payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/scenes/{scene_id}/pause")
    def pause_scene(scene_id: str) -> dict:
        try:
            return scenes.pause(scene_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/scenes/{scene_id}/run")
    def run_scene(scene_id: str) -> dict:
        try:
            return scenes.run(scene_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
