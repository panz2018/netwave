/**
 * Stray-profraw guard for the native vitest run.
 *
 * LLVM writes source-based coverage to `LLVM_PROFILE_FILE`; when that variable
 * is unset at process exit it falls back to `default_%m_%p.profraw` in the
 * process cwd. A profraw outside `target/` is therefore proof the coverage
 * chain did not take effect, and such files are never inputs to
 * `cargo llvm-cov report` — deleting them loses nothing.
 *
 * The scan root is this project (`typescript/`): whoever produces the file
 * cleans it. `cargo llvm-cov report` reads only what it registered under
 * `target/`, so anything outside those directories is debris.
 */

import { readdirSync, rmSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const SCAN_ROOT = fileURLToPath(new URL("..", import.meta.url));

/** Build outputs and dependency caches — never report inputs, never stray sites. */
const SKIP_DIRS = new Set(["target", "target-wasm", "node_modules", "dist", "coverage"]);

function findStray(dir: string, found: string[]): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) {
        findStray(full, found);
      }
    } else if (entry.name.endsWith(".profraw")) {
      found.push(relative(SCAN_ROOT, full).split(sep).join("/"));
    }
  }
  return found;
}

function drainAndReport(phase: string): void {
  const stray = findStray(SCAN_ROOT, []).sort();
  if (stray.length === 0) {
    return;
  }
  for (const rel of stray) {
    rmSync(join(SCAN_ROOT, rel));
  }
  process.stderr.write(
    `profraw outside target/ = the coverage chain did not take effect, ` +
      `so coverage numbers for this run are untrustworthy` +
      ` (${phase}: found ${stray.length}, deleted):\n` +
      `${stray.map((p) => `  ${p}`).join("\n")}\n`,
  );
  process.exitCode = 1;
}

export async function setup(): Promise<() => void> {
  drainAndReport("pre-test");
  return () => {
    drainAndReport("post-test");
  };
}
