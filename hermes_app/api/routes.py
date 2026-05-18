from __future__ import annotations

from fastapi import APIRouter, HTTPException

from hermes_app.schemas import ChatRequest, ChatResponse, ConfirmActionResponse
from hermes_app.services.actions import ActionService
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.memory import MemoryService
from hermes_app.services.orchestrator import HermesOrchestrator
from hermes_app.services.skills import SkillRegistry
from hermes_app.services.weather import WeatherService


def create_api_router(
    orchestrator: HermesOrchestrator,
    memory: MemoryService,
    actions: ActionService,
    skills: SkillRegistry,
    weather: WeatherService,
    logs: ExecutionLogService,
) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "hermes"}

    @router.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return orchestrator.handle_chat(request)

    @router.post("/decompose")
    def decompose(request: ChatRequest) -> dict:
        intent = orchestrator.intent_router.route(request.message)
        risk_level = orchestrator.safety.classify(request.message, intent)
        return orchestrator.task_decomposer.decompose(request.message, intent, risk_level).model_dump()

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
    def list_reminders() -> list[dict]:
        return orchestrator.actions.db.query("SELECT * FROM reminders ORDER BY created_at DESC LIMIT 80")

    @router.get("/ideas")
    def list_ideas() -> list[dict]:
        return orchestrator.actions.db.query("SELECT * FROM idea_cards ORDER BY created_at DESC LIMIT 80")

    @router.get("/wardrobe")
    def list_wardrobe() -> list[dict]:
        return orchestrator.actions.db.query("SELECT * FROM wardrobe_items ORDER BY created_at DESC LIMIT 80")

    @router.get("/weather")
    def lookup_weather(location: str) -> dict:
        return weather.lookup(location)

    @router.get("/weather/cache")
    def list_weather_cache() -> list[dict]:
        return weather.list_cache()

    @router.get("/skills")
    def list_skills() -> list[dict]:
        return [skill.model_dump() for skill in skills.list()]

    @router.get("/logs")
    def list_logs() -> list[dict]:
        return logs.list()

    return router
