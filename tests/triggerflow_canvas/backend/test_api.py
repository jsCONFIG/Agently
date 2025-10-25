from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
import sys
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlalchemy.pool import StaticPool
from sqlmodel.ext.asyncio.session import AsyncSession

from triggerflow_canvas.backend import database, main
from triggerflow_canvas.backend.run_manager import RunManager
from triggerflow_canvas.connector import TriggerFlowConnector


@pytest_asyncio.fixture()
async def async_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def init_db_override() -> None:
        async with test_engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def session_scope_override() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(test_engine) as session:
            yield session

    monkeypatch.setattr(database, "engine", test_engine, raising=False)
    monkeypatch.setattr(database, "init_db", init_db_override)
    monkeypatch.setattr(database, "session_scope", session_scope_override)
    monkeypatch.setattr(main, "init_db", init_db_override)
    monkeypatch.setattr(main, "session_scope", session_scope_override)
    monkeypatch.setattr(main, "run_manager", RunManager(TriggerFlowConnector()))

    await init_db_override()

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio()
async def test_workflow_crud_and_execution(async_client: AsyncClient) -> None:
    create_payload = {
        "name": "示例流程",
        "description": "用于自动化测试的流程",
        "nodes": [
            {
                "id": "node-1",
                "type": "action.chat_completion",
                "label": "对话",
                "x": 80,
                "y": 120,
                "configuration": {"prompt": "你好", "model": "gpt-4o-mini"},
                "ports": [
                    {"id": "in", "label": "输入", "direction": "input"},
                    {"id": "out", "label": "输出", "direction": "output"}
                ]
            }
        ],
        "edges": []
    }

    create_response = await async_client.post("/api/workflows", json=create_payload)
    assert create_response.status_code == 200
    workflow = create_response.json()
    workflow_id = workflow["id"]
    assert workflow["nodes"][0]["configuration"]["prompt"] == "你好"

    list_response = await async_client.get("/api/workflows")
    assert list_response.status_code == 200
    workflows = list_response.json()
    assert len(workflows) == 1
    assert workflows[0]["name"] == "示例流程"

    update_payload = {**create_payload, "name": "更新后的流程", "description": "更新描述"}
    update_response = await async_client.put(f"/api/workflows/{workflow_id}", json=update_payload)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "更新后的流程"
    assert updated["description"] == "更新描述"

    execute_response = await async_client.post(f"/api/workflows/{workflow_id}/execute")
    assert execute_response.status_code == 200
    run_id = execute_response.json()["runId"]

    await main.run_manager.wait_for(run_id)

    messages: list[str] = []
    async with async_client.stream("GET", f"/api/runs/{run_id}/logs") as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if not line:
                continue
            if line.startswith("data: "):
                payload = json.loads(line.removeprefix("data: "))
                messages.append(payload["message"])
            if line.startswith("event: end"):
                break

    assert any("开始执行节点" in message for message in messages)
    assert any("工作流执行完成" in message for message in messages)

    delete_response = await async_client.delete(f"/api/workflows/{workflow_id}")
    assert delete_response.status_code == 204

    list_after_delete = await async_client.get("/api/workflows")
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []
