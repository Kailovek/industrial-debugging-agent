from collections.abc import Callable
from typing import Any

Tool = Callable[[dict[str, Any]], dict[str, Any]]


PARAMETER_LIMITS = {
    "voltage": (0.0, 690.0, "V"),
    "current": (0.0, 500.0, "A"),
    "frequency": (0.0, 400.0, "Hz"),
    "temperature": (-40.0, 150.0, "C"),
}


def validate_parameter_range(arguments: dict[str, Any]) -> dict[str, Any]:
    violations = []
    for name, raw_value in arguments.get("parameters", {}).items():
        if name not in PARAMETER_LIMITS or not isinstance(raw_value, int | float):
            continue
        minimum, maximum, unit = PARAMETER_LIMITS[name]
        if not minimum <= float(raw_value) <= maximum:
            violations.append(
                {"parameter": name, "value": raw_value, "allowed": [minimum, maximum], "unit": unit}
            )
    return {"valid": not violations, "violations": violations}


def query_fault_tree(arguments: dict[str, Any]) -> dict[str, Any]:
    symptom = str(arguments.get("symptom", "")).lower()
    if "过流" in symptom or "overcurrent" in symptom:
        branch = ["mechanical_load", "acceleration_parameter", "motor_wiring"]
    elif "过压" in symptom or "overvoltage" in symptom:
        branch = ["deceleration_parameter", "braking_unit", "supply_quality"]
    else:
        branch = ["power", "connection", "parameter", "communication"]
    return {"fault_tree": branch, "requires_isolation": True}


def lookup_case_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "matched_cases": int(arguments.get("knowledge_count", 0)),
        "scope": "synthetic-demo-cases",
    }


TOOL_REGISTRY: dict[str, Tool] = {
    "validate_parameter_range": validate_parameter_range,
    "query_fault_tree": query_fault_tree,
    "lookup_case_summary": lookup_case_summary,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name not in TOOL_REGISTRY:
        return {"error": "tool_not_registered"}
    return TOOL_REGISTRY[name](arguments)
