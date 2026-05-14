from __future__ import annotations

from implementation import mcp_server
from implementation.init_db import create_database


def use_temp_database(tmp_path):
    db_path = create_database(tmp_path / "server_test.sqlite3")
    mcp_server.DEFAULT_DB_PATH = db_path


def test_search_tool_success(tmp_path):
    use_temp_database(tmp_path)
    result = mcp_server.search(
        table="students",
        filters=[{"column": "cohort", "op": "eq", "value": "A1"}],
    )

    assert result["ok"] is True
    assert result["count"] == 2


def test_search_tool_validation_error(tmp_path):
    use_temp_database(tmp_path)
    result = mcp_server.search(table="missing_table")

    assert result["ok"] is False
    assert "unknown table" in result["error"]


def test_schema_resources(tmp_path):
    use_temp_database(tmp_path)
    full_schema = mcp_server.database_schema()
    student_schema = mcp_server.table_schema("students")

    assert "students" in full_schema["tables"]
    assert student_schema["table"] == "students"
