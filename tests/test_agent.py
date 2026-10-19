def test_health_reports_demo_dependencies(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
    assert response.json()["dependencies"]["llm"] == "ready"


def test_fault_workflow_executes_all_nodes_and_tools(client):
    response = client.post(
        "/api/v1/runs",
        json={
            "question": "驱动器启动时报过流告警，电流=24A，应该如何排查？",
            "device_type": "generic_drive",
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["intent"] == "fault_diagnosis"
    assert body["parsed_parameters"]["current"] == 24.0
    assert len(body["tool_calls"]) == 3
    assert body["plan"]["citations"]
    nodes = [event["node"] for event in body["trace"]]
    assert nodes == [
        "intent",
        "parameter_parse",
        "knowledge_retrieval",
        "fault_analysis",
        "tool_dispatch",
        "plan_generation",
        "result_validation",
    ]


def test_out_of_range_parameter_triggers_reflection(client):
    response = client.post(
        "/api/v1/runs",
        json={
            "question": "设备过压告警，voltage=900V，请给出处理建议",
            "device_type": "generic_drive",
        },
    )
    body = response.json()
    assert response.status_code == 202
    assert body["warnings"]
    assert body["plan"]["risk_level"] == "high"
    nodes = [event["node"] for event in body["trace"]]
    assert "reflection" in nodes
    assert nodes.count("plan_generation") == 2


def test_run_and_trace_are_persisted(client):
    created = client.post(
        "/api/v1/runs",
        json={"question": "传感器出现信号丢失故障", "device_type": "generic_sensor"},
    ).json()
    run_id = created["run_id"]

    fetched = client.get(f"/api/v1/runs/{run_id}")
    trace = client.get(f"/api/v1/runs/{run_id}/trace")

    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == run_id
    assert trace.status_code == 200
    assert trace.json()[0]["node"] == "intent"


def test_missing_run_returns_structured_error(client):
    response = client.get("/api/v1/runs/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404
    assert response.json()["code"] == "run_not_found"
