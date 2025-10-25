from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, AsyncIterator, Dict, Iterable, List, Mapping, Optional


@dataclass
class ExecutionStep:
    id: str
    type: str
    label: str
    configuration: Dict[str, Any]


@dataclass
class DebugOverride:
    """Per-node debugging instructions injected during simulation."""

    outputs: List[str] = field(default_factory=list)
    input_payload: Any | None = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DebugOverride":
        outputs: Any = data.get("outputs") or data.get("output") or data.get("responses") or []
        if isinstance(outputs, (str, bytes)):
            outputs = [str(outputs)]
        elif isinstance(outputs, Mapping):
            outputs = [str(item) for item in outputs.values()]
        elif isinstance(outputs, Iterable):
            outputs = [str(item) for item in outputs]
        else:
            outputs = []
        notes = data.get("notes") or data.get("note") or data.get("description")
        input_payload = data.get("input") or data.get("payload")
        reserved_keys = {"outputs", "output", "responses", "notes", "note", "description", "input", "payload"}
        metadata = {key: value for key, value in data.items() if key not in reserved_keys}
        return cls(outputs=list(outputs), input_payload=input_payload, notes=notes, metadata=metadata)


@dataclass
class ExecutionPlan:
    workflow_id: str
    steps: List[ExecutionStep]
    debug_overrides: Dict[str, DebugOverride] = field(default_factory=dict)


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

    def record(self, step: ExecutionStep, event: str, payload: Optional[Mapping[str, Any]] = None) -> None:
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
    """Converts workflow definitions into an executable plan and runs them sequentially."""

    async def compile(self, workflow: Dict[str, Any]) -> ExecutionPlan:
        steps: List[ExecutionStep] = []
        for node in workflow.get("nodes", []):
            step = ExecutionStep(
                id=node["id"],
                type=node["type"],
                label=node.get("label", node["type"]),
                configuration=node.get("configuration", {}),
            )
            steps.append(step)
        debug_overrides = self._resolve_debug_overrides(workflow, steps)
        return ExecutionPlan(workflow_id=workflow.get("id", ""), steps=steps, debug_overrides=debug_overrides)

    async def execute(self, plan: ExecutionPlan, debugger: Optional[NodeDebugger] = None) -> AsyncIterator[str]:
        if not plan.steps:
            yield self._format_log("工作流中未包含可执行节点。")
            return

        for index, step in enumerate(plan.steps, start=1):
            header = self._format_log(f"开始执行节点[{index}/{len(plan.steps)}]: {step.label}")
            if debugger:
                debugger.record(step, "start", {"index": index})
            yield header
            await asyncio.sleep(0)  # allow event loop to switch context
            override = plan.debug_overrides.get(step.id)
            for message in self._simulate_step(step, override, debugger):
                yield message
            if debugger:
                debugger.record(step, "completed", {"index": index})
        yield self._format_log("工作流执行完成。")

    def _resolve_debug_overrides(
        self, workflow: Dict[str, Any], steps: List[ExecutionStep]
    ) -> Dict[str, DebugOverride]:
        debug_section = workflow.get("debug")
        if not isinstance(debug_section, Mapping):
            return {}
        node_overrides = debug_section.get("nodes", {})
        if not isinstance(node_overrides, Mapping):
            return {}

        resolved: Dict[str, DebugOverride] = {}
        for step in steps:
            override_config = self._match_override(step, node_overrides)
            if override_config is not None:
                resolved[step.id] = DebugOverride.from_mapping(override_config)
        return resolved

    @staticmethod
    def _match_override(step: ExecutionStep, overrides: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        for key in (step.id, step.label, step.type):
            if key in overrides:
                candidate = overrides[key]
                if isinstance(candidate, Mapping):
                    return candidate
        return None

    def _simulate_step(
        self,
        step: ExecutionStep,
        override: Optional[DebugOverride],
        debugger: Optional[NodeDebugger],
    ) -> Iterable[str]:
        yield self._format_log(
            f"节点 {step.label} 类型 {step.type} 使用配置 {step.configuration}"
        )

        if override:
            if debugger:
                debugger.record(step, "override", {
                    "notes": override.notes,
                    "metadata": override.metadata,
                    "has_outputs": bool(override.outputs),
                })
            if override.notes:
                yield self._format_log(f"调试备注: {override.notes}")
            if override.input_payload is not None:
                yield self._format_log(f"模拟输入: {override.input_payload}")
            if override.outputs:
                for idx, output in enumerate(override.outputs, start=1):
                    yield self._format_log(f"调试输出[{idx}]: {output}")
            else:
                yield self._format_log("调试配置未提供输出，使用默认占位响应。")
            if override.metadata:
                yield self._format_log(f"调试元数据: {override.metadata}")
        else:
            yield self._format_log("未开启调试覆盖，返回默认占位响应。")

        timestamp = datetime.now(UTC).isoformat()
        yield self._format_log(f"{step.label} @ {timestamp}: 执行完成。")

    @staticmethod
    def _format_log(message: str) -> str:
        return f"[{datetime.now(UTC).isoformat()}] {message}"


async def run_workflow(workflow: Dict[str, Any], debugger: Optional[NodeDebugger] = None) -> AsyncIterator[str]:
    connector = TriggerFlowConnector()
    plan = await connector.compile(workflow)
    async for log in connector.execute(plan, debugger=debugger):
        yield log
