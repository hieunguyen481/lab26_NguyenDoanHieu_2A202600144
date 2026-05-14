from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

from fastmcp import Client

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent))

from init_db import create_database
import mcp_server


def print_section(title: str, payload) -> None:
    print(f"\n{title}")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def resource_json(resource_result):
    return json.loads(resource_result[0].text)


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        mcp_server.DEFAULT_DB_PATH = create_database(Path(tmp_dir) / "verify.sqlite3")
        await verify()


async def verify() -> None:
    client = Client(mcp_server.mcp)

    async with client:
        await client.ping()

        tools = await client.list_tools()
        tool_names = sorted(tool.name for tool in tools)
        print_section("Tools", tool_names)
        assert {"search", "insert", "aggregate"}.issubset(tool_names)

        resources = await client.list_resources()
        resource_uris = sorted(str(resource.uri) for resource in resources)
        print_section("Resources", resource_uris)
        assert "schema://database" in resource_uris

        templates = await client.list_resource_templates()
        template_uris = sorted(str(template.uriTemplate) for template in templates)
        print_section("Resource templates", template_uris)
        assert "schema://table/{table_name}" in template_uris

        schema = await client.read_resource("schema://database")
        print_section("Full schema resource", resource_json(schema))

        table_schema = await client.read_resource("schema://table/students")
        print_section("Students table schema", resource_json(table_schema))

        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": [{"column": "cohort", "op": "eq", "value": "A1"}],
                "order_by": "name",
                "limit": 10,
            },
        )
        print_section("Search result", search_result.data)

        insert_result = await client.call_tool(
            "insert",
            {
                "table": "students",
                "values": {
                    "name": "Lan Vu",
                    "email": "lan.vu@example.edu",
                    "cohort": "A1",
                    "age": 20,
                },
            },
        )
        print_section("Insert result", insert_result.data)

        aggregate_result = await client.call_tool(
            "aggregate",
            {
                "table": "enrollments",
                "metric": "avg",
                "column": "score",
                "group_by": "semester",
            },
        )
        print_section("Aggregate result", aggregate_result.data)

        invalid_result = await client.call_tool("search", {"table": "missing_table"})
        print_section("Invalid request result", invalid_result.data)


if __name__ == "__main__":
    asyncio.run(main())
