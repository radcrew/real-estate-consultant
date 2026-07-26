/**
 * Cross-platform MCP launcher for local concurrent dev (Streamable HTTP).
 * Stdio mode stays for Cursor via run-mcp.cmd / mcp.json.
 */
import { existsSync } from "node:fs";
import { spawn, spawnSync } from "node:child_process";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mcpRoot = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";

const venvPython = path.join(
  mcpRoot,
  ".venv",
  isWindows ? "Scripts" : "bin",
  isWindows ? "python.exe" : "python",
);

const activateHint = isWindows
  ? ".\\.venv\\Scripts\\Activate.ps1"
  : "source .venv/bin/activate";

function exitWith(message) {
  console.error(message);
  process.exit(1);
}

if (!existsSync(venvPython)) {
  exitWith(
    `Missing MCP virtual environment.\n` +
      `Run:\ncd services/mcp\npython -m venv .venv\n${activateHint}\npip install -e .`,
  );
}

const check = spawnSync(venvPython, ["-c", "import mcp, app"], {
  cwd: mcpRoot,
  env: { ...process.env, PYTHONPATH: mcpRoot },
  stdio: "ignore",
});

if (check.status !== 0) {
  exitWith(
    `Missing MCP Python deps.\n` +
      `Run:\ncd services/mcp\n${activateHint}\npip install -e .`,
  );
}

const host = process.env.MCP_HTTP_HOST || "127.0.0.1";
const port = process.env.MCP_HTTP_PORT || "8900";

const child = spawn(venvPython, ["-m", "app.main"], {
  cwd: mcpRoot,
  stdio: "inherit",
  env: {
    ...process.env,
    PYTHONPATH: mcpRoot,
    MCP_TRANSPORT: "streamable-http",
    MCP_HTTP_HOST: host,
    MCP_HTTP_PORT: String(port),
  },
});

console.error(
  `radestate MCP (HTTP) → http://${host}:${port}/mcp  (token from services/mcp/.env)`,
);

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
