from __future__ import annotations

import pytest

from implementation.db import SQLiteAdapter, ValidationError
from implementation.init_db import create_database


@pytest.fixture()
def adapter(tmp_path):
    db_path = create_database(tmp_path / "test.sqlite3")
    return SQLiteAdapter(db_path)


def test_list_tables(adapter):
    assert adapter.list_tables() == ["courses", "enrollments", "students"]


def test_search_filters_ordering_and_pagination(adapter):
    result = adapter.search(
        table="students",
        columns=["name", "cohort"],
        filters=[{"column": "cohort", "op": "eq", "value": "A1"}],
        order_by="name",
        limit=1,
        offset=0,
    )

    assert result["count"] == 1
    assert result["rows"][0] == {"name": "An Nguyen", "cohort": "A1"}


def test_search_strips_identifier_whitespace(adapter):
    result = adapter.search(
        table="students\n",
        filters=[{"column": "cohort\n", "op": "eq", "value": "A1"}],
        order_by="name\n",
    )

    assert result["count"] == 2


def test_insert_returns_inserted_row(adapter):
    result = adapter.insert(
        "students",
        {
            "name": "Lan Vu",
            "email": "lan.vu@example.edu",
            "cohort": "A1",
            "age": 20,
        },
    )

    assert result["inserted_id"] > 0
    assert result["row"]["email"] == "lan.vu@example.edu"


def test_aggregate_count(adapter):
    result = adapter.aggregate("students", "count")

    assert result["rows"] == [{"value": 5}]


def test_aggregate_avg_group_by(adapter):
    result = adapter.aggregate(
        table="enrollments",
        metric="avg",
        column="score",
        group_by="semester",
    )

    assert result["rows"][0]["semester"] == "2026S"
    assert result["rows"][0]["value"] > 80


def test_invalid_table_rejected(adapter):
    with pytest.raises(ValidationError, match="unknown table"):
        adapter.search("missing")


def test_invalid_column_rejected(adapter):
    with pytest.raises(ValidationError, match="unknown column"):
        adapter.search("students", columns=["password"])


def test_invalid_filter_operator_rejected(adapter):
    with pytest.raises(ValidationError, match="unsupported filter operator"):
        adapter.search(
            "students",
            filters=[{"column": "cohort", "op": "contains", "value": "A1"}],
        )


def test_empty_insert_rejected(adapter):
    with pytest.raises(ValidationError, match="must not be empty"):
        adapter.insert("students", {})
