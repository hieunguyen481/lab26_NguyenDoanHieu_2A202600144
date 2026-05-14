from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import Client


async def main() -> None:
    server_path = Path(__file__).resolve().parent / "mcp_server.py"
    async with Client(str(server_path)) as client:
        await client.ping()
        tools = await client.list_tools()
        print("STDIO tools:", sorted(tool.name for tool in tools))


if __name__ == "__main__":
    asyncio.run(main())
