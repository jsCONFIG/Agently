from __future__ import annotations

import asyncio


async def main() -> None:
    print("TriggerFlow core placeholder 正在运行，等待后端调度…", flush=True)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
