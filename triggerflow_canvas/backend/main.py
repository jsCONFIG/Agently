from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .database import init_db, session_scope
from .models import WorkflowRecord
from .repositories import RunRepository, WorkflowRepository
from .run_manager import RunManager
from .schemas import ExecuteResponse, WorkflowPayload, WorkflowResponse
from ..connector import TriggerFlowConnector


connector = TriggerFlowConnector()
run_manager = RunManager(connector)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="TriggerFlow Canvas API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def get_workflow_repo() -> AsyncIterator[WorkflowRepository]:
    async with session_scope() as session:
        yield WorkflowRepository(session)


async def get_run_repo() -> AsyncIterator[RunRepository]:
    async with session_scope() as session:
        yield RunRepository(session)


def _to_response(record: WorkflowRecord) -> WorkflowResponse:
    definition: Dict[str, object] = record.definition or {}
    return WorkflowResponse(
        id=record.id,
        name=record.name,
        description=record.description,
        nodes=definition.get("nodes", []),
        edges=definition.get("edges", []),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@app.get("/api/workflows", response_model=list[WorkflowResponse])
async def list_workflows(repo: WorkflowRepository = Depends(get_workflow_repo)) -> list[WorkflowResponse]:
    records = await repo.list_workflows()
    return [_to_response(record) for record in records]


@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(
    payload: WorkflowPayload, repo: WorkflowRepository = Depends(get_workflow_repo)
) -> WorkflowResponse:
    record = WorkflowRecord(
        id=payload.id or None,
        name=payload.name,
        description=payload.description,
        definition=payload.model_dump(by_alias=True, exclude={"id", "name", "description"}),
    )
    saved = await repo.save(record)
    return _to_response(saved)


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str, repo: WorkflowRepository = Depends(get_workflow_repo)
) -> WorkflowResponse:
    record = await repo.get(workflow_id)
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(record)


@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowPayload,
    repo: WorkflowRepository = Depends(get_workflow_repo),
) -> WorkflowResponse:
    record = await repo.get(workflow_id)
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    record.name = payload.name
    record.description = payload.description
    record.definition = payload.model_dump(by_alias=True, exclude={"id", "name", "description"})
    saved = await repo.save(record)
    return _to_response(saved)


@app.delete("/api/workflows/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str, repo: WorkflowRepository = Depends(get_workflow_repo)
) -> None:
    await repo.delete(workflow_id)


@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecuteResponse)
async def execute_workflow(
    workflow_id: str,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo),
    run_repo: RunRepository = Depends(get_run_repo),
) -> ExecuteResponse:
    record = await workflow_repo.get(workflow_id)
    if not record:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow = {"id": record.id, "name": record.name, "description": record.description, **record.definition}
    run_id = await run_manager.start(workflow, run_repo)
    return ExecuteResponse(runId=run_id)


def _escape_message(message: str) -> str:
    return message.replace("\\", "\\\\").replace("\"", "\\\"")


async def _log_event_stream(run_id: str, run_repo: RunRepository) -> AsyncIterator[bytes]:
    async for message in run_manager.stream(run_id, run_repo):
        payload = f"data: {{\"message\": \"{_escape_message(message)}\"}}\n\n"
        yield payload.encode("utf-8")
    yield b"event: end\ndata: {}\n\n"


@app.get("/api/runs/{run_id}/logs")
async def stream_logs(run_id: str, run_repo: RunRepository = Depends(get_run_repo)) -> StreamingResponse:
    generator = _log_event_stream(run_id, run_repo)
    return StreamingResponse(generator, media_type="text/event-stream")
