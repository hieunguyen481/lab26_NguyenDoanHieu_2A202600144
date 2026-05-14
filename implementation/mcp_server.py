from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

try:
    from .db import SQLiteAdapter, ValidationError
    from .init_db import DEFAULT_DB_PATH, create_database
except ImportError:
    from db import SQLiteAdapter, ValidationError
    from init_db import DEFAULT_DB_PATH, create_database


mcp = FastMCP("SQLite Lab MCP Server")


def get_adapter() -> SQLiteAdapter:
    db_path = Path(DEFAULT_DB_PATH)
    if not db_path.exists():
        create_database(db_path)
    return SQLiteAdapter(db_path)


def _handle_validation_error(error: ValidationError) -> dict[str, Any]:
    return {"ok": False, "error": str(error)}


@mcp.tool(
    name="search",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def search(
    table: str,
    filters: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search rows in a whitelisted SQLite table with validated filters and pagination."""
    try:
        result = get_adapter().search(
            table=table,
            filters=filters,
            columns=columns,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
        return {"ok": True, **result}
    except ValidationError as error:
        return _handle_validation_error(error)


@mcp.tool(
    name="insert",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert one row into a whitelisted SQLite table and return the inserted row."""
    try:
        result = get_adapter().insert(table=table, values=values)
        return {"ok": True, **result}
    except ValidationError as error:
        return _handle_validation_error(error)


@mcp.tool(
    name="aggregate",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Run count, avg, sum, min, or max over validated table and column names."""
    try:
        result = get_adapter().aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
        return {"ok": True, **result}
    except ValidationError as error:
        return _handle_validation_error(error)


@mcp.resource("schema://database", mime_type="application/json")
def database_schema() -> dict[str, Any]:
    """Return the full database schema as JSON."""
    return get_adapter().get_database_schema()


@mcp.resource("schema://table/{table_name}", mime_type="application/json")
def table_schema(table_name: str) -> dict[str, Any]:
    """Return schema information for one table."""
    try:
        return get_adapter().get_table_schema(table_name)
    except ValidationError as error:
        return {"ok": False, "error": str(error)}


if __name__ == "__main__":
    mcp.run()
