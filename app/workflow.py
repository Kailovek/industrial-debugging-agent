import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.knowledge import search_entries
from app.tools import execute_tool


class AgentState(TypedDict, total=False):
    question: str
    device_type: str
    context: dict[str, Any]
    intent: str
    parsed_parameters: dict[str, float | str]
    knowledge: list[dict[str, str]]
    analysis: str
    tool_calls: list[dict[str, Any]]
    warnings: list[str]
    plan: dict[str, Any]
    validation_errors: list[str]
    reflected: bool
    trace: list[dict[str, str]]


PARAMETER_NAMES = {
    "voltage": "voltage",
    "电压": "voltage",
    "current": "current",
    "电流": "current",
    "frequency": "frequency",
    "频率": "frequency",
    "temperature": "temperature",
    "温度": "temperature",
}
PARAMETER_PATTERN = re.compile(
    r"(voltage|current|frequency|temperature|电压|电流|频率|温度)"
    r"\s*(?:[:=为]|is)?\s*(-?\d+(?:\.\d+)?)\s*(V|A|Hz|C|℃)?",
    re.IGNORECASE,
)


def _event(state: AgentState, node: str, summary: str, status: str = "succeeded") -> list:
    return [*state.get("trace", []), {"node": node, "status": status, "summary": summary}]


def build_workflow(db: Session):
    def classify_intent(state: AgentState) -> dict[str, Any]:
        question = state["question"].lower()
        if any(term in question for term in ("故障", "告警", "异常", "fault", "alarm")):
            intent = "fault_diagnosis"
        elif any(term in question for term in ("参数", "设置", "parameter", "configure")):
            intent = "parameter_review"
        else:
            intent = "technical_guidance"
        return {
            "intent": intent,
            "trace": _event(state, "intent", f"classified as {intent}"),
        }

    def parse_parameters(state: AgentState) -> dict[str, Any]:
        parameters: dict[str, float | str] = {}
        for name, value, unit in PARAMETER_PATTERN.findall(state["question"]):
            canonical = PARAMETER_NAMES[name.lower()]
            parameters[canonical] = float(value)
            if unit:
                parameters[f"{canonical}_unit"] = unit
        parameters.update(state.get("context", {}).get("parameters", {}))
        return {
            "parsed_parameters": parameters,
            "trace": _event(state, "parameter_parse", f"parsed {len(parameters)} fields"),
        }

    def retrieve_knowledge(state: AgentState) -> dict[str, Any]:
        entries = search_entries(db, state["device_type"], state["question"])
        knowledge = [
            {
                "fault_code": entry.fault_code,
                "symptom": entry.symptom,
                "probable_cause": entry.probable_cause,
                "safe_action": entry.safe_action,
                "citation": f"[{entry.source}:{entry.fault_code}]",
            }
            for entry in entries
        ]
        return {
            "knowledge": knowledge,
            "trace": _event(state, "knowledge_retrieval", f"retrieved {len(knowledge)} cases"),
        }

    def analyze_fault(state: AgentState) -> dict[str, Any]:
        knowledge = state.get("knowledge", [])
        cause = knowledge[0]["probable_cause"] if knowledge else "insufficient reference evidence"
        return {
            "analysis": f"Primary diagnostic hypothesis: {cause}",
            "trace": _event(state, "fault_analysis", "formed an evidence-linked hypothesis"),
        }

    def call_tools(state: AgentState) -> dict[str, Any]:
        calls = []
        specifications = [
            ("validate_parameter_range", {"parameters": state.get("parsed_parameters", {})}),
            ("query_fault_tree", {"symptom": state["question"]}),
            ("lookup_case_summary", {"knowledge_count": len(state.get("knowledge", []))}),
        ]
        for name, arguments in specifications:
            calls.append(
                {"name": name, "arguments": arguments, "result": execute_tool(name, arguments)}
            )
        warnings = list(state.get("warnings", []))
        violations = calls[0]["result"].get("violations", [])
        if violations:
            warnings.append("One or more parameters are outside the Demo safety range.")
        return {
            "tool_calls": calls,
            "warnings": warnings,
            "trace": _event(state, "tool_dispatch", f"executed {len(calls)} registered tools"),
        }

    def generate_plan(state: AgentState) -> dict[str, Any]:
        knowledge = state.get("knowledge", [])
        evidence_steps = [item["safe_action"] for item in knowledge[:2]]
        citations = [item["citation"] for item in knowledge]
        caution = []
        if state.get("reflected"):
            caution.append("参数超出演示安全范围，停止调整并由具备资质的人员复核。")
        plan = {
            "title": "设备故障排查建议",
            "risk_level": "high" if state.get("warnings") else "medium",
            "steps": [
                "将设备置于安全状态并断开自动执行输出。",
                *caution,
                *evidence_steps,
                "核对告警记录与参数变更记录，完成后进行受控验证。",
            ],
            "stop_conditions": [
                "发现绝缘损坏、异常温升或不可控运动时立即停止。",
                "现场条件与引用资料不一致时不得继续执行。",
            ],
            "citations": citations,
        }
        return {
            "plan": plan,
            "trace": _event(state, "plan_generation", f"generated {len(plan['steps'])} steps"),
        }

    def validate_result(state: AgentState) -> dict[str, Any]:
        errors = []
        plan = state.get("plan", {})
        if len(plan.get("steps", [])) < 3:
            errors.append("plan_has_too_few_steps")
        if not plan.get("stop_conditions"):
            errors.append("missing_stop_conditions")
        violations = state.get("tool_calls", [{}])[0].get("result", {}).get("violations", [])
        if violations and not state.get("reflected"):
            errors.append("parameter_range_requires_reflection")
        return {
            "validation_errors": errors,
            "trace": _event(state, "result_validation", f"found {len(errors)} issues"),
        }

    def reflect(state: AgentState) -> dict[str, Any]:
        return {
            "reflected": True,
            "trace": _event(
                state,
                "reflection",
                "added a conservative stop-and-review instruction",
                status="retried",
            ),
        }

    def route_validation(state: AgentState) -> str:
        return (
            "reflect" if state.get("validation_errors") and not state.get("reflected") else "done"
        )

    graph = StateGraph(AgentState)
    graph.add_node("intent", classify_intent)
    graph.add_node("parameter_parse", parse_parameters)
    graph.add_node("knowledge_retrieval", retrieve_knowledge)
    graph.add_node("fault_analysis", analyze_fault)
    graph.add_node("tool_dispatch", call_tools)
    graph.add_node("plan_generation", generate_plan)
    graph.add_node("result_validation", validate_result)
    graph.add_node("reflection", reflect)
    graph.add_edge(START, "intent")
    graph.add_edge("intent", "parameter_parse")
    graph.add_edge("parameter_parse", "knowledge_retrieval")
    graph.add_edge("knowledge_retrieval", "fault_analysis")
    graph.add_edge("fault_analysis", "tool_dispatch")
    graph.add_edge("tool_dispatch", "plan_generation")
    graph.add_edge("plan_generation", "result_validation")
    graph.add_conditional_edges(
        "result_validation", route_validation, {"reflect": "reflection", "done": END}
    )
    graph.add_edge("reflection", "plan_generation")
    return graph.compile()
