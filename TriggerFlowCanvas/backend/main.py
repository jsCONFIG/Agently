"""HTTP server for TriggerFlow Canvas built on the standard library."""

from __future__ import annotations

import json
import os
import time
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingTCPServer
from typing import Any, Callable

from .flow_builder import FlowBuilder, FlowBuildError, create_builtin_registry
from .schemas import FlowDefinition, FlowExecutionRequest, FlowExecutionResult
from .storage import FlowStorage

BASE_DIR = Path(__file__).resolve().parent.parent
_dist_dir = BASE_DIR / "frontend" / "dist"
FRONTEND_DIR = _dist_dir if _dist_dir.exists() else BASE_DIR / "frontend"
DEFAULT_FLOW_PATH = BASE_DIR / "data" / "default_flow.json"
STORAGE_PATH = BASE_DIR / "data" / "flow.json"


class CanvasService:
    """Encapsulates business logic for reading, writing and executing flows."""

    def __init__(
        self,
        *,
        storage: FlowStorage | None = None,
        builder: FlowBuilder | None = None,
    ):
        self.storage = storage or FlowStorage(STORAGE_PATH)
        self.builder = builder or FlowBuilder(create_builtin_registry())
        self._ensure_default_flow()

    def _ensure_default_flow(self) -> None:
        if self.storage.load() is None and DEFAULT_FLOW_PATH.exists():
            default_definition = FlowDefinition.model_validate_json(
                DEFAULT_FLOW_PATH.read_text(encoding="utf-8")
            )
            self.storage.save(default_definition)

    def load_flow(self) -> FlowDefinition:
        flow = self.storage.load()
        if flow is not None:
            return flow
        if DEFAULT_FLOW_PATH.exists():
            return FlowDefinition.model_validate_json(DEFAULT_FLOW_PATH.read_text(encoding="utf-8"))
        raise FileNotFoundError("Flow definition not found")

    def save_flow(self, definition: FlowDefinition) -> FlowDefinition:
        self.storage.save(definition)
        return definition

    def execute(self, request: FlowExecutionRequest) -> FlowExecutionResult:
        flow = self.builder.build_flow(request.flow)
        execution = flow.create_execution()
        started = time.perf_counter()
        result = execution.start(request.user_input)
        runtime = time.perf_counter() - started
        return FlowExecutionResult(result=result, runtime=runtime)


class CanvasHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler that exposes the TriggerFlow Canvas REST API."""

    def __init__(self, *args: Any, service: CanvasService, **kwargs: Any) -> None:
        self.service = service
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/api/flow":
            self._handle_get_flow()
        else:
            super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/api/flow":
            self._handle_post_flow()
        elif self.path == "/api/execute":
            self._handle_execute()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - signature inherited
        if os.environ.get("CANVAS_DEBUG") == "1":
            super().log_message(format, *args)

    # Handlers -------------------------------------------------------------------------------------------------
    def _handle_get_flow(self) -> None:
        try:
            definition = self.service.load_flow()
            self._send_json(definition.model_dump(mode="json"))
        except FileNotFoundError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))

    def _handle_post_flow(self) -> None:
        try:
            payload = self._read_json()
            definition = FlowDefinition.model_validate(payload)
            saved = self.service.save_flow(definition)
            self._send_json(saved.model_dump(mode="json"))
        except json.JSONDecodeError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _handle_execute(self) -> None:
        try:
            payload = self._read_json()
            request = FlowExecutionRequest.model_validate(payload)
            result = self.service.execute(request)
            self._send_json(result.model_dump(mode="json"))
        except FlowBuildError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
        except json.JSONDecodeError:
            self._send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))

    # Utilities ------------------------------------------------------------------------------------------------
    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, detail: str) -> None:
        self._send_json({"detail": detail}, status=status)


def serve(
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
    service_factory: Callable[[], CanvasService] | None = None,
) -> None:
    """Start the HTTP server and block until interrupted."""

    service = service_factory() if service_factory else CanvasService()
    handler = partial(CanvasHTTPRequestHandler, service=service)
    with ThreadingTCPServer((host, port), handler) as httpd:
        print(f"TriggerFlow Canvas listening on http://{host}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping TriggerFlow Canvas...")


if __name__ == "__main__":
    serve()
