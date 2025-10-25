from __future__ import annotations

import asyncio
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, AsyncIterator, Dict, Iterable, List, Mapping, Optional

from agently import TriggerFlow
from agently.types.trigger_flow import TriggerFlowEventData


_active_debugger: ContextVar["NodeDebugger | None"] = ContextVar(
    "triggerflow_canvas_active_debugger", default=None
)


@dataclass
class NodeSpec:
    id: str
    type: str
    label: str
    configuration: Dict[str, Any]
    is_terminal: bool = False


@dataclass
class ExecutionPlan:
    workflow_id: str
    flow: Optional[TriggerFlow]
    nodes: Dict[str, NodeSpec]
    start_node_id: Optional[str]
    initial_payload: Any


@dataclass
class DebugEvent:
    timestamp: datetime
    step_id: str
    step_type: str
    event: str
    payload: Dict[str, Any]


class NodeDebugger:
    """Collects timeline events for each node during execution."""

    def __init__(self) -> None:
        self._events: List[DebugEvent] = []

    def record(self, step: NodeSpec, event: str, payload: Optional[Mapping[str, Any]] = None) -> None:
        self._events.append(
            DebugEvent(
                timestamp=datetime.now(UTC),
                step_id=step.id,
                step_type=step.type,
                event=event,
                payload=dict(payload or {}),
            )
        )

    def timeline(self, step_id: str) -> List[DebugEvent]:
        return [event for event in self._events if event.step_id == step_id]

    @property
    def events(self) -> List[DebugEvent]:
        return list(self._events)

    def as_dict(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "step_id": event.step_id,
                "step_type": event.step_type,
                "event": event.event,
                "payload": event.payload,
            }
            for event in self._events
        ]


class TriggerFlowConnector:
    """Compile TriggerFlow Canvas definitions into runnable TriggerFlow pipelines."""

    async def compile(self, workflow: Dict[str, Any]) -> ExecutionPlan:
        nodes: Dict[str, NodeSpec] = {}
        for node in workflow.get("nodes", []):
            nodes[node["id"]] = NodeSpec(
                id=node["id"],
                type=node["type"],
                label=node.get("label", node["type"]),
                configuration=node.get("configuration", {}),
            )

        if not nodes:
            return ExecutionPlan(
                workflow_id=workflow.get("id", ""),
                flow=None,
                nodes={},
                start_node_id=None,
                initial_payload=None,
            )

        flow = TriggerFlow(name=workflow.get("name") or workflow.get("id") or "canvas-flow")
        adjacency, indegree = self._build_graph(nodes, workflow.get("edges", []))
        self._validate_graph(adjacency, indegree)

        start_candidates = [node_id for node_id, degree in indegree.items() if degree == 0]
        start_node = start_candidates[0]

        order = self._topological_order(adjacency, indegree, start_node)
        chunks: Dict[str, Any] = {}
        for node_id in order:
            spec = nodes[node_id]
            spec.is_terminal = not adjacency[node_id]
            handler = self._make_handler(spec)
            chunks[node_id] = flow.chunk(spec.id)(handler)

        process_map: Dict[str, Any] = {}
        process_map[start_node] = flow.to(chunks[start_node])

        for node_id in order:
            for successor in adjacency[node_id]:
                process = process_map[node_id]
                next_process = process.to(chunks[successor])
                process_map[successor] = next_process

        for node_id, process in process_map.items():
            if not adjacency[node_id]:
                process.end()

        initial_payload = self._initial_payload(nodes[start_node])
        return ExecutionPlan(
            workflow_id=workflow.get("id", ""),
            flow=flow,
            nodes=nodes,
            start_node_id=start_node,
            initial_payload=initial_payload,
        )

    async def execute(self, plan: ExecutionPlan, debugger: Optional[NodeDebugger] = None) -> AsyncIterator[str]:
        if not plan.nodes or plan.flow is None or plan.start_node_id is None:
            yield self._format_log("工作流中未包含可执行节点。")
            return

        token = _active_debugger.set(debugger)
        execution = plan.flow.create_execution()
        runner = asyncio.create_task(
            execution.async_start(plan.initial_payload, wait_for_result=False)
        )
        try:
            yield self._format_log(
                f"开始执行工作流: {plan.flow.name} (ID: {plan.workflow_id or plan.flow.name})"
            )
            async for item in execution.get_async_runtime_stream(timeout=None):
                yield self._format_log(self._stringify_stream_item(item))
            result = await execution.async_get_result(timeout=None)
            if result is not None:
                yield self._format_log(f"工作流执行结果: {self._summarize(result)}")
            yield self._format_log("工作流执行完成。")
        finally:
            _active_debugger.reset(token)
            await runner

    def _make_handler(self, spec: NodeSpec):
        async def _handler(event: TriggerFlowEventData) -> Any:
            debugger = _active_debugger.get()
            if debugger:
                debugger.record(spec, "start")

            await event.async_put_into_stream(
                f"节点 {spec.label} (类型 {spec.type}) 开始执行"
            )

            try:
                result = await self._execute_node(spec, event)
            except Exception as exc:  # pragma: no cover - defensive guard
                await event.async_put_into_stream(
                    f"节点 {spec.label} 执行失败: {exc}"
                )
                if debugger:
                    debugger.record(spec, "error", {"message": str(exc)})
                raise

            await event.async_put_into_stream(
                f"节点 {spec.label} 输出: {self._summarize(result)}"
            )
            if spec.is_terminal:
                await event.async_stop_stream()
            if debugger:
                debugger.record(spec, "completed", {"result": result})
            return result

        return _handler

    async def _execute_node(self, spec: NodeSpec, event: TriggerFlowEventData) -> Any:
        if spec.type == "trigger.http":
            return await self._execute_http_trigger(spec, event)
        if spec.type == "action.chat_completion":
            return await self._execute_chat_completion(spec, event)
        if spec.type == "action.http_request":
            return await self._execute_http_request(spec, event)
        return event.value

    async def _execute_http_trigger(self, spec: NodeSpec, event: TriggerFlowEventData) -> Dict[str, Any]:
        config = spec.configuration
        method = str(config.get("method", "GET")).upper()
        path = config.get("path", "/")
        payload = config.get("samplePayload") or event.value or {}
        timestamp = datetime.now(UTC).isoformat()
        request = {
            "method": method,
            "path": path,
            "timestamp": timestamp,
            "payload": payload,
        }
        await event.async_set_runtime_data(f"nodes.{spec.id}.request", request)
        return request

    async def _execute_chat_completion(
        self, spec: NodeSpec, event: TriggerFlowEventData
    ) -> Dict[str, Any]:
        config = spec.configuration
        model = config.get("model", "gpt-4o-mini")
        prompt = config.get("prompt", "")
        incoming = event.value or {}
        user_message = incoming.get("payload", {}).get("message") if isinstance(incoming, dict) else None
        if not user_message:
            user_message = incoming.get("reply") if isinstance(incoming, dict) else None
        if not user_message:
            user_message = prompt
        reply = f"{model} 回复: {user_message}" if user_message else f"{model} 生成了一个空回复"
        history_key = f"nodes.{spec.id}.history"
        history = event.get_runtime_data(history_key, []) or []
        history.append({"prompt": user_message, "reply": reply})
        await event.async_set_runtime_data(history_key, history)
        return {
            "model": model,
            "prompt": user_message,
            "reply": reply,
            "history": history,
        }

    async def _execute_http_request(
        self, spec: NodeSpec, event: TriggerFlowEventData
    ) -> Dict[str, Any]:
        config = spec.configuration
        method = str(config.get("method", "GET")).upper()
        url = config.get("url", "")
        payload = event.value or {}
        response = {
            "status": 200,
            "body": {
                "echo": payload,
                "note": "模拟请求已执行，未进行真实的网络调用。",
            },
            "headers": {"content-type": "application/json"},
        }
        await event.async_set_runtime_data(
            f"nodes.{spec.id}.response",
            {"method": method, "url": url, "response": response},
        )
        return {
            "method": method,
            "url": url,
            "payload": payload,
            "response": response,
        }

    def _build_graph(
        self, nodes: Dict[str, NodeSpec], edges: Iterable[Mapping[str, Any]]
    ) -> tuple[Dict[str, List[str]], Dict[str, int]]:
        adjacency: Dict[str, List[str]] = {node_id: [] for node_id in nodes}
        indegree: Dict[str, int] = {node_id: 0 for node_id in nodes}

        for edge in edges:
            source = edge.get("from", {}).get("nodeId")
            target = edge.get("to", {}).get("nodeId")
            if source not in nodes or target not in nodes:
                raise ValueError("连线引用了不存在的节点，请检查流程配置。")
            adjacency[source].append(target)
            indegree[target] += 1

        return adjacency, indegree

    def _validate_graph(self, adjacency: Dict[str, List[str]], indegree: Dict[str, int]) -> None:
        for node_id, outgoing in adjacency.items():
            if len(outgoing) > 1:
                raise ValueError(
                    f"节点 {node_id} 存在多个输出分支，目前的执行器仅支持单一路径。"
                )
        for node_id, degree in indegree.items():
            if degree > 1:
                raise ValueError(
                    f"节点 {node_id} 存在多个输入分支，目前的执行器仅支持单一路径。"
                )
        start_nodes = [node_id for node_id, degree in indegree.items() if degree == 0]
        if not start_nodes:
            raise ValueError("流程缺少入口节点，请至少保留一个触发器。")
        if len(start_nodes) > 1:
            raise ValueError("检测到多个入口节点，目前仅支持单一入口的工作流。")

    def _topological_order(
        self,
        adjacency: Dict[str, List[str]],
        indegree: Dict[str, int],
        start_node: str,
    ) -> List[str]:
        indegree_copy = indegree.copy()
        queue: deque[str] = deque([start_node])
        order: List[str] = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for successor in adjacency[node_id]:
                indegree_copy[successor] -= 1
                if indegree_copy[successor] == 0:
                    queue.append(successor)

        if len(order) != len(adjacency):
            raise ValueError("流程存在闭环或与主干断开的节点，无法编译。")
        return order

    def _initial_payload(self, spec: NodeSpec) -> Any:
        if spec.type == "trigger.http":
            config = spec.configuration
            return {
                "method": str(config.get("method", "GET")).upper(),
                "path": config.get("path", "/"),
                "payload": config.get("samplePayload", {}),
            }
        return {}

    @staticmethod
    def _stringify_stream_item(item: Any) -> str:
        if isinstance(item, str):
            return item
        return TriggerFlowConnector._summarize(item)

    @staticmethod
    def _summarize(value: Any) -> str:
        text = str(value)
        return text if len(text) <= 160 else text[:157] + "..."

    @staticmethod
    def _format_log(message: str) -> str:
        return f"[{datetime.now(UTC).isoformat()}] {message}"


async def run_workflow(workflow: Dict[str, Any], debugger: Optional[NodeDebugger] = None) -> AsyncIterator[str]:
    connector = TriggerFlowConnector()
    plan = await connector.compile(workflow)
    async for log in connector.execute(plan, debugger=debugger):
        yield log
