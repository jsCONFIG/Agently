from __future__ import annotations

import http.client
import json
import threading
from functools import partial
from pathlib import Path
from typing import Iterator
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from TriggerFlowCanvas.backend.flow_builder import FlowBuilder, create_builtin_registry
from TriggerFlowCanvas.backend.main import CanvasHTTPRequestHandler, CanvasService
from TriggerFlowCanvas.backend.storage import FlowStorage


def _build_linear_flow() -> dict:
    return {
        "nodes": [
            {
                "id": "start",
                "name": "Start",
                "type": "start",
                "config": {},
                "position": {"x": 0, "y": 0},
            },
            {
                "id": "echo",
                "name": "Echo",
                "type": "echo",
                "config": {"template": "{value}"},
                "position": {"x": 100, "y": 0},
            },
            {
                "id": "upper",
                "name": "Upper",
                "type": "uppercase",
                "config": {},
                "position": {"x": 200, "y": 0},
            },
            {
                "id": "output",
                "name": "Output",
                "type": "output",
                "config": {"label": "result"},
                "position": {"x": 300, "y": 0},
            },
        ],
        "edges": [
            {"id": "start_echo", "source": "start", "target": "echo"},
            {"id": "echo_upper", "source": "echo", "target": "upper"},
            {"id": "upper_output", "source": "upper", "target": "output"},
        ],
        "metadata": {"description": "unit-test"},
    }


@pytest.fixture()
def server(tmp_path: Path) -> Iterator[str]:
    storage = FlowStorage(tmp_path / "flow.json")
    builder = FlowBuilder(create_builtin_registry())
    service = CanvasService(storage=storage, builder=builder)

    from socketserver import ThreadingTCPServer

    handler = partial(CanvasHTTPRequestHandler, service=service)
    httpd = ThreadingTCPServer(("127.0.0.1", 0), handler)
    host, port = httpd.server_address
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


def _http_get(server: str, path: str):
    conn = http.client.HTTPConnection(server)
    conn.request("GET", path)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    conn.close()
    return response.status, json.loads(data)


def _http_post(server: str, path: str, payload: dict):
    conn = http.client.HTTPConnection(server)
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    conn.request("POST", path, body=body, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    conn.close()
    return response.status, json.loads(data)


def test_get_flow_returns_default(server: str):
    status, data = _http_get(server, "/api/flow")
    assert status == 200
    assert any(node["type"] == "start" for node in data["nodes"])


def test_save_and_reload_flow(server: str):
    flow = _build_linear_flow()
    status, response = _http_post(server, "/api/flow", flow)
    assert status == 200
    assert response["metadata"]["description"] == "unit-test"

    status, data = _http_get(server, "/api/flow")
    assert status == 200
    assert len(data["nodes"]) == len(flow["nodes"])


def test_execute_flow_returns_result(server: str):
    flow = _build_linear_flow()
    payload = {"flow": flow, "user_input": "canvas"}
    status, result = _http_post(server, "/api/execute", payload)
    assert status == 200
    assert result["result"] == "CANVAS"
    assert result["runtime"] >= 0


def test_execute_rejects_branching_flow(server: str):
    flow = _build_linear_flow()
    flow["edges"].append({"id": "branch", "source": "start", "target": "upper"})
    payload = {"flow": flow, "user_input": "canvas"}
    status, result = _http_post(server, "/api/execute", payload)
    assert status == 400
    assert "线" in result["detail"] or "linear" in result["detail"].lower()
