"""TriggerFlow Canvas 数据管道示例流程。

展示 Canvas 中 HTTP 触发器、HTTP 请求和自定义节点的组合用法：

1. `prepare_request` 模拟 `trigger.http` 节点，解析请求参数。
2. `fetch_dataset` 对应 `action.http_request`，示例中返回伪造数据。
3. `transform_records` 演示自定义数据处理节点。

运行方式：

```bash
python examples/triggerflow-canvas/data_pipeline_flow.py
```
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from agently import TriggerFlow, TriggerFlowEventData

flow = TriggerFlow(name="canvas-data-pipeline")


async def prepare_request(data: TriggerFlowEventData) -> Dict[str, Any]:
    """提取数据源配置并写入运行时。"""
    payload = data.value or {}
    source_url = payload.get("source_url", "https://example.com/api")
    method = payload.get("method", "GET")
    await data.async_set_runtime_data("http.request", {"url": source_url, "method": method})
    return {"url": source_url, "method": method}


async def fetch_dataset(data: TriggerFlowEventData) -> Dict[str, Any]:
    """模拟外部 API 调用，返回结构化数据。"""
    request = data.get_runtime_data("http.request", {})
    print(f"Fetching dataset from {request.get('url')} with method {request.get('method')}")
    records = [
        {"id": 1, "value": 42},
        {"id": 2, "value": 7},
        {"id": 3, "value": 13},
    ]
    await data.async_set_runtime_data("dataset.raw", records)
    return {"status": 200, "items": records}


async def transform_records(data: TriggerFlowEventData) -> Dict[str, List[Dict[str, Any]]]:
    """清洗数据并返回供下游节点使用的格式。"""
    records = data.get_runtime_data("dataset.raw", []) or []
    normalized = [
        {
            "id": item.get("id"),
            "value": item.get("value"),
            "processed": True,
        }
        for item in records
    ]
    return {"records": normalized}


flow.to(prepare_request).to(fetch_dataset).to(transform_records).end()


async def main() -> None:
    execution = flow.create_execution()
    result = await execution.async_start(
        {"source_url": "https://data-service/api/items", "method": "POST"},
        wait_for_result=True,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
