from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    FILTER_OPERATORS = {
        "eq": "=",
        "ne": "!=",
        "lt": "<",
        "lte": "<=",
        "gt": ">",
        "gte": ">=",
        "like": "LIKE",
        "in": "IN",
    }
    AGGREGATES = {"count", "avg", "sum", "min", "max"}

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def list_tables(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> dict[str, Any]:
        table = self.validate_table(table)
        with self.connect() as conn:
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        return {
            "table": table,
            "columns": [
                {
                    "name": row["name"],
                    "type": row["type"],
                    "not_null": bool(row["notnull"]),
                    "default": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                }
                for row in rows
            ],
        }

    def get_database_schema(self) -> dict[str, Any]:
        return {
            "tables": {
                table: self.get_table_schema(table)
                for table in self.list_tables()
            }
        }

    def search(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: list[dict[str, Any]] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table = self.validate_table(table)
        selected_columns = self._validate_columns(table, columns) if columns else ["*"]
        where_sql, params = self._build_where(table, filters)
        limit, offset = self._validate_pagination(limit, offset)

        sql = f"SELECT {self._select_list(selected_columns)} FROM {self._quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            order_by = self.validate_column(table, order_by)
            direction = "DESC" if descending else "ASC"
            sql += f" ORDER BY {self._quote_identifier(order_by)} {direction}"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(sql, params).fetchall()]

        return {
            "table": table,
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "rows": rows,
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table = self.validate_table(table)
        if not values:
            raise ValidationError("insert values must not be empty")

        columns = [self._normalize_identifier(column) for column in values.keys()]
        if len(columns) != len(set(columns)):
            raise ValidationError("insert values contain duplicate columns after normalization")
        self._validate_columns(table, columns)
        normalized_values = {
            self._normalize_identifier(column): value
            for column, value in values.items()
        }

        quoted_columns = ", ".join(self._quote_identifier(column) for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT INTO {self._quote_identifier(table)} ({quoted_columns}) "
            f"VALUES ({placeholders})"
        )

        with self.connect() as conn:
            cursor = conn.execute(sql, [normalized_values[column] for column in columns])
            inserted_id = cursor.lastrowid
            conn.commit()
            row = conn.execute(
                f"SELECT * FROM {self._quote_identifier(table)} WHERE rowid = ?",
                (inserted_id,),
            ).fetchone()

        return {
            "table": table,
            "inserted_id": inserted_id,
            "row": dict(row) if row else dict(values),
        }

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: list[dict[str, Any]] | None = None,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        table = self.validate_table(table)
        metric = metric.lower()
        if metric not in self.AGGREGATES:
            raise ValidationError(
                f"unsupported aggregate metric '{metric}'. Supported metrics: {sorted(self.AGGREGATES)}"
            )
        if metric == "count":
            target = "*"
        else:
            if not column:
                raise ValidationError(f"aggregate metric '{metric}' requires a column")
            column = self.validate_column(table, column)
            target = self._quote_identifier(column)

        select_parts = []
        if group_by:
            group_by = self.validate_column(table, group_by)
            select_parts.append(self._quote_identifier(group_by))
        select_parts.append(f"{metric.upper()}({target}) AS value")

        sql = f"SELECT {', '.join(select_parts)} FROM {self._quote_identifier(table)}"
        where_sql, params = self._build_where(table, filters)
        if where_sql:
            sql += f" WHERE {where_sql}"
        if group_by:
            quoted_group = self._quote_identifier(group_by)
            sql += f" GROUP BY {quoted_group} ORDER BY {quoted_group}"

        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(sql, params).fetchall()]

        return {
            "table": table,
            "metric": metric,
            "column": column,
            "group_by": group_by,
            "rows": rows,
        }

    def validate_table(self, table: str) -> str:
        table = self._normalize_identifier(table)
        if table not in self.list_tables():
            raise ValidationError(f"unknown table '{table}'")
        return table

    def validate_column(self, table: str, column: str) -> str:
        column = self._normalize_identifier(column)
        valid_columns = self._column_names(table)
        if column not in valid_columns:
            raise ValidationError(f"unknown column '{column}' for table '{table}'")
        return column

    def _validate_columns(self, table: str, columns: list[str]) -> list[str]:
        if not columns:
            raise ValidationError("columns must not be empty when provided")
        return [self.validate_column(table, column) for column in columns]

    def _column_names(self, table: str) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        return {row["name"] for row in rows}

    def _build_where(
        self,
        table: str,
        filters: list[dict[str, Any]] | None,
    ) -> tuple[str, list[Any]]:
        if not filters:
            return "", []
        if not isinstance(filters, list):
            raise ValidationError("filters must be a list of objects")

        clauses: list[str] = []
        params: list[Any] = []
        for item in filters:
            if not isinstance(item, dict):
                raise ValidationError("each filter must be an object")
            column = item.get("column")
            operator = item.get("op", "eq")
            value = item.get("value")
            if not column:
                raise ValidationError("filter column is required")
            column = self.validate_column(table, column)
            if operator not in self.FILTER_OPERATORS:
                raise ValidationError(f"unsupported filter operator '{operator}'")

            quoted_column = self._quote_identifier(column)
            sql_operator = self.FILTER_OPERATORS[operator]
            if operator == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError("operator 'in' requires a non-empty list value")
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{quoted_column} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{quoted_column} {sql_operator} ?")
                params.append(value)

        return " AND ".join(clauses), params

    def _validate_pagination(self, limit: int, offset: int) -> tuple[int, int]:
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise ValidationError("limit must be an integer between 1 and 100")
        if not isinstance(offset, int) or offset < 0:
            raise ValidationError("offset must be a non-negative integer")
        return limit, offset

    def _select_list(self, columns: list[str]) -> str:
        if columns == ["*"]:
            return "*"
        return ", ".join(self._quote_identifier(column) for column in columns)

    def _quote_identifier(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    def _normalize_identifier(self, identifier: str) -> str:
        if not isinstance(identifier, str):
            raise ValidationError("table and column names must be strings")
        return identifier.strip()
