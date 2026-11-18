/**
 * Stray-profraw guard for the native vitest run.
 *
 * The scan-and-delete logic lives once in `scripts/run/clean_stray_profraw.py`
 * (function `drain_stray_profraw` in `scripts/versions/lib/repository.py`);
 * this global setup shells out to it so every consumer shares one
 * implementation. A profraw outside `target/` proves the coverage chain did
 * not take effect, so the run deletes the strays and fails.
 *
 * The scan root is this project (`typescript/`): whoever produces the file
 * cleans it. Requires `python3` on PATH (preinstalled on CI runners; on
 * Windows locally, install Python).
 */

import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const REPO_ROOT = fileURLToPath(new URL("../..", import.meta.url));
const CLI = "scripts/run/clean_stray_profraw.py";

function drainAndReport(phase: string): void {
  const proc = spawnSync("python3", [CLI, "typescript"], {
    cwd: REPO_ROOT,
    encoding: "utf8",
  });
  if (proc.error) {
    process.stderr.write(
      `stray-profraw guard could not run python3 (${proc.error.message}) — ` +
        `install python3 so ${CLI} can execute\n`,
    );
    process.exitCode = 1;
    return;
  }
  if (proc.status === 0) {
    return;
  }
  process.stderr.write(`${phase}: ${proc.stderr}`);
  process.exitCode = 1;
}

export async function setup(): Promise<() => void> {
  drainAndReport("pre-test");
  return () => {
    drainAndReport("post-test");
  };
}
