@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo radestate-mcp: missing .venv. From services/mcp run: python -m venv .venv ^& .venv\Scripts\python.exe -m pip install -e . 1>&2
  exit /b 1
)

REM Prefer the console script when present; fall back to python -m.
if exist ".venv\Scripts\radestate-mcp.exe" (
  ".venv\Scripts\radestate-mcp.exe"
) else (
  ".venv\Scripts\python.exe" -m app.main
)
