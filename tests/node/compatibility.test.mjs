import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {
  document,
  git,
  init,
  ok,
  put,
  python,
  run,
  runHook,
  snapshot,
  temp,
} from "./helpers.mjs";

// This suite deliberately requires Python: npm test is the independent Node-only suite.
assert.ok(
  fs.existsSync(python),
  `比較用Pythonがありません。OKF_TEST_PYTHON を指定してください: ${python}`,
);
const normalize = (text) =>
  text.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/g, "<timestamp>");
const normalized = (files) =>
  Object.fromEntries(Object.entries(files).map(([k, v]) => [k, normalize(v)]));
test("existing Python install wins over a development checkout without npm dependencies", (t) => {
  const root = temp(t);
  init(root, "python");
  put(
    root,
    "node/cli.mjs",
    'throw new Error("npm dependencies are not installed");',
  );
  put(root, "src/okf_devkit/defaults.yml", "bundle_root: docs\n");
  const windows = process.platform === "win32";
  const name = windows ? "okf.exe" : "okf";
  const candidates = [
    path.join(path.dirname(python), name),
    path.join(path.dirname(python), "Scripts", name),
  ];
  const launcher = candidates.find((p) => fs.existsSync(p));
  assert.ok(
    launcher,
    "Python比較環境にpip install -e .でokfコマンドを導入してください",
  );
  const installed = path.join(
    root,
    windows ? ".venv/Scripts/okf.exe" : ".venv/bin/okf",
  );
  fs.mkdirSync(path.dirname(installed), { recursive: true });
  fs.copyFileSync(launcher, installed);
  if (!windows) fs.chmodSync(installed, 0o755);
  const hook = runHook(root);
  assert.equal(hook.status, 0, hook.stderr);
  assert.equal(hook.stdout.trim(), "{}");
});

test("init and new produce the same scaffold bytes (except generation time)", (t) => {
  const py = temp(t),
    js = temp(t);
  init(py, "python");
  init(js);
  assert.equal(
    fs.readFileSync(path.join(py, "okf.yml"), "utf8"),
    fs.readFileSync(path.join(js, "okf.yml"), "utf8"),
  );
  assert.deepEqual(normalized(snapshot(js)), normalized(snapshot(py)));
  for (const args of [
    [
      "new",
      "backlog",
      "--title",
      'API: "quoted" # note',
      "--slug",
      "quoted",
      "--priority",
      "high",
    ],
    [
      "new",
      "doc",
      "--title",
      "Design choice",
      "--layer",
      "shared",
      "--type",
      "Decision Record",
      "--dir",
      "decisions",
    ],
    [
      "new",
      "doc",
      "--title",
      "Reference",
      "--layer",
      "api",
      "--type",
      "Reference",
    ],
  ]) {
    ok(run(py, args, { runtime: "python" }));
    ok(run(js, args));
  }
  assert.deepEqual(normalized(snapshot(js)), normalized(snapshot(py)));
});
for (const style of ["relative", "bundle-absolute"])
  test(`index golden parity: ${style}, draft/deprecated/backlog/escaped paths`, (t) => {
    const root = temp(t);
    init(root);
    fs.appendFileSync(
      path.join(root, "okf.yml"),
      `\nindex:\n  link_style: ${style}\n`,
    );
    // Avoid a duplicate mapping key: replace the initial index section.
    let cfg = fs.readFileSync(path.join(root, "okf.yml"), "utf8");
    cfg = cfg.replace(/index:\n  root_heading:[^\n]+\n/, "");
    fs.writeFileSync(path.join(root, "okf.yml"), cfg);
    put(root, "src/main.js", "code");
    put(root, "docs/api/a (50%).md", document("", "# One\n"));
    put(
      root,
      "docs/api/draft.md",
      document()
        .replace("status: stable", "status: draft")
        .replace("title: Example", "title: Z draft"),
    );
    put(
      root,
      "docs/api/old.md",
      document().replace("status: stable", "status: deprecated"),
    );
    ok(run(root, ["new", "backlog", "--title", "todo item"]));
    ok(run(root, ["index", "--write"], { runtime: "python" }));
    const golden = snapshot(root);
    ok(run(root, ["index", "--check"]));
    ok(run(root, ["index", "--write"]));
    assert.deepEqual(snapshot(root), golden);
    assert.equal(
      ok(run(root, ["lint", "--strict"])),
      ok(run(root, ["lint", "--strict"], { runtime: "python" })),
    );
  });
test("Git log, affected, stale and status agree with the Python CLI", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/旧.js", "one");
  put(root, "docs/api/example.md", document());
  git(root, "add", ".");
  git(root, "commit", "-qm", "feat: first");
  const base = git(root, "rev-parse", "HEAD");
  git(root, "mv", "src/旧.js", "src/新.js");
  git(root, "commit", "-qam", "feat: rename (#42)");
  for (const args of [
    ["affected", "--base", base],
    ["stale", "--format", "json"],
    ["status", "--format", "json"],
    ["log", "--dry-run"],
  ])
    assert.equal(
      ok(run(root, args)),
      ok(run(root, args, { runtime: "python" })),
      args.join(" "),
    );
  const log = path.join(root, "docs/api/log.md"),
    original = fs.readFileSync(log, "utf8");
  ok(run(root, ["log", "--write"], { runtime: "python" }));
  const golden = fs.readFileSync(log, "utf8");
  fs.writeFileSync(log, original);
  ok(run(root, ["log", "--write"]));
  assert.equal(fs.readFileSync(log, "utf8"), golden);
});
test("L1-L14 finding rules, severity, locations and exit codes agree", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/main.js", "code");
  put(
    root,
    "docs/api/bad.md",
    document("verified: []\nsources: [bad]\nrelated: [/missing.md]\n")
      .replace("status: stable", "status: 123")
      .replace("layer: api", "layer: unknown")
      .replace("code_globs: [src/**]", "code_globs: [missing/**, 2]"),
  );
  put(root, "docs/missing.md", "# no metadata");
  ok(run(root, ["index", "--write"]));
  const py = run(root, ["lint"], { runtime: "python" }),
    js = run(root, ["lint"]);
  assert.equal(js.status, py.status);
  assert.equal(js.stdout, py.stdout);
});
test("HTML golden parity and idempotence on shared Markdown and assets", (t) => {
  const root = temp(t);
  init(root);
  put(root, "src/main.js", "code");
  put(
    root,
    "docs/api/example.md",
    document(
      "related: [/api/other.md]\n",
      '# Example\n\n[Other](/api/other.md?q=one#日本語)\n\n{{TITLE}} & <unsafe>\n\n## First\n## First\n## Third\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```mermaid\ngraph TD; A-->B\n```\n\n```js\nconst n = "one";\n```\n',
    ),
  );
  put(root, "docs/api/other.md", document("", "# Other\n\nText.\n"));
  ok(run(root, ["index", "--write"]));
  ok(run(root, ["render", "--output", "_site"], { runtime: "python" }));
  const golden = snapshot(root, "_site");
  ok(run(root, ["render", "--output", "_site"]));
  const result = snapshot(root, "_site");
  for (const [file, content] of Object.entries(golden))
    assert.equal(result[file], content, file);
  assert.deepEqual(Object.keys(result), Object.keys(golden));
  assert.match(ok(run(root, ["render", "--output", "_site"])), /書き込み 0 件/);
});
