import { existsSync } from "node:fs";
import { spawn, spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";

const backendRoot = path.resolve(process.cwd(), "backend");
const isWindows = process.platform === "win32";

const venvPath = path.join(
  backendRoot,
  ".venv",
  isWindows ? "Scripts" : "bin",
  isWindows ? "python.exe" : "python"
);

const activateHint = isWindows
  ? ".\\.venv\\Scripts\\Activate.ps1"
  : "source .venv/bin/activate";

function exitWith(message) {
  console.error(message);
  process.exit(1);
}

// 1. Check virtual environment
if (!existsSync(venvPath)) {
  exitWith(
    `Missing backend virtual environment.\n` +
    `Run:\ncd backend\npython -m venv .venv\n${activateHint}\npip install -e ".[dev]"`
  );
}

// 2. Check dependency (uvicorn)
const check = spawnSync(venvPath, ["-c", "import uvicorn"], {
  cwd: backendRoot,
  stdio: "ignore",
});

if (check.status !== 0) {
  exitWith(
    `Missing Python dependency 'uvicorn'.\n` +
    `Run:\ncd backend\n${activateHint}\npip install -e ".[dev]"`
  );
}

// 3. Start server (no activation needed)
const child = spawn(
  venvPath,
  [
    "-m",
    "uvicorn",
    "app.main:app",
    "--reload",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ],
  {
    cwd: backendRoot,
    stdio: "inherit",
  }
);

// 4. Forward exit signals properly
child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});