import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import AgentRun
from app.schemas import AgentRunResponse, DebugPlan, DebugRequest, ToolCall, TraceEvent
from app.workflow import build_workflow


def execute_run(db: Session, payload: DebugRequest) -> AgentRunResponse:
    workflow = build_workflow(db)
    state = workflow.invoke(
        {
            "question": payload.question,
            "device_type": payload.device_type,
            "context": payload.context,
            "warnings": [],
            "trace": [],
            "reflected": False,
        }
    )
    serializable = {
        "intent": state["intent"],
        "device_type": state["device_type"],
        "parsed_parameters": state.get("parsed_parameters", {}),
        "plan": state["plan"],
        "tool_calls": state.get("tool_calls", []),
        "warnings": state.get("warnings", []),
    }
    run = AgentRun(
        status="succeeded",
        request_json=payload.model_dump_json(),
        result_json=json.dumps(serializable, ensure_ascii=False),
        trace_json=json.dumps(state["trace"], ensure_ascii=False),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return _to_response(run)


def get_run(db: Session, run_id: UUID) -> AgentRunResponse:
    run = db.get(AgentRun, str(run_id))
    if run is None:
        raise AppError(404, "run_not_found", "Agent run was not found")
    return _to_response(run)


def get_trace(db: Session, run_id: UUID) -> list[TraceEvent]:
    run = db.get(AgentRun, str(run_id))
    if run is None:
        raise AppError(404, "run_not_found", "Agent run was not found")
    return [TraceEvent.model_validate(item) for item in json.loads(run.trace_json)]


def _to_response(run: AgentRun) -> AgentRunResponse:
    result = json.loads(run.result_json)
    return AgentRunResponse(
        run_id=run.id,
        status=run.status,
        intent=result["intent"],
        device_type=result["device_type"],
        parsed_parameters=result["parsed_parameters"],
        plan=DebugPlan.model_validate(result["plan"]),
        tool_calls=[ToolCall.model_validate(item) for item in result["tool_calls"]],
        warnings=result["warnings"],
        trace=[TraceEvent.model_validate(item) for item in json.loads(run.trace_json)],
        created_at=run.created_at,
    )
