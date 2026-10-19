from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DebugRequest(BaseModel):
    question: str = Field(min_length=3, max_length=3000)
    device_type: str = Field(default="generic_drive", min_length=2, max_length=64)
    context: dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    node: str
    status: Literal["succeeded", "retried"]
    summary: str


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class DebugPlan(BaseModel):
    title: str
    risk_level: Literal["low", "medium", "high", "unknown"]
    steps: list[str]
    stop_conditions: list[str]
    citations: list[str]


class AgentRunResponse(BaseModel):
    run_id: UUID
    status: Literal["succeeded", "failed"]
    intent: str
    device_type: str
    parsed_parameters: dict[str, float | str]
    plan: DebugPlan
    tool_calls: list[ToolCall]
    warnings: list[str]
    trace: list[TraceEvent]
    created_at: datetime


class KnowledgeCreate(BaseModel):
    device_type: str = Field(min_length=2, max_length=64)
    fault_code: str = Field(min_length=1, max_length=64)
    symptom: str = Field(min_length=3, max_length=512)
    probable_cause: str = Field(min_length=3, max_length=2000)
    safe_action: str = Field(min_length=3, max_length=2000)
    source: str = Field(default="public-demo", min_length=2, max_length=128)


class KnowledgeRead(KnowledgeCreate):
    id: UUID
