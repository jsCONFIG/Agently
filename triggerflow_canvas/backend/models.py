from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Column, Field, SQLModel
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict, MutableList


class WorkflowRecord(SQLModel, table=True):
    __tablename__ = "workflows"

    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    definition: Dict[str, Any] = Field(sa_column=Column(MutableDict.as_mutable(JSON), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RunRecord(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    id: Optional[str] = Field(default=None, primary_key=True)
    workflow_id: str = Field(foreign_key="workflows.id")
    status: str = Field(default="pending")
    logs: List[str] = Field(
        default_factory=list,
        sa_column=Column(MutableList.as_mutable(JSON), nullable=False),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
