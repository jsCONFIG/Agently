from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class NodePort(BaseModel):
    id: str
    label: str
    direction: str


class CanvasNode(BaseModel):
    id: str
    type: str
    label: str
    x: float
    y: float
    configuration: Dict[str, object]
    ports: List[NodePort] = Field(default_factory=list)


class WorkflowEdge(BaseModel):
    id: str
    from_: Dict[str, str] = Field(alias="from")
    to: Dict[str, str]

    class Config:
        populate_by_name = True


class WorkflowPayload(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    nodes: List[CanvasNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)


class WorkflowResponse(WorkflowPayload):
    created_at: datetime
    updated_at: datetime


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    logs: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ExecuteResponse(BaseModel):
    run_id: str = Field(alias="runId")

    class Config:
        populate_by_name = True
