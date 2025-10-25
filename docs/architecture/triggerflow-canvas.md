# TriggerFlow Canvas Architecture

## Overview
TriggerFlow Canvas is an interactive workflow authoring and execution environment built on top of Agently's TriggerFlow runtime. It provides a web canvas for composing triggers, blocks, and data channels; a backend that persists workflow blueprints and coordinates executions; and an integration layer that connects TriggerFlow to external systems. This document captures the system components, technology stack, module boundaries, data flows, deployment topology, communication protocols, and integration adapter interfaces required to deliver the experience.

## System Components and Technology Stack

| Component | Responsibility | Technology Choices |
| --- | --- | --- |
| Canvas Web App | Visual workflow editor, real-time status updates, authentication, and collaboration surfaces. | React + TypeScript, Zustand for state, React Flow for node graph rendering, Tailwind CSS, WebSocket client, Vite build. |
| Canvas API Gateway | Authenticates clients, enforces authorization, forwards requests to services, publishes server-sent events. | FastAPI + Python 3.11, AsyncAPI-compliant WebSocket endpoints, OAuth2/OpenID Connect integration via Authlib. |
| Flow Registry Service | Stores workflow blueprints, version history, metadata, and deployment state. | FastAPI service backed by PostgreSQL (SQLModel ORM) and Redis for caching. |
| Execution Orchestrator | Creates TriggerFlow executions, routes events to runtime, handles lifecycle (start/stop/retry). | Python TriggerFlow runtime, Celery workers with Redis broker, Pydantic models for request validation. |
| Event Stream Gateway | Streams execution progress, telemetry, and logs to clients. | Starlette WebSocket endpoints, Apache Kafka (or Redis Streams) for fan-out, Avro serialization for internal transport. |
| Integration Adapter Layer | Bridges TriggerFlow handlers with external systems (LLMs, SaaS APIs, queues). | Python plug-in modules discovered via entry points, `pydantic` schemas for configuration. |
| Observability Stack | Collects metrics, traces, and logs. | OpenTelemetry SDK, Prometheus, Grafana, Loki. |
| Deployment Automation | Packaging and deployment of services. | Docker, Kubernetes (Helm charts), GitHub Actions CI/CD. |

## Module Boundaries

### Frontend Modules
- **Graph Canvas**: wraps React Flow, renders nodes/edges, supports drag-and-drop and inline editing, translates UI state to protocol payloads.
- **Metadata Store**: manages local cache of node metadata, versions, and validation status via Zustand; synchronizes with backend through GraphQL-like queries or REST.
- **Execution Console**: subscribes to event streams, renders logs, metrics, and runtime data updates.
- **Protocol Client**: encapsulates REST/WebSocket clients, handles authentication tokens, schema validation, retries, and exponential backoff.

### Backend Modules
- **API Gateway**: single entry point exposing REST endpoints (`/flows`, `/executions`, `/events`), authenticates and maps requests to internal services.
- **Flow Registry**: owns blueprint persistence, validation, versioning, diffing, and release promotion. Exposes gRPC/REST interface to orchestrator and adapters.
- **Execution Orchestrator**: coordinates TriggerFlow runtime, schedule jobs, manages worker pools, resolves handlers via integration adapters.
- **Event Stream Gateway**: converts orchestrator events to client protocol messages, multiplexes WebSocket connections, enforces subscription policies.
- **Integration Adapter SDK**: provides base classes and utilities for third-party integrations (credentials, secrets resolution, rate limiting).

### Shared Modules
- **Identity & Access**: central auth service providing JWTs and role-based access control policies consumed by both frontend and backend.
- **Schema Registry**: stores JSON Schemas for protocol messages to ensure validation and compatibility.

## Data Flow

1. **Authoring**
   - User opens a project; Canvas Web App fetches latest blueprint via `GET /flows/{id}`.
   - Node modifications are saved through `PUT /flows/{id}` with metadata conforming to `TriggerFlowNodeMetadata` schema.
   - Flow registry validates schema, persists to PostgreSQL, updates cache, and emits `flow.updated` event to Kafka.

2. **Execution Request**
   - User clicks "Run"; Canvas Web App sends `POST /executions` containing execution request payload.
   - API Gateway authenticates, forwards to Execution Orchestrator.
   - Orchestrator loads blueprint version from Flow Registry, resolves integration adapters, enqueues job for TriggerFlow worker.

3. **Runtime Streaming**
   - Worker spins up `TriggerFlowExecution`, emits chunk status via Event Stream Gateway.
   - Event Stream Gateway publishes events to WebSocket clients subscribed to `/executions/{id}/events`.
   - Frontend Execution Console updates UI with runtime data, logs, and status transitions.

4. **Completion and Persistence**
   - On completion/failure, orchestrator persists execution summary, metrics, and logs to PostgreSQL/S3.
   - Flow registry stores derived artifacts (snapshots, exported code) if required.

## Deployment Topology

```
+-------------------+            +-------------------+
|  Canvas Web App   |<--https--> |   API Gateway     |
+-------------------+            +-------------------+
           |                               |
           |                               v
           |                     +-------------------+
           |                     | Flow Registry     |
           |                     +-------------------+
           |                               |
           v                               v
+-------------------+             +-------------------+
| Event Stream GW   | <---------> | Execution Orchestrator |
+-------------------+             +-------------------+
                                         |
                                         v
                                +-------------------+
                                | TriggerFlow Workers|
                                +-------------------+
                                         |
                                         v
                                +-------------------+
                                | Integration Layer |
                                +-------------------+
                                         |
                                         v
                                External SaaS / APIs
```

All components run inside Kubernetes. The Canvas Web App is served by an Nginx ingress, while API Gateway, Flow Registry, Execution Orchestrator, Event Stream Gateway, and TriggerFlow workers run as separate deployments sharing a Redis cache and connecting to managed PostgreSQL, Kafka, and object storage services. Horizontal Pod Autoscalers scale orchestrator and worker deployments based on queue depth and CPU utilization. Prometheus and Grafana run in the same cluster for observability.

## Frontend ↔ Backend Communication Protocols

### Node Metadata Exchange
- **Endpoint**: `GET /flows/{flowId}/nodes`, `PUT /flows/{flowId}/nodes/{nodeId}`
- **Transport**: HTTPS (REST)
- **Schema**: `TriggerFlowNodeMetadata`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agently.dev/schemas/triggerflow/node-metadata.json",
  "title": "TriggerFlowNodeMetadata",
  "type": "object",
  "required": ["id", "type", "name", "handlers", "position"],
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "type": {"type": "string", "enum": ["trigger", "action", "condition", "subflow", "output"]},
    "name": {"type": "string", "minLength": 1},
    "description": {"type": "string"},
    "handlers": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["entrypoint"],
        "properties": {
          "entrypoint": {"type": "string", "description": "Python dotted path or adapter reference"},
          "config": {"type": "object", "additionalProperties": true},
          "timeoutSeconds": {"type": "integer", "minimum": 1},
          "retries": {
            "type": "object",
            "properties": {
              "maxAttempts": {"type": "integer", "minimum": 0},
              "backoffSeconds": {"type": "integer", "minimum": 0}
            },
            "additionalProperties": false
          }
        },
        "additionalProperties": false
      }
    },
    "position": {
      "type": "object",
      "required": ["x", "y"],
      "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"}
      },
      "additionalProperties": false
    },
    "ports": {
      "type": "object",
      "properties": {
        "inputs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["key", "label", "type"],
            "properties": {
              "key": {"type": "string"},
              "label": {"type": "string"},
              "type": {"type": "string"},
              "default": {}
            },
            "additionalProperties": false
          }
        },
        "outputs": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["key", "label"],
            "properties": {
              "key": {"type": "string"},
              "label": {"type": "string"},
              "type": {"type": "string"}
            },
            "additionalProperties": false
          }
        }
      },
      "additionalProperties": false
    },
    "annotations": {
      "type": "object",
      "additionalProperties": true
    },
    "version": {"type": "integer", "minimum": 0}
  },
  "additionalProperties": false
}
```

### Execution Request
- **Endpoint**: `POST /executions`
- **Transport**: HTTPS (REST)
- **Schema**: `TriggerFlowExecutionRequest`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agently.dev/schemas/triggerflow/execution-request.json",
  "title": "TriggerFlowExecutionRequest",
  "type": "object",
  "required": ["flowId", "inputs"],
  "properties": {
    "flowId": {"type": "string", "format": "uuid"},
    "blueprintVersion": {"type": "string"},
    "inputs": {
      "type": "object",
      "additionalProperties": true
    },
    "context": {
      "type": "object",
      "properties": {
        "userId": {"type": "string"},
        "labels": {
          "type": "array",
          "items": {"type": "string"}
        },
        "priority": {"type": "string", "enum": ["low", "normal", "high"]}
      },
      "additionalProperties": false
    },
    "executionOptions": {
      "type": "object",
      "properties": {
        "async": {"type": "boolean", "default": true},
        "timeoutSeconds": {"type": "integer", "minimum": 1},
        "trace": {"type": "boolean", "default": false}
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### Event Stream
- **Endpoint**: `GET /executions/{executionId}/events`
- **Transport**: WebSocket (JSON message frames)
- **Schema**: `TriggerFlowExecutionEvent`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://agently.dev/schemas/triggerflow/execution-event.json",
  "title": "TriggerFlowExecutionEvent",
  "type": "object",
  "required": ["id", "executionId", "type", "timestamp"],
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "executionId": {"type": "string", "format": "uuid"},
    "type": {
      "type": "string",
      "enum": [
        "execution.started",
        "execution.completed",
        "execution.failed",
        "chunk.started",
        "chunk.completed",
        "chunk.failed",
        "runtime.output",
        "log",
        "metric"
      ]
    },
    "timestamp": {"type": "string", "format": "date-time"},
    "payload": {
      "oneOf": [
        {
          "type": "object",
          "title": "ExecutionState",
          "properties": {
            "status": {"type": "string", "enum": ["running", "succeeded", "failed"]},
            "message": {"type": "string"}
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "title": "ChunkEvent",
          "required": ["nodeId", "status"],
          "properties": {
            "nodeId": {"type": "string", "format": "uuid"},
            "status": {"type": "string", "enum": ["running", "succeeded", "failed"]},
            "result": {},
            "error": {
              "type": "object",
              "properties": {
                "type": {"type": "string"},
                "message": {"type": "string"},
                "stack": {"type": "string"}
              },
              "additionalProperties": false
            }
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "title": "RuntimeOutput",
          "required": ["stream"],
          "properties": {
            "stream": {"type": "string", "enum": ["stdout", "stderr", "custom"]},
            "data": {},
            "sequence": {"type": "integer", "minimum": 0}
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "title": "LogEvent",
          "required": ["level", "message"],
          "properties": {
            "level": {"type": "string", "enum": ["debug", "info", "warning", "error"]},
            "message": {"type": "string"},
            "nodeId": {"type": "string", "format": "uuid"}
          },
          "additionalProperties": false
        },
        {
          "type": "object",
          "title": "MetricEvent",
          "required": ["name", "value"],
          "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"},
            "unit": {"type": "string"}
          },
          "additionalProperties": false
        }
      ]
    }
  },
  "additionalProperties": false
}
```

## TriggerFlow Integration Adapter Interface

The integration adapter layer allows TriggerFlow to interact with external systems without hardcoding dependencies into workflow handlers. Adapters translate between TriggerFlow's execution context and vendor-specific APIs.

### Adapter Responsibilities
- Provide metadata describing available handler entrypoints and configuration requirements.
- Resolve handler callables and inject credentials/configuration at runtime.
- Persist workflow blueprints to remote systems when needed (e.g., SaaS workflow builders) and load them back into TriggerFlow.
- Emit capability and health information to allow orchestration decisions.

### Python Interface

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Mapping
from agently.core import TriggerFlowBluePrint

class TriggerFlowIntegrationAdapter(ABC):
    """Defines the contract for integrating TriggerFlow with external systems."""

    name: str

    @abstractmethod
    def describe(self) -> Mapping[str, Any]:
        """Return metadata about available handlers, configuration schema, and capabilities."""

    @abstractmethod
    def resolve_handler(self, reference: str) -> Any:
        """Return a callable or coroutine function for the given handler reference."""

    @abstractmethod
    def load_blue_print(self, *, source: Mapping[str, Any]) -> TriggerFlowBluePrint:
        """Construct and return a TriggerFlowBluePrint from an external serialized representation."""

    @abstractmethod
    def save_blue_print(self, *, blue_print: TriggerFlowBluePrint) -> Mapping[str, Any]:
        """Serialize and persist the blueprint, returning an external identifier or descriptor."""

    def on_execution_start(self, execution_id: str, context: Mapping[str, Any]) -> None:
        """Optional lifecycle hook before execution begins."""

    def on_execution_end(self, execution_id: str, context: Mapping[str, Any], *, success: bool) -> None:
        """Optional lifecycle hook after execution finishes."""
```

### Loading and Saving Workflows

- **Saving**: When the Flow Registry receives an updated blueprint, it calls `save_blue_print` on all registered adapters whose handlers are referenced in the flow. The adapter serializes the `TriggerFlowBluePrint` into its domain format (e.g., vendor JSON schema) and persists it (API call, file storage). The method returns a descriptor (external ID, version, checksum) that the registry stores alongside the blueprint to support round-trip synchronization.

- **Loading**: On import or execution, the orchestrator retrieves adapter descriptors from the registry and calls `load_blue_print`. The adapter fetches the external definition, translates it into a `TriggerFlowBluePrint`, and returns it. The orchestrator merges or replaces the in-cluster blueprint ensuring schema compatibility before execution.

- **Versioning**: Adapters should embed external version identifiers within the descriptor, allowing the Flow Registry to detect drift between TriggerFlow and remote systems.

- **Error Handling**: Exceptions raised during load/save propagate as adapter-specific errors. The orchestrator converts them into `chunk.failed` events so clients can surface actionable feedback.

### Registration and Discovery

Adapters are distributed as Python packages exposing an entry point group `agently.triggerflow.adapters`. At startup, the Integration Adapter Layer loads available adapters, validates their configuration via `describe()`, and registers handler references in the Flow Registry. The Canvas Web App uses the Node Metadata protocol to enumerate handler types and expose them in the UI.

## Summary

This architecture ensures TriggerFlow Canvas delivers a robust, extensible workflow authoring and execution experience backed by strict schemas, clear module boundaries, and a pluggable integration layer.
