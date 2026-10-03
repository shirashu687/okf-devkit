import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import {
  Bundle,
  parseYaml,
  scalar,
  matches,
  timestamp,
  write,
} from "../../node/core.mjs";
import {
  cli,
  document,
  git,
  init,
  ok,
  put,
  repo,
  run,
  snapshot,
  temp,
} from "./helpers.mjs";

test("Node alone initializes, indexes, lints, creates docs, reports and renders", (t) => {
  const root = temp(t),
    noPython = { env: { PATH: "" } };
  ok(run(root, ["init", "--layer", "api=src/**"], noPython));
  put(root, "src/main.js", "export const n = 1;");
  ok(
    run(
      root,
      ["new", "backlog", "--title", "Node support", "--slug", "node-support"],
      noPython,
    ),
  );
  ok(
    run(
      root,
      [
        "new",
        "doc",
        "--title",
        "Example",
        "--layer",
        "api",
        "--type",
        "Reference",
        "--code-globs",
        "src/**",
        "--slug",
        "example",
      ],
      noPython,
    ),
  );
  put(root, "docs/api/example.md", document());
  ok(run(root, ["index", "--write"], noPython));
  ok(run(root, ["index", "--check"], noPython));
  ok(run(root, ["lint", "--strict"], noPython));
  assert.equal(
    JSON.parse(ok(run(root, ["status", "--format", "json"], noPython))).total,
    1,
  );
  assert.match(
    ok(run(root, ["affected", "--paths", "src/main.js"], noPython)),
    /docs\/api\/example.md/,
  );
  assert.equal(
    JSON.parse(ok(run(root, ["stale", "--format", "json"], noPython))).some(
      (r) => r.kind === "unverified",
    ),
    true,
  );
  assert.equal(ok(run(root, ["render", "--hook"], noPython)).trim(), "{}");
  const before = snapshot(root),
    mtime = fs.statSync(path.join(root, "docs/index.html")).mtimeMs;
  ok(run(root, ["render", "--hook"], noPython));
  assert.deepEqual(snapshot(root), before);
  assert.equal(fs.statSync(path.join(root, "docs/index.html")).mtimeMs, mtime);
});
test("index preflights every marker and never partially writes", (t) => {
  const root = temp(t);
  init(root);
  ok(run(root, ["index", "--write"]));
  const index = path.join(root, "docs/api/index.md");
  fs.appendFileSync(index, "\n<!-- okf:auto:start -->\n");
  put(root, "docs/example.md", document());
  const before = snapshot(root);
  assert.equal(run(root, ["index", "--write"]).status, 1);
  assert.deepEqual(snapshot(root), before);
  assert.equal(run(root, ["lint"]).status, 1);
});
test("log baseline, commit routing, Unicode rename and idempotence", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/旧.js", "old");
  git(root, "add", ".");
  git(root, "commit", "-qm", "feat: first");
  git(root, "mv", "src/旧.js", "src/新.js");
  git(root, "commit", "-qam", "feat: rename (#12)");
  ok(run(root, ["log", "--write"]));
  const log = fs.readFileSync(path.join(root, "docs/api/log.md"), "utf8");
  assert.match(log, /rename/);
  assert.match(log, /first/);
  ok(run(root, ["log", "--write"]));
  assert.equal(
    fs.readFileSync(path.join(root, "docs/api/log.md"), "utf8"),
    log,
  );
  fs.appendFileSync(path.join(root, "docs/api/log.md"), "- Manual entry.\n");
  const before = snapshot(root);
  assert.equal(run(root, ["log", "--write"]).status, 1);
  assert.deepEqual(snapshot(root), before);
  assert.equal(run(root, ["log", "--range", "no-such-ref"]).status, 1);
});
test("resource globs support explicit dot files without traversing unrelated trees", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/main.js", "main");
  put(root, "src/deep/other.js", "other");
  put(root, "src/.hidden.js", "hidden");
  put(root, "src/.hidden/private.js", "private");
  const bundle = new Bundle(root);
  assert.deepEqual(bundle.resources("src/*.js"), ["src/main.js"]);
  assert.deepEqual(bundle.resources("src/**/*.js"), [
    "src/deep/other.js",
    "src/main.js",
  ]);
  assert.deepEqual(bundle.resources("src/.*.js"), ["src/.hidden.js"]);
  assert.deepEqual(bundle.resources("src/.hidden/*.js"), [
    "src/.hidden/private.js",
  ]);
});

test("YAML 1.1 booleans, dates, nested metadata and safe scalar quoting", () => {
  assert.deepEqual(
    parseYaml("yes: no\nd: 2026-01-01\nt: 2026-01-01T00:00:00Z\ntags: [a, b]"),
    {
      true: false,
      d: "2026-01-01",
      t: "2026-01-01T00:00:00Z",
      tags: ["a", "b"],
    },
  );
  for (const value of [
    "true",
    "2026-01-01",
    "12",
    "a: b",
    'say "hi"',
    "abc",
    "C:\\x",
    "quoted # text",
  ])
    assert.equal(parseYaml(`title: ${scalar(value)}`).title, value);
  assert.throws(() => parseYaml("x: [unclosed"));
  assert.throws(() => parseYaml("x: &loop [*loop]"));
  assert.throws(() => parseYaml("at: 2026-02-30T00:00:00Z"));
  assert.throws(() => parseYaml("at: 2026-01-01T24:00:00Z"));
  assert.equal(timestamp("2026-01-01T24:00:00Z"), null);
  assert.equal(matches("src/a/b.js", "src/**/*.js"), true);
  assert.equal(matches("src/a.js", "src/**/*.js"), true);
  assert.equal(matches("src/a.js", "src/[!b].js"), true);
});
test("new and init reject traversal and do not overwrite files", (t) => {
  const root = temp(t);
  init(root);
  const before = snapshot(root);
  for (const args of [
    [
      "new",
      "doc",
      "--title",
      "X",
      "--layer",
      "api",
      "--type",
      "Reference",
      "--code-globs",
      "src/**",
      "--dir",
      "../escape",
    ],
    ["new", "backlog", "--title", "X", "--slug", "../escape"],
    ["init", "--bundle-root", "../outside"],
    ["init", "--layer", "x=src/**:..\\escape"],
  ])
    assert.notEqual(run(root, args).status, 0);
  assert.deepEqual(snapshot(root), before);
  ok(
    run(root, [
      "new",
      "doc",
      "--title",
      "X",
      "--layer",
      "api",
      "--type",
      "Reference",
      "--code-globs",
      "src/**",
    ]),
  );
  assert.equal(
    run(root, [
      "new",
      "doc",
      "--title",
      "X",
      "--layer",
      "api",
      "--type",
      "Reference",
      "--code-globs",
      "src/**",
    ]).status,
    1,
  );
  assert.equal(run(root, ["render", "--output", "../outside"]).status, 1);
});
test("render links, escaped HTML, Mermaid, owned cleanup and check mode", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/main.js", "ok");
  put(
    root,
    "docs/api/example.md",
    document(
      "related: [/api/other.md]\n",
      "# Example\n\n[Other](other.md#heading)\n\n<script>alert(1)</script>\n\n```mermaid\ngraph TD; A-->B\n```\n\n## Heading\n## Heading\n## Three\n",
    ),
  );
  put(root, "docs/api/other.md", document("", "# Other\n"));
  ok(run(root, ["index", "--write"]));
  const before = snapshot(root);
  ok(run(root, ["render", "--check"]));
  assert.deepEqual(snapshot(root), before);
  ok(run(root, ["render", "--output", "_site"]));
  const html = fs.readFileSync(
    path.join(root, "_site/api/example.html"),
    "utf8",
  );
  assert.match(html, /other.html#heading/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /class="mermaid"/);
  assert.match(html, /id="heading-2"/);
  put(root, "_site/user.html", "user owned");
  fs.unlinkSync(path.join(root, "docs/api/other.md"));
  ok(run(root, ["render", "--output", "_site"]));
  assert.equal(fs.existsSync(path.join(root, "_site/api/other.html")), false);
  assert.equal(
    fs.readFileSync(path.join(root, "_site/user.html"), "utf8"),
    "user owned",
  );
  assert.equal(
    run(root, ["render", "--hook", "--output", "../outside"]).status,
    1,
  );
});
test("gate returns 2 once per fingerprint and fails closed for operational errors", (t) => {
  const root = temp(t);
  init(root);
  put(root, "docs/bad.md", "# Missing metadata");
  const args = ["sync", "--gate", "--session-id", "native-test"];
  assert.equal(run(root, args).status, 2);
  assert.equal(run(root, args).status, 0);
  put(root, "docs/another.md", "# Also missing metadata");
  assert.equal(run(root, args).status, 2);
  assert.equal(
    run(root, ["sync", "--gate", "--config", "missing.yml"]).status,
    2,
  );
});
test("gate stdin without EOF is bounded", async (t) => {
  const root = temp(t);
  init(root);
  put(root, "docs/bad.md", "# Missing metadata");
  const start = Date.now();
  const result = await new Promise((resolve, reject) => {
    const child = spawn(
      process.execPath,
      [cli, "--root", root, "sync", "--gate"],
      {
        stdio: ["pipe", "ignore", "pipe"],
        windowsHide: true,
        env: { ...process.env, CLAUDE_SESSION_ID: "", OKF_SESSION_ID: "" },
      },
    );
    const timeout = setTimeout(() => {
      child.kill();
      reject(new Error("stdin timeout"));
    }, 10000);
    child.on("error", reject);
    child.on("exit", (code) => {
      clearTimeout(timeout);
      resolve(code);
    });
    child.stdin.write("{");
  });
  assert.equal(result, 2);
  assert.ok(Date.now() - start < 9000);
});
test("atomic write leaves original content after replacement failure", (t) => {
  const root = temp(t),
    dir = put(root, "target/file", "original");
  assert.throws(() => write(path.dirname(dir), "replacement"));
  assert.equal(fs.readFileSync(dir, "utf8"), "original");
  assert.equal(
    fs.readdirSync(root).some((p) => p.endsWith(".okftmp")),
    false,
  );
});
test("local npm hook resolves Node with Python removed from PATH", (t) => {
  const root = temp(t);
  init(root);
  ok(run(root, ["index", "--write"]));
  // A junction/symlink emulates a locally installed npm package without copying dependencies.
  fs.mkdirSync(path.join(root, "node_modules"));
  fs.symlinkSync(
    repo,
    path.join(root, "node_modules/okf-devkit"),
    process.platform === "win32" ? "junction" : "dir",
  );
  const gitPath = spawnSync(
    process.platform === "win32" ? "where.exe" : "which",
    ["git"],
    { encoding: "utf8" },
  )
    .stdout.trim()
    .split(/\r?\n/)[0];
  const env = {
    ...process.env,
    PATH: [path.dirname(process.execPath), path.dirname(gitPath)].join(
      path.delimiter,
    ),
  };
  let hook;
  if (process.platform === "win32")
    hook = spawnSync(
      path.join(
        process.env.SystemRoot,
        "System32/WindowsPowerShell/v1.0/powershell.exe",
      ),
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        path.join(root, ".okf/hooks/render_hook.ps1"),
      ],
      { cwd: root, env, encoding: "utf8", windowsHide: true, timeout: 20000 },
    );
  else
    hook = spawnSync(
      "/bin/sh",
      [path.join(root, ".okf/hooks/render_hook.sh")],
      { cwd: root, env, encoding: "utf8", timeout: 20000 },
    );
  assert.equal(hook.status, 0, hook.stderr);
  assert.equal(hook.stdout.trim(), "{}");
});

function progressFixture(root) {
  const config = fs.readFileSync(path.join(root, "okf.yml"), "utf8");
  put(root, "okf.yml", config + "\nbacklog:\n  dir: work/tasks\n  states: [queued, doing, done, dropped]\n  state_order: [done, queued, doing, dropped]\n");
  put(root, "docs/work/tasks/index.md", "# Tasks\n");
  for (const [index, state] of ["queued", "doing", "done", "dropped", "unexpected", null].entries()) {
    put(root, `docs/work/tasks/B-000${index + 1}-x #%.md`, document(state ? `state: ${state}\n` : "").replace("type: Reference", "type: Backlog Item").replace("title: Example", 'title: "Task <safe>"'));
  }
  put(root, "docs/work/tasks/reference.md", document());
  put(root, "docs/work/tasks/nested/B-9999.md", document("state: queued\n").replace("type: Reference", "type: Backlog Item"));
}
const summary = html => html.split('<section class="backlog-progress"')[1].split('</section>')[0];

test("backlog progress honors configuration, source links, empty and regeneration", t => {
  const root = temp(t); init(root);
  put(root, "docs/index.md", "# Docs\n");
  ok(run(root, ["render", "--output", "_site"]));
  assert.match(fs.readFileSync(path.join(root, "_site/index.html"), "utf8"), /Backlog Item はありません。/);
  progressFixture(root);
  const before = snapshot(root);
  ok(run(root, ["render", "--output", "_site"]));
  assert.deepEqual(snapshot(root), before);
  const read = file => fs.readFileSync(path.join(root, file), "utf8");
  let view = summary(read("_site/index.html"));
  assert.match(view, /全 6 件/);
  for (const state of ["queued", "doing", "done", "dropped", "unexpected", "未設定"]) assert.ok(view.includes(`>${state}</span> 1 件`));
  assert.ok(view.indexOf(">done</span>") < view.indexOf(">queued</span>"));
  assert.ok(view.includes('href="work/tasks/B-0001-x%20%23%25.html"'));
  assert.ok(view.includes("Task &lt;safe&gt;"));
  assert.ok(summary(read("_site/work/tasks/index.html")).includes('href="B-0001-x%20%23%25.html"'));
  put(root, "docs/work/tasks/B-0001-x #%.md", read("docs/work/tasks/B-0001-x #%.md").replace("state: queued", "state: done"));
  ok(run(root, ["render", "--output", "_site"]));
  view = summary(read("_site/index.html"));
  assert.ok(view.includes('>queued</span> 0 件'));
  assert.ok(view.includes('>done</span> 2 件'));
});


test("new doc requires code evidence and creates lint-clean frontmatter", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/main.js", "export const n = 1;");
  for (const type of ["Project Overview", "Architecture", "Reference", "How-To"])
    assert.match(run(root, ["new", "doc", "--title", "Missing", "--layer", "api", "--type", type, "--slug", "missing"]).stderr, /--code-globs/);
  assert.equal(fs.existsSync(path.join(root, "docs/api/missing.md")), false);
  ok(run(root, ["new", "doc", "--title", "API \\1", "--layer", "api", "--type", "Reference", "--slug", "api", "--code-globs", "src/*.js", "src/main.js"]));
  const text = fs.readFileSync(path.join(root, "docs/api/api.md"), "utf8");
  const fm = parseYaml(text.split("---")[1]);
  assert.deepEqual(fm.code_globs, ["src/*.js", "src/main.js"]);
  assert.deepEqual(fm.related, []);
  assert.match(text, /# API \\1\n\n/);
  ok(run(root, ["new", "doc", "--title", "Terms", "--layer", "shared", "--type", "Glossary"]));
  ok(run(root, ["index", "--write"]));
  ok(run(root, ["lint", "--strict"]));
});

test("init shared log matches config and log write reuses it", (t) => {
  for (const bundleRoot of ["docs", "knowledge"]) {
    const root = temp(t);
    git(root, "init", "-q");
    ok(run(root, ["init", "--bundle-root", bundleRoot, "--layer", "api=src/**"]));
    const bundle = new Bundle(root);
    assert.equal(bundle.logPath("shared"), path.join(root, bundleRoot, "log.md"));
    assert.equal(fs.existsSync(bundle.logPath("shared")), true);
    assert.equal(fs.existsSync(path.join(root, bundleRoot, "project/log.md")), false);
    put(root, "README.md", "Shared source\n");
    git(root, "add", ".");
    git(root, "commit", "-qm", "Update shared source");
    const before = fs.readdirSync(path.join(root, bundleRoot), { recursive: true }).filter((p) => p === "log.md" || p.endsWith(`${path.sep}log.md`));
    ok(run(root, ["log", "--layer", "shared", "--write"]));
    assert.deepEqual(fs.readdirSync(path.join(root, bundleRoot), { recursive: true }).filter((p) => p === "log.md" || p.endsWith(`${path.sep}log.md`)), before);
    assert.match(fs.readFileSync(bundle.logPath("shared"), "utf8"), /Update shared source/);
  }
});
