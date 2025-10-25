"""TriggerFlow Canvas 聊天机器人示例流程。

该示例展示了如何将 Canvas 中的 HTTP 触发器与对话节点映射到
原生 TriggerFlow 代码：

1. `receive_http_request` 对应画布上的 `trigger.http` 触发器，接收请求并提取用户输入。
2. `chat_completion` 模拟 `action.chat_completion` 节点，基于输入生成回复。
3. 流程末尾调用 `.end()`，将最后一个节点的返回值作为执行结果。

运行方式：

```bash
python examples/triggerflow-canvas/chatbot_flow.py
```
"""

from __future__ import annotations

import asyncio
from agently import TriggerFlow, TriggerFlowEventData

flow = TriggerFlow(name="canvas-http-chatbot")


async def receive_http_request(data: TriggerFlowEventData) -> dict[str, object]:
    """模拟 HTTP 触发器，将请求体写入运行时数据。"""
    payload = data.value or {}
    message = payload.get("message", "")
    await data.async_set_runtime_data("http.payload", payload)
    await data.async_set_runtime_data("chat.message", message)
    return {"message": message}


async def chat_completion(data: TriggerFlowEventData) -> dict[str, object]:
    """根据用户输入构造回复并记录历史。"""
    message = data.get_runtime_data("chat.message", "")
    history = data.get_runtime_data("chat.history", []) or []
    reply = f"Echo: {message}" if message else "请提供消息内容。"
    history = [*history, {"role": "assistant", "content": reply}]
    await data.async_set_runtime_data("chat.history", history)
    return {"reply": reply, "history": history}


flow.to(receive_http_request).to(chat_completion).end()


async def main() -> None:
    execution = flow.create_execution()
    result = await execution.async_start(
        {"message": "你好，TriggerFlow Canvas!"}, wait_for_result=True
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
