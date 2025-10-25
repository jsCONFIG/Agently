"""Utilities to compile and execute TriggerFlow workflows."""

from typing import Sequence

from .engine import (
    DebugEvent,
    ExecutionPlan,
    NodeDebugger,
    NodeSpec,
    TriggerFlowConnector,
    run_workflow,
)

__all__ = [
    "DebugEvent",
    "ExecutionPlan",
    "NodeDebugger",
    "NodeSpec",
    "TriggerFlowConnector",
    "check_environment",
    "format_report",
    "run_workflow",
]


def check_environment():
    """Run the TriggerFlow Canvas preflight checks."""
    from .preflight import check_environment as _check_environment

    return _check_environment()


def format_report(statuses: Sequence) -> str:
    """Format preflight results into a human-readable report."""
    from .preflight import format_report as _format_report

    return _format_report(statuses)
