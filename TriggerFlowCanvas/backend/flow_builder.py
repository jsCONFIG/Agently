"""Utilities that convert canvas definitions to executable TriggerFlow instances."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

from agently import TriggerFlow, TriggerFlowEventData

from .schemas import CanvasNode, FlowDefinition

HandlerFactory = Callable[[CanvasNode], Callable[[TriggerFlowEventData], Any]]


class FlowBuildError(RuntimeError):
    """Raised when the canvas definition cannot be translated into a flow."""


class FlowBuilder:
    """Builds TriggerFlow instances from canvas definitions."""

    def __init__(self, registry: Dict[str, HandlerFactory]):
        self._registry = registry

    def build_flow(self, definition: FlowDefinition) -> TriggerFlow:
        """Create a TriggerFlow from the provided definition."""
        if not definition.nodes:
            msg = "Flow must contain at least one node"
            raise FlowBuildError(msg)

        nodes = {node.id: node for node in definition.nodes}
        adjacency: Dict[str, list[str]] = {node.id: [] for node in definition.nodes}
        reverse: Dict[str, list[str]] = {node.id: [] for node in definition.nodes}
        for edge in definition.edges:
            if edge.source not in nodes or edge.target not in nodes:
                msg = f"Edge {edge.id} references unknown nodes"
                raise FlowBuildError(msg)
            adjacency[edge.source].append(edge.target)
            reverse[edge.target].append(edge.source)

        start_nodes = [node for node in definition.nodes if node.type == "start"]
        if len(start_nodes) != 1:
            msg = "Flow must contain exactly one start node"
            raise FlowBuildError(msg)
        start_node = start_nodes[0]

        if adjacency[start_node.id] == []:
            msg = "Start node must connect to at least one action node"
            raise FlowBuildError(msg)
        if len(adjacency[start_node.id]) > 1:
            msg = "TriggerFlow Canvas currently supports a single linear path from the start node"
            raise FlowBuildError(msg)

        for node in definition.nodes:
            if node.type != "start" and reverse[node.id] == []:
                msg = f"Node '{node.name}' is unreachable from start"
                raise FlowBuildError(msg)
            if len(adjacency[node.id]) > 1:
                msg = (
                    "TriggerFlow Canvas currently supports sequential flows only;"
                    f" node '{node.name}' has multiple outgoing edges"
                )
                raise FlowBuildError(msg)

        flow = TriggerFlow()
        handler_cache: Dict[str, Callable[[TriggerFlowEventData], Any]] = {}

        def resolve_handler(node_id: str) -> Callable[[TriggerFlowEventData], Any]:
            if node_id in handler_cache:
                return handler_cache[node_id]
            node = nodes[node_id]
            if node.type == "start":
                msg = "Start node cannot be executed directly"
                raise FlowBuildError(msg)
            if node.type not in self._registry:
                msg = f"Unsupported node type '{node.type}'"
                raise FlowBuildError(msg)
            handler = self._registry[node.type](node)
            handler_cache[node_id] = handler
            return handler

        current_process = flow
        current_node_id = adjacency[start_node.id][0]
        visited: set[str] = set()
        while current_node_id:
            if current_node_id in visited:
                msg = "Detected a cycle in the flow definition"
                raise FlowBuildError(msg)
            visited.add(current_node_id)
            handler = resolve_handler(current_node_id)
            current_process = current_process.to(handler)
            next_nodes = adjacency[current_node_id]
            current_node_id = next_nodes[0] if next_nodes else ""

        current_process.end()
        return flow


def create_builtin_registry() -> Dict[str, HandlerFactory]:
    """Return the default set of handler factories used by the canvas service."""

    def make_echo(node: CanvasNode) -> Callable[[TriggerFlowEventData], Any]:
        template = node.config.get("template", "{value}")

        async def echo(data: TriggerFlowEventData) -> str:
            value = data.value
            return str(template).format(value=value, name=node.name)

        return echo

    def make_uppercase(node: CanvasNode) -> Callable[[TriggerFlowEventData], Any]:
        async def uppercase(data: TriggerFlowEventData) -> str:
            return str(data.value).upper()

        return uppercase

    def make_llm(node: CanvasNode) -> Callable[[TriggerFlowEventData], Any]:
        prompt = node.config.get("prompt", "Respond to: {value}")
        suffix = node.config.get("suffix", " (simulated)")

        async def llm(data: TriggerFlowEventData) -> str:
            rendered_prompt = str(prompt).format(value=data.value, name=node.name)
            await data.async_append_runtime_data(
                "llm_history",
                {
                    "timestamp": time.time(),
                    "prompt": rendered_prompt,
                },
            )
            return f"{rendered_prompt}{suffix}"

        return llm

    def make_output(node: CanvasNode) -> Callable[[TriggerFlowEventData], Any]:
        async def output(data: TriggerFlowEventData) -> Any:
            label = node.config.get("label")
            if label:
                await data.async_append_runtime_data(
                    "outputs",
                    {"label": label, "value": data.value},
                )
            return data.value

        return output

    return {
        "echo": make_echo,
        "uppercase": make_uppercase,
        "llm": make_llm,
        "output": make_output,
    }
