from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class ToolStatus:
    name: str
    available: bool
    version: Optional[str] = None
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "name": self.name,
            "available": "yes" if self.available else "no",
            "version": self.version,
            "detail": self.detail,
        }


@dataclass
class ToolCheck:
    name: str
    command: Iterable[str]
    required: bool = True
    friendly_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        return self.friendly_name or self.name


TOOLS: List[ToolCheck] = [
    ToolCheck(name="poetry", command=["poetry", "--version"]),
    ToolCheck(name="node", command=["node", "--version"], friendly_name="Node.js"),
    ToolCheck(name="npm", command=["npm", "--version"], friendly_name="npm"),
    ToolCheck(name="docker", command=["docker", "--version"], required=False, friendly_name="Docker"),
]


def check_tool(tool: ToolCheck) -> ToolStatus:
    executable = shutil.which(tool.name)
    if not executable:
        detail = "未在 PATH 中找到，可根据指南安装或配置镜像源。"
        if not tool.required:
            detail = f"可选组件缺失：{detail}"
        return ToolStatus(name=tool.display_name, available=False, detail=detail)

    try:
        result = subprocess.run(tool.command, capture_output=True, text=True, check=False)
    except Exception as exc:  # pragma: no cover - defensive guard
        return ToolStatus(name=tool.display_name, available=True, detail=f"无法读取版本: {exc}")

    output = (result.stdout or result.stderr or "").strip()
    version = output.splitlines()[0] if output else None
    return ToolStatus(name=tool.display_name, available=True, version=version)


def check_environment() -> List[ToolStatus]:
    """Check whether the recommended local development tools are available."""
    return [check_tool(tool) for tool in TOOLS]


def format_report(statuses: List[ToolStatus]) -> str:
    lines = ["TriggerFlow Canvas 环境预检结果:"]
    for status in statuses:
        icon = "✅" if status.available else ("⚠️" if status.detail and "可选" in status.detail else "❌")
        version_text = f" - {status.version}" if status.version else ""
        detail_text = f" ({status.detail})" if status.detail else ""
        lines.append(f"- {icon} {status.name}{version_text}{detail_text}")
    return "\n".join(lines)


def main() -> None:
    statuses = check_environment()
    print(format_report(statuses))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
