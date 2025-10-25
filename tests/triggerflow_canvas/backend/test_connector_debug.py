import asyncio

import pytest

from triggerflow_canvas.connector.engine import NodeDebugger, TriggerFlowConnector, run_workflow


def _collect_logs(workflow, debugger=None):
    async def _inner():
        logs = []
        async for log in run_workflow(workflow, debugger=debugger):
            logs.append(log)
        return logs

    return asyncio.run(_inner())


def test_debugger_records_real_execution_events():
    workflow = {
        "id": "wf-1",
        "name": "调试流程",
        "nodes": [
            {
                "id": "node-trigger",
                "type": "trigger.http",
                "label": "HTTP 入口",
                "configuration": {
                    "method": "POST",
                    "path": "/demo",
                    "samplePayload": {"message": "hello"},
                },
            },
            {
                "id": "node-chat",
                "type": "action.chat_completion",
                "label": "对话节点",
                "configuration": {"model": "gpt-test", "prompt": "hi"},
            },
        ],
        "edges": [
            {
                "id": "edge-1",
                "from": {"nodeId": "node-trigger", "portId": "out"},
                "to": {"nodeId": "node-chat", "portId": "in"},
            }
        ],
    }

    debugger = NodeDebugger()
    logs = _collect_logs(workflow, debugger)

    assert any("开始执行工作流" in entry for entry in logs)
    assert any("节点 HTTP 入口" in entry for entry in logs)
    assert any("工作流执行完成" in entry for entry in logs)

    trigger_events = debugger.timeline("node-trigger")
    chat_events = debugger.timeline("node-chat")

    assert any(event.event == "start" for event in trigger_events)
    assert any(event.event == "completed" for event in trigger_events)
    assert any(event.event == "start" for event in chat_events)
    assert any(event.event == "completed" for event in chat_events)


def test_execute_without_nodes_reports_message():
    connector = TriggerFlowConnector()

    async def _inner():
        plan = await connector.compile({"id": "empty", "nodes": []})
        return [log async for log in connector.execute(plan)]

    logs = asyncio.run(_inner())
    assert logs and "未包含可执行节点" in logs[0]


@pytest.mark.asyncio()
async def test_compile_rejects_multiple_branches() -> None:
    connector = TriggerFlowConnector()
    workflow = {
        "id": "wf-invalid",
        "nodes": [
            {"id": "n1", "type": "trigger.http", "label": "入口", "configuration": {}},
            {"id": "n2", "type": "action.chat_completion", "label": "A", "configuration": {}},
            {"id": "n3", "type": "action.http_request", "label": "B", "configuration": {}},
        ],
        "edges": [
            {"id": "e1", "from": {"nodeId": "n1", "portId": "out"}, "to": {"nodeId": "n2", "portId": "in"}},
            {"id": "e2", "from": {"nodeId": "n1", "portId": "out"}, "to": {"nodeId": "n3", "portId": "in"}},
        ],
    }

    with pytest.raises(ValueError):
        await connector.compile(workflow)
