from __future__ import annotations

from pathlib import Path
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from hermes_app.api.routes import create_api_router
from hermes_app.core.config import get_settings
from hermes_app.core.database import Database
from hermes_app.services.actions import ActionService
from hermes_app.services.inspiration import InspirationService
from hermes_app.services.intent_router import IntentRouter
from hermes_app.services.logs import ExecutionLogService
from hermes_app.services.memory import MemoryService
from hermes_app.services.orchestrator import HermesOrchestrator
from hermes_app.services.reminders import ReminderService
from hermes_app.services.safety import SafetyService
from hermes_app.services.skills import SkillRegistry
from hermes_app.services.task_decomposer import TaskDecomposer
from hermes_app.services.tools import ToolRegistry
from hermes_app.services.wardrobe import WardrobeService
from hermes_app.services.weather import WeatherService


settings = get_settings()
db = Database(settings.database_path)
db.init()

memory_service = MemoryService(db)
reminder_service = ReminderService(db)
wardrobe_service = WardrobeService(db)
tool_registry = ToolRegistry(db, memory_service, reminder_service, wardrobe_service)
action_service = ActionService(db, memory_service, tool_registry)
skill_registry = SkillRegistry()
log_service = ExecutionLogService(db)
weather_service = WeatherService(db)
orchestrator = HermesOrchestrator(
    intent_router=IntentRouter(),
    task_decomposer=TaskDecomposer(),
    safety=SafetyService(),
    memory=memory_service,
    actions=action_service,
    skills=skill_registry,
    inspiration=InspirationService(),
    weather=weather_service,
    logs=log_service,
)

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parent / "web"
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
app.include_router(
    create_api_router(orchestrator, memory_service, action_service, skill_registry, weather_service, log_service)
)


@app.middleware("http")
async def local_token_guard(request: Request, call_next):
    local_token = os.getenv("HERMES_LOCAL_TOKEN", "")
    if local_token and request.url.path.startswith("/api/") and request.url.path != "/api/health":
        header_token = request.headers.get("x-hermes-token", "")
        bearer = request.headers.get("authorization", "")
        bearer_token = bearer.removeprefix("Bearer ").strip() if bearer.startswith("Bearer ") else ""
        query_token = request.query_params.get("token", "")
        provided_token = header_token or bearer_token or query_token
        if not secrets.compare_digest(provided_token, local_token):
            return JSONResponse({"detail": "Invalid local Hermes token."}, status_code=401)
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "token": request.query_params.get("token", "")})
