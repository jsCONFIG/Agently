from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterable, List


@dataclass
class ExecutionStep:
    id: str
    type: str
    label: str
    configuration: Dict[str, Any]


@dataclass
class ExecutionPlan:
    workflow_id: str
    steps: List[ExecutionStep]


class TriggerFlowConnector:
    """Converts workflow definitions into an executable plan and runs them sequentially."""

    async def compile(self, workflow: Dict[str, Any]) -> ExecutionPlan:
        steps: List[ExecutionStep] = []
        for node in workflow.get("nodes", []):
            steps.append(
                ExecutionStep(
                    id=node["id"],
                    type=node["type"],
                    label=node.get("label", node["type"]),
                    configuration=node.get("configuration", {}),
                )
            )
        return ExecutionPlan(workflow_id=workflow.get("id", ""), steps=steps)

    async def execute(self, plan: ExecutionPlan) -> AsyncIterator[str]:
        for index, step in enumerate(plan.steps, start=1):
            yield self._format_log(f"开始执行节点[{index}/{len(plan.steps)}]: {step.label}")
            await asyncio.sleep(0)  # allow event loop to switch context
            for message in self._simulate_step(step):
                yield message
        if not plan.steps:
            yield self._format_log("工作流中未包含可执行节点。")
        else:
            yield self._format_log("工作流执行完成。")

    def _simulate_step(self, step: ExecutionStep) -> Iterable[str]:
        timestamp = datetime.utcnow().isoformat()
        yield self._format_log(f"{step.label} @ {timestamp}: 使用配置 {step.configuration}")

    @staticmethod
    def _format_log(message: str) -> str:
        return f"[{datetime.utcnow().isoformat()}] {message}"


async def run_workflow(workflow: Dict[str, Any]) -> AsyncIterator[str]:
    connector = TriggerFlowConnector()
    plan = await connector.compile(workflow)
    async for log in connector.execute(plan):
        yield log
