from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import RunRecord, WorkflowRecord


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_workflows(self) -> List[WorkflowRecord]:
        result = await self._session.exec(select(WorkflowRecord))
        return result.all()

    async def get(self, workflow_id: str) -> Optional[WorkflowRecord]:
        return await self._session.get(WorkflowRecord, workflow_id)

    async def save(self, record: WorkflowRecord) -> WorkflowRecord:
        record.updated_at = datetime.utcnow()
        if record.id is None:
            record.id = str(uuid4())
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def delete(self, workflow_id: str) -> None:
        workflow = await self.get(workflow_id)
        if workflow is None:
            return
        await self._session.delete(workflow)
        await self._session.commit()


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workflow_id: str) -> RunRecord:
        record = RunRecord(id=str(uuid4()), workflow_id=workflow_id, status="running")
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def append_log(self, run_id: str, message: str) -> RunRecord:
        run = await self._session.get(RunRecord, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        run.logs.append(message)
        run.updated_at = datetime.utcnow()
        self._session.add(run)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def update_status(self, run_id: str, status: str) -> Optional[RunRecord]:
        run = await self._session.get(RunRecord, run_id)
        if not run:
            return None
        run.status = status
        run.updated_at = datetime.utcnow()
        self._session.add(run)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def get(self, run_id: str) -> Optional[RunRecord]:
        return await self._session.get(RunRecord, run_id)
