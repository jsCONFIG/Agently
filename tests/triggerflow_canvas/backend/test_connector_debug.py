import asyncio

from triggerflow_canvas.connector.engine import NodeDebugger, TriggerFlowConnector, run_workflow


def _collect_logs(workflow, debugger=None):
    async def _inner():
        logs = []
        async for log in run_workflow(workflow, debugger=debugger):
            logs.append(log)
        return logs

    return asyncio.run(_inner())


def test_debug_override_emits_simulated_output():
    workflow = {
        "id": "wf-1",
        "nodes": [
            {
                "id": "node-1",
                "type": "llm",
                "label": "LLM 回复",
                "configuration": {"model": "gpt-test", "prompt": "hello"},
            }
        ],
        "debug": {
            "nodes": {
                "node-1": {
                    "outputs": ["你好，我是调试响应"],
                    "input": {"messages": ["hi"]},
                    "notes": "使用伪造的响应验证链路",
                }
            }
        },
    }

    debugger = NodeDebugger()
    logs = []
    logs = _collect_logs(workflow, debugger)

    assert any("调试输出[1]: 你好，我是调试响应" in message for message in logs)
    override_events = [event for event in debugger.timeline("node-1") if event.event == "override"]
    assert override_events, "override event should be recorded"
    assert override_events[0].payload["has_outputs"] is True


def test_execute_without_nodes_reports_message():
    connector = TriggerFlowConnector()

    async def _inner():
        plan = await connector.compile({"id": "empty", "nodes": []})
        return [log async for log in connector.execute(plan)]

    logs = asyncio.run(_inner())
    assert logs and "未包含可执行节点" in logs[0]
