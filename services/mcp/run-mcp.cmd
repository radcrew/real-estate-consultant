@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo radestate-mcp: missing .venv. From services/mcp run: python -m venv .venv ^& .venv\Scripts\python.exe -m pip install -e . 1>&2
  exit /b 1
)

REM Load services/mcp/.env into this process (overrides empty Cursor-injected vars).
if exist ".env" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)

set "PYTHONPATH=%CD%;%PYTHONPATH%"
".venv\Scripts\python.exe" -m app.main
