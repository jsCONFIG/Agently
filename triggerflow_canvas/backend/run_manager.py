from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional

from .repositories import RunRepository
from ..connector import TriggerFlowConnector


@dataclass
class RunHandle:
    queue: "asyncio.Queue[Optional[str]]"
    task: asyncio.Task[Any]


class RunManager:
    def __init__(self, connector: TriggerFlowConnector) -> None:
        self._connector = connector
        self._runs: Dict[str, RunHandle] = {}
        self._lock = asyncio.Lock()

    async def start(self, workflow: Dict[str, Any], run_repo: RunRepository) -> str:
        async with self._lock:
            run_record = await run_repo.create(workflow_id=workflow["id"])
            queue: "asyncio.Queue[Optional[str]]" = asyncio.Queue()
            task = asyncio.create_task(self._execute(run_record.id, workflow, run_repo, queue))
            self._runs[run_record.id] = RunHandle(queue=queue, task=task)
            task.add_done_callback(lambda _: asyncio.create_task(self._cleanup(run_record.id)))
            return run_record.id

    async def _execute(
        self,
        run_id: str,
        workflow: Dict[str, Any],
        run_repo: RunRepository,
        queue: "asyncio.Queue[Optional[str]]",
    ) -> None:
        try:
            plan = await self._connector.compile(workflow)
            async for message in self._connector.execute(plan):
                await run_repo.append_log(run_id, message)
                await queue.put(message)
            await run_repo.update_status(run_id, "completed")
        except Exception as error:  # pragma: no cover - defensive guard
            failure_message = f"执行失败: {error}"
            await run_repo.append_log(run_id, failure_message)
            await run_repo.update_status(run_id, "failed")
            await queue.put(failure_message)
        finally:
            await queue.put(None)

    async def _cleanup(self, run_id: str) -> None:
        async with self._lock:
            handle = self._runs.pop(run_id, None)
            if handle and not handle.task.cancelled() and handle.task.done():
                _ = handle.task.exception()

    async def stream(self, run_id: str, run_repo: RunRepository) -> AsyncIterator[str]:
        run = await run_repo.get(run_id)
        existing_logs = run.logs if run else []
        for message in existing_logs:
            yield message

        handle = self._runs.get(run_id)
        if not handle:
            return

        skipped = 0
        while True:
            message = await handle.queue.get()
            if message is None:
                break
            if skipped < len(existing_logs):
                skipped += 1
                continue
            yield message

    async def wait_for(self, run_id: str) -> None:
        handle = self._runs.get(run_id)
        if handle:
            await handle.task
