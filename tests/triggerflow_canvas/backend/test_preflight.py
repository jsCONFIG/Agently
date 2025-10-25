from __future__ import annotations

from typing import List

from triggerflow_canvas.connector import check_environment, format_report
from triggerflow_canvas.connector.preflight import TOOLS, ToolCheck, ToolStatus, check_tool


def test_check_tool_when_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    tool = ToolCheck(name="poetry", command=["poetry", "--version"])
    status = check_tool(tool)
    assert not status.available
    assert "未在 PATH" in status.detail


def test_check_tool_when_available(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/tool")

    class Result:
        stdout = "poetry version 1.7.0"
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Result())
    tool = ToolCheck(name="poetry", command=["poetry", "--version"])
    status = check_tool(tool)
    assert status.available
    assert status.version == "poetry version 1.7.0"


def test_check_environment_order(monkeypatch):
    statuses: List[ToolStatus] = [
        ToolStatus(name=tool.display_name, available=False) for tool in TOOLS
    ]
    monkeypatch.setattr(
        "triggerflow_canvas.connector.preflight.check_tool",
        lambda tool: statuses.pop(0),
    )
    results = check_environment()
    assert len(results) == len(TOOLS)


def test_format_report_with_optional_tool():
    statuses = [
        ToolStatus(name="poetry", available=True, version="poetry 1.7.0"),
        ToolStatus(name="Docker", available=False, detail="可选组件缺失：test"),
    ]
    report = format_report(statuses)
    assert "poetry 1.7.0" in report
    assert "⚠️" in report
