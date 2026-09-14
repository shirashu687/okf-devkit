import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import assert from "node:assert/strict";

export const repo = fileURLToPath(new URL("../../", import.meta.url));
export const cli = path.join(repo, "node/cli.mjs");
export const python =
  process.env.OKF_TEST_PYTHON ||
  path.join(
    repo,
    process.platform === "win32"
      ? ".venv/Scripts/python.exe"
      : ".venv/bin/python",
  );
export function runHook(root, env = process.env) {
  const windows = process.platform === "win32";
  const executable = windows
    ? path.join(
        process.env.SystemRoot,
        "System32/WindowsPowerShell/v1.0/powershell.exe",
      )
    : "/bin/sh";
  const args = windows
    ? [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        path.join(root, ".okf/hooks/render_hook.ps1"),
      ]
    : [path.join(root, ".okf/hooks/render_hook.sh")];
  return spawnSync(executable, args, {
    cwd: root,
    env,
    encoding: "utf8",
    windowsHide: true,
    timeout: 20000,
  });
}
export function temp(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "okf node "));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}
export function run(root, args, options = {}) {
  const { runtime = "node", env = {}, ...other } = options;
  const result = spawnSync(
    runtime === "python" ? python : process.execPath,
    runtime === "python"
      ? ["-m", "okf_devkit.cli", "--root", root, ...args]
      : [cli, "--root", root, ...args],
    {
      cwd: root,
      encoding: "utf8",
      windowsHide: true,
      timeout: 20000,
      env: { ...process.env, PYTHONIOENCODING: "utf-8", ...env },
      ...other,
    },
  );
  // Console newline conventions differ on Windows; generated files are compared untouched.
  for (const key of ["stdout", "stderr"])
    if (result[key]) result[key] = result[key].replaceAll("\r\n", "\n");
  return result;
}
export function ok(result) {
  assert.equal(
    result.status,
    0,
    `${result.error || ""}\n${result.stdout}\n${result.stderr}`,
  );
  return result.stdout;
}
export function put(root, file, text) {
  const target = path.join(root, file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, text);
  return target;
}
export function git(root, ...args) {
  const r = spawnSync("git", args, {
    cwd: root,
    encoding: "utf8",
    windowsHide: true,
    env: {
      ...process.env,
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_AUTHOR_NAME: "OKF Test",
      GIT_AUTHOR_EMAIL: "test@example.invalid",
      GIT_COMMITTER_NAME: "OKF Test",
      GIT_COMMITTER_EMAIL: "test@example.invalid",
      GIT_AUTHOR_DATE: "2026-01-02T12:00:00+00:00",
      GIT_COMMITTER_DATE: "2026-01-02T12:00:00+00:00",
    },
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout.trim();
}
export function init(root, runtime = "node") {
  git(root, "init", "-q");
  ok(
    run(root, ["init", "--site-name", "Test Site", "--layer", "api=src/**"], {
      runtime,
    }),
  );
}
export function snapshot(root, prefix = "docs") {
  const out = {};
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else
        out[path.relative(root, p).replaceAll("\\", "/")] = fs.readFileSync(
          p,
          "utf8",
        );
    }
  };
  walk(path.join(root, prefix));
  return out;
}
export const document = (extra = "", body = "# Example\n\nBody.\n") =>
  `---\ntype: Reference\ntitle: Example\ndescription: One sentence.\nlayer: api\nstatus: stable\ngenerated:\n  by: process:test\n  at: "2026-01-01T00:00:00Z"\ncode_globs: [src/**]\n${extra}---\n\n${body}`;
