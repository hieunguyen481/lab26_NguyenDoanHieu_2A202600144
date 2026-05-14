# Lab Report: SQLite FastMCP Server

## 1. Overview

This submission implements a FastMCP server backed by SQLite for the database MCP lab. The server exposes three required MCP tools and two schema resources.

Implemented tools:

- `search`
- `insert`
- `aggregate`

Implemented resources:

- `schema://database`
- `schema://table/{table_name}`

The database contains three related tables:

- `students`
- `courses`
- `enrollments`

## 2. Repository Structure

Main implementation files:

- `implementation/init_db.py`: creates the SQLite schema and seed data
- `implementation/db.py`: database adapter, validation, and SQL execution
- `implementation/mcp_server.py`: FastMCP tools and resources
- `implementation/verify_server.py`: repeatable MCP verification script
- `implementation/verify_stdio.py`: stdio client smoke test
- `implementation/tests/test_db.py`: database behavior tests
- `implementation/tests/test_server.py`: server wrapper/resource tests

Supporting files:

- `README.md`: setup, usage, verification, Inspector, and Codex instructions
- `AGENTS.md`: Codex project instruction for the MCP server
- `requirements.txt`: Python dependencies
- `demo_assets/`: screenshots used for demo evidence

## 3. Implemented Features

The implementation satisfies the required lab features:

- FastMCP server starts over stdio
- SQLite database can be initialized reproducibly
- `search` supports filters, ordering, limit, and offset
- `insert` inserts a validated row and returns the inserted payload
- `aggregate` supports `count`, `avg`, `sum`, `min`, and `max`
- full database schema resource is exposed
- per-table schema resource template is exposed
- invalid tables, columns, operators, aggregates, pagination, and empty inserts are rejected

## 4. Safety and Validation

The database adapter validates table and column names against SQLite schema metadata before building SQL. User values are passed through SQLite parameter placeholders instead of raw string concatenation.

Validation examples:

- unknown table: rejected
- unknown column: rejected
- unsupported operator: rejected
- empty insert payload: rejected
- invalid aggregate metric or missing aggregate column: rejected

The MCP tools return clear structured error payloads such as:

```json
{
  "ok": false,
  "error": "unknown table 'missing_table'"
}
```

## 5. Verification Results

Automated tests:

```powershell
python -m pytest -p no:cacheprovider implementation\tests
```

Result:

```text
13 passed
```

MCP verification script:

```powershell
python implementation\verify_server.py
```

Verified:

- tool discovery: `search`, `insert`, `aggregate`
- resource discovery: `schema://database`
- resource template discovery: `schema://table/{table_name}`
- successful `search`
- successful `insert`
- successful `aggregate`
- invalid table error handling

## 6. Inspector Verification

MCP Inspector was used to verify the server manually.

Verified in Inspector:

- server connected successfully
- tools were discoverable
- `search` returned students in cohort `A1`
- `aggregate` returned average score by semester
- invalid table request returned a clear error
- `schema://database` returned the full schema
- `schema://table/students` returned the students table schema

Screenshots are stored in `demo_assets/`.

## 7. Codex Client Verification

Codex MCP configuration:

```toml
[mcp_servers.sqlite_lab]
command = "D:/puthon310/python.exe"
args = ["D:/VinUni/Day26-Track3-MCP-tool-integration-main/Day26-Track3-MCP-tool-integration-main/implementation/mcp_server.py"]
```

Verified command:

```powershell
codex exec -m gpt-5.4 -C "D:\VinUni\Day26-Track3-MCP-tool-integration-main\Day26-Track3-MCP-tool-integration-main" -s read-only "Use the sqlite_lab MCP server. Read schema://database, then search students in cohort A1. Return only the table names and student names."
```

Observed output:

```text
students

An Nguyen
Binh Tran
```

## 8. Demo Video

Demo video link:

https://drive.google.com/file/d/1lO6ljJporYHW5AyEoAyhHQRqYY6o97JK/view?usp=sharing

The video demonstrates setup/verification, Inspector tool usage, schema resources, and Codex MCP client integration.

## 9. Completion Status

The lab is complete against the base rubric:

- Server Foundation: complete
- Required Tools: complete
- MCP Resources: complete
- Safety and Error Handling: complete
- Verification: complete
- Client Integration and Demo: complete

Bonus features such as HTTP auth or PostgreSQL support were not implemented.
