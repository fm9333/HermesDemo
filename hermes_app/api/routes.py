from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from hermes_app.schemas import ChatRequest, ChatResponse, ConfirmActionResponse
from hermes_app.services.actions import ActionService
from hermes_app.services.context_signals import ContextSignalService
from hermes_app.services.files import FileService
from hermes_app.services.images import ImageService
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.memory import MemoryService
from hermes_app.services.orchestrator import HermesOrchestrator
from hermes_app.services.opportunities import OpportunityEngine
from hermes_app.services.recommendations import RecommendationService
from hermes_app.services.reminders import ReminderService
from hermes_app.services.scenes import SceneService
from hermes_app.services.skill_runtime import SkillRuntime
from hermes_app.services.skills import SkillRegistry
from hermes_app.services.wardrobe import WardrobeService
from hermes_app.services.weather import WeatherService


def create_api_router(
    orchestrator: HermesOrchestrator,
    memory: MemoryService,
    actions: ActionService,
    skills: SkillRegistry,
    skill_runtime: SkillRuntime,
    weather: WeatherService,
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
        return orchestrator.actions.db.query("SELECT * FROM idea_cards ORDER BY created_at DESC LIMIT 80")

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

    @router.get("/skills")
    def list_skills() -> list[dict]:
        return [skill.model_dump() for skill in skills.list()]

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
        return skill_runtime.run("document.summarize", text)

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
