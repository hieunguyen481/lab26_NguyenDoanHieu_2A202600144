# SQLite Lab MCP Server

This project implements a FastMCP server backed by SQLite. It exposes three MCP tools:

- `search`
- `insert`
- `aggregate`

It also exposes database schema context through MCP resources:

- `schema://database`
- `schema://table/{table_name}`

The sample database uses three related tables: `students`, `courses`, and `enrollments`.

## Project Structure

```text
implementation/
  __init__.py
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  start_inspector.ps1
  tests/
    test_db.py
    test_server.py
pseudocode/
requirements.txt
AGENTS.md
```

## Setup

Use a virtual environment so FastMCP dependencies do not conflict with other Python projects.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python implementation\init_db.py
```

## Run The MCP Server

```powershell
python implementation\mcp_server.py
```

FastMCP uses stdio by default, which is the expected transport for local MCP clients such as Codex, Claude Code, and Gemini CLI.

## Tools

### `search`

Search rows in a validated table with filters, selected columns, ordering, limit, and offset.

Example arguments:

```json
{
  "table": "students",
  "filters": [{"column": "cohort", "op": "eq", "value": "A1"}],
  "order_by": "name",
  "limit": 10
}
```

Supported filter operators:

```text
eq, ne, lt, lte, gt, gte, like, in
```

### `insert`

Insert one row and return the inserted record.

Example arguments:

```json
{
  "table": "students",
  "values": {
    "name": "Lan Vu",
    "email": "lan.vu@example.edu",
    "cohort": "A1",
    "age": 20
  }
}
```

### `aggregate`

Run `count`, `avg`, `sum`, `min`, or `max`.

Example arguments:

```json
{
  "table": "enrollments",
  "metric": "avg",
  "column": "score",
  "group_by": "semester"
}
```

## Resources

Read the full schema:

```text
schema://database
```

Read one table schema:

```text
schema://table/students
```

## Safety

The server rejects:

- unknown table names
- unknown column names
- unsupported filter operators
- invalid aggregate metrics
- aggregate calls missing required columns
- empty inserts
- invalid pagination

SQL values are passed through SQLite parameters. Table and column identifiers are only inserted into SQL after validation against SQLite schema metadata.

## Automated Tests

```powershell
python -m pytest -p no:cacheprovider implementation\tests
```

Expected result:

```text
12 passed
```

## Verification Script

Run:

```powershell
python implementation\verify_server.py
```

The script verifies:

- MCP server ping
- discovery of `search`, `insert`, and `aggregate`
- discovery of `schema://database`
- discovery of `schema://table/{table_name}`
- valid `search`
- valid `insert`
- valid `aggregate`
- invalid table request returns a clear error

## MCP Inspector

PowerShell helper:

```powershell
.\implementation\start_inspector.ps1
```

Manual command:

```powershell
npx -y @modelcontextprotocol/inspector D:/puthon310/python.exe D:/VinUni/Day26-Track3-MCP-tool-integration-main/Day26-Track3-MCP-tool-integration-main/implementation/mcp_server.py
```

In Inspector, check:

- tools list contains `search`, `insert`, `aggregate`
- resources list contains `schema://database`
- resource templates contain `schema://table/{table_name}`
- valid calls work
- invalid calls return clear errors

## Codex Client Configuration

Add this to `~/.codex/config.toml`. Replace the path if your repo is in a different location.

```toml
[mcp_servers.sqlite_lab]
command = "D:/puthon310/python.exe"
args = ["D:/VinUni/Day26-Track3-MCP-tool-integration-main/Day26-Track3-MCP-tool-integration-main/implementation/mcp_server.py"]
```

Verify Codex can see the server:

```powershell
codex mcp list
```

Expected row:

```text
sqlite_lab  D:/puthon310/python.exe  .../implementation/mcp_server.py  enabled
```

Example Codex prompt:

```text
Use the sqlite_lab MCP server. Read schema://database, then search students in cohort A1.
```

Another prompt:

```text
Use sqlite_lab to compute the average enrollment score grouped by semester.
```

Verified non-interactive Codex command:

```powershell
codex exec -m gpt-5.4 -C "D:\VinUni\Day26-Track3-MCP-tool-integration-main\Day26-Track3-MCP-tool-integration-main" -s read-only "Use the sqlite_lab MCP server. Read schema://database, then search students in cohort A1. Return only the table names and student names."
```

Expected output:

```text
students

An Nguyen
Binh Tran
```

If your Codex CLI reports that `gpt-5.5` requires a newer version, either upgrade Codex CLI or pass `-m gpt-5.4` for this demo command.

## Demo Script

Use this flow for a 2 minute demo:

1. Show project structure.
2. Run `python implementation\init_db.py`.
3. Run `python implementation\verify_server.py`.
4. Open MCP Inspector or Codex.
5. Show the three tools are discoverable.
6. Read `schema://database`.
7. Call `search` for students in cohort `A1`.
8. Call `insert` to add one student.
9. Call `aggregate` to compute average score.
10. Call `search` with `missing_table` and show the clear error.

## Report And Demo Video

- Report: `REPORT.md`
- Demo video: https://drive.google.com/file/d/1lO6ljJporYHW5AyEoAyhHQRqYY6o97JK/view?usp=sharing
