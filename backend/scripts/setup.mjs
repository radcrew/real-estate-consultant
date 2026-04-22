import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";

const backendRoot = path.resolve(process.cwd(), "backend");
const isWindows = process.platform === "win32";
const pythonPath = isWindows
  ? path.join(backendRoot, ".venv", "Scripts", "python.exe")
  : path.join(backendRoot, ".venv", "bin", "python");

if (!existsSync(pythonPath)) {
  const activateHint = isWindows
    ? ".\\.venv\\Scripts\\Activate.ps1"
    : "source .venv/bin/activate";
  console.error(
    `Missing backend virtual environment. Run: cd backend; python -m venv .venv; ${activateHint}; pip install -e ".[dev]"`
  );
  process.exit(1);
}

const child = spawn(
  pythonPath,
  ["-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
  {
    cwd: backendRoot,
    stdio: "inherit",
  }
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
