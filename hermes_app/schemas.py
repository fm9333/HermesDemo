from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "sensitive", "blocked"]
ActionStatus = Literal["pending", "executed", "rejected", "failed"]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class MemoryCandidate(BaseModel):
    memory_type: str
    key: str
    value: str
    sensitivity: str = "normal"
    confidence: float = Field(default=0.72, ge=0, le=1)


class PendingAction(BaseModel):
    id: str
    action_type: str
    risk_level: RiskLevel
    status: ActionStatus
    payload: dict[str, Any]
    reason: str
    created_at: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    risk_level: RiskLevel
    cards: list[dict[str, Any]] = Field(default_factory=list)
    memory_candidates: list[MemoryCandidate] = Field(default_factory=list)
    actions: list[PendingAction] = Field(default_factory=list)
    execution_id: str


class ConfirmActionResponse(BaseModel):
    action: PendingAction
    result: dict[str, Any]


class SkillContract(BaseModel):
    skill_id: str
    title: str
    autonomy_zone: Literal["green", "yellow", "red"]
    allowed_inputs: list[str]
    allowed_outputs: list[str]
    can_write_memory: bool
    can_call_tools: list[str]
    cannot_call_tools: list[str]
    requires_eval_before_activation: bool
    rollback_supported: bool

