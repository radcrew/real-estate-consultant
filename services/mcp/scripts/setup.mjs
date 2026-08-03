/**
 * Cross-platform MCP launcher for local concurrent dev (Streamable HTTP).
 * Stdio mode stays for Cursor via run-mcp.cmd / mcp.json.
 */
import { existsSync, readFileSync } from "node:fs";
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

/** Load services/mcp/.env into env, skipping blank values so they do not wipe secrets. */
function loadDotEnv(env) {
  const envPath = path.join(mcpRoot, ".env");
  if (!existsSync(envPath)) {
    return env;
  }
  const next = { ...env };
  for (const raw of readFileSync(envPath, "utf8").split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) {
      continue;
    }
    const eq = line.indexOf("=");
    const key = line.slice(0, eq).trim();
    const value = line.slice(eq + 1).trim();
    if (!key || !value) {
      continue;
    }
    next[key] = value;
  }
  return next;
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
// .env supplies credentials, but this launcher is the HTTP entry point — its
// transport/bind settings must win. Loading .env last would let the stdio
// default shipped in .env.example silently start a server that binds no port.
const childEnv = {
  ...loadDotEnv({ ...process.env }),
  PYTHONPATH: mcpRoot,
  MCP_TRANSPORT: "streamable-http",
  MCP_HTTP_HOST: host,
  MCP_HTTP_PORT: String(port),
};

const child = spawn(venvPython, ["-m", "app.main"], {
  cwd: mcpRoot,
  stdio: "inherit",
  env: childEnv,
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
