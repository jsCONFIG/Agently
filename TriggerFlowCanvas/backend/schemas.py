"""Pydantic schemas for TriggerFlow Canvas backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CanvasPosition(BaseModel):
    """Represents the position of a node on the canvas."""

    x: float = Field(default=0, ge=-10_000, le=10_000)
    y: float = Field(default=0, ge=-10_000, le=10_000)


class CanvasNode(BaseModel):
    """A node displayed on the TriggerFlow Canvas."""

    id: str
    name: str
    type: Literal["start", "echo", "uppercase", "llm", "output"]
    config: dict[str, Any] = Field(default_factory=dict)
    position: CanvasPosition = Field(default_factory=CanvasPosition)

    @field_validator("id", "name")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            msg = "Node id and name must not be empty"
            raise ValueError(msg)
        return value


class CanvasEdge(BaseModel):
    """Represents a directional connection between two nodes."""

    id: str
    source: str
    target: str

    @field_validator("id", "source", "target")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            msg = "Edge identifiers must not be empty"
            raise ValueError(msg)
        return value


class FlowMetadata(BaseModel):
    """Additional flow level metadata that can be displayed on the canvas."""

    description: str | None = None


class FlowDefinition(BaseModel):
    """A complete flow definition exchanged with the frontend."""

    nodes: list[CanvasNode]
    edges: list[CanvasEdge]
    metadata: FlowMetadata | None = None


class FlowExecutionRequest(BaseModel):
    """Payload used when the user executes a flow."""

    flow: FlowDefinition
    user_input: Any


class FlowExecutionResult(BaseModel):
    """Response body returned when a flow finishes execution."""

    result: Any
    runtime: float
