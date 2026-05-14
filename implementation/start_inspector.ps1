$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Server = Join-Path $PSScriptRoot "mcp_server.py"

if (-not (Test-Path $Python)) {
    $Python = (Get-Command python).Source
}

$PythonForInspector = $Python -replace "\\", "/"
$ServerForInspector = $Server -replace "\\", "/"

Write-Host "Starting MCP Inspector with:"
Write-Host "  Python: $PythonForInspector"
Write-Host "  Server: $ServerForInspector"
Write-Host "  Auth: disabled for local demo"

$env:DANGEROUSLY_OMIT_AUTH = "true"
npx -y @modelcontextprotocol/inspector $PythonForInspector $ServerForInspector
