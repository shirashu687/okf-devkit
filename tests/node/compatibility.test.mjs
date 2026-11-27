import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import YAML from "yaml";
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
  for (const dir of [".okf", ".claude", ".codex", ".github"])
    assert.deepEqual(snapshot(js, dir), snapshot(py, dir), dir);
  assert.equal(fs.readFileSync(path.join(js, ".gitignore"), "utf8"),
    fs.readFileSync(path.join(py, ".gitignore"), "utf8"));
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
      "--code-globs",
      "src/**",
    ],
  ]) {
    ok(run(py, args, { runtime: "python" }));
    ok(run(js, args));
  }
  assert.deepEqual(normalized(snapshot(js)), normalized(snapshot(py)));
});
test("both runtimes preserve existing agent settings, other hooks and ignore rules even with force", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    git(root, "init", "-q");
    const files = [".claude/settings.json", ".codex/hooks.json", ".github/hooks/okf-render.json", ".github/hooks/other.json", ".gitignore"];
    for (const file of files) put(root, file, "user content\n");
    for (const force of [false, true]) {
      const output = ok(run(root, ["init", ...(force ? ["--force"] : [])], {runtime}));
      for (const file of files) assert.equal(fs.readFileSync(path.join(root, file), "utf8"), "user content\n", file);
      assert.match(output, /既存のエージェント設定は保持/);
      assert.match(output, /既存の .gitignore は保持/);
    }
  }
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
    const backlog = ok(run(root, ["new", "backlog", "--title", "todo item"])).trim();
    put(root, backlog, fs.readFileSync(path.join(root, backlog), "utf8").replace(/<[^<>\n]+>/g, "Fixture content"));
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

test("both CLIs select hooks, render the chosen runner and compare scaffold read-only", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    git(root, "init", "-q");
    put(root, "package.json", '{"private":true}\n');
    put(root, "node_modules/fixture/index.js", "fixture\n");
    put(root, "src/app.ts", "fixture\n");
    assert.match(ok(run(root, ["--version"], {runtime})), /^okf-devkit \d+\.\d+\.\d+/);
    const selected = ["--agent", "claude,codex", "--runner", "pnpm run okf"];
    const output = ok(run(root, ["init", "--bundle-root", "knowledge", "--site-name", "Example",
      "--layer", "app=src/**:appClient", ...selected], {runtime}));
    assert.match(output, /pnpm run okf index --write/);
    assert.match(fs.readFileSync(path.join(root, "knowledge/AGENTS.md"), "utf8"), /pnpm run okf lint/);
    assert.match(fs.readFileSync(path.join(root, "knowledge/_templates/reference.md"), "utf8"), /layer: <app \| shared>/);
    assert.match(fs.readFileSync(path.join(root, ".gitignore"), "utf8"), /^\/node_modules\/$/m);
    const claude = JSON.parse(fs.readFileSync(path.join(root, ".claude/settings.json"), "utf8"));
    assert.equal(claude.hooks.Stop[0].hooks[0].shell, process.platform === "win32" ? "powershell" : "bash");
    assert.equal(fs.existsSync(path.join(root, ".github/hooks/okf-render.json")), false);
    assert.match(ok(run(root, ["upgrade", "--check", ...selected], {runtime})), /一致: knowledge\/AGENTS\.md/);
    put(root, "knowledge/AGENTS.md", "Maintainer content\n");
    put(root, "knowledge/log.html", "Legacy HTML candidate\n");
    fs.unlinkSync(path.join(root, ".codex/hooks.json"));
    const before = snapshot(root, "knowledge");
    const diff = ok(run(root, ["upgrade", "--check", ...selected], {runtime}));
    assert.match(diff, /差分あり（手動確認）: knowledge\/AGENTS\.md/);
    assert.match(diff, /追加候補: \.codex\/hooks\.json/);
    const doctor = ok(run(root, ["doctor"], {runtime}));
    assert.match(doctor, /layer_map app \(src\/\*\*\): 1 件一致/);
    assert.match(doctor, /hook claude .*登録あり/);
    assert.match(doctor, /Git 除外 node_modules\/: 除外済み/);
    assert.match(doctor, /knowledge\/log\.html/);
    assert.deepEqual(snapshot(root, "knowledge"), before);
    assert.equal(fs.existsSync(path.join(root, ".codex/hooks.json")), false);

    const disabled = temp(t);
    ok(run(disabled, ["init", "--agent", "none"], {runtime}));
    assert.equal(fs.existsSync(path.join(disabled, ".okf/hooks/render_hook.sh")), true);
    assert.equal(fs.existsSync(path.join(disabled, ".okf/hooks/agent_stop.sh")), false);
    assert.equal(fs.existsSync(path.join(disabled, ".claude/settings.json")), false);
    assert.match(run(disabled, ["doctor", "--"], {runtime}).stderr, /--/);
  }
});

test("both CLIs handle forwarded options and optional index updates", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    init(root, runtime);
    put(root, "src/app.ts", "code\n");
    put(root, "docs/index.md", "# Root\n\nMaintainer introduction\n");
    const options = ["--title", "日本語 API", "--layer", "api", "--type", "Project Overview",
      "--code-globs", "src/app.ts", "--dir", "nested", "--index"];
    assert.match(run(root, ["new", "doc", "--", ...options], {runtime}).stderr, /--slug/);
    const newFile = path.join(root, "docs/api/nested/api.md");
    assert.equal(fs.existsSync(newFile), true);
    assert.match(fs.readFileSync(path.join(root, "docs/index.md"), "utf8"), /Maintainer introduction/);
    ok(run(root, ["new", "backlog", "--", "--title", "日本語", "--index"], {runtime}));
    ok(run(root, ["index", "--check"], {runtime}));
    assert.equal(run(root, ["new", "doc", "--", "--", "--title", "Bad"], {runtime}).status, 2);
    assert.equal(run(root, ["new", "doc", "--title", "--"], {runtime}).status, 2);
    assert.match(ok(run(root, ["affected", "--", "--paths", "src/app.ts"], {runtime})), /docs\/api\/nested\/api\.md/);
    put(root, "docs/api/index.md", "# Broken\n\n<!-- okf:auto:start -->\n");
    const partial = run(root, ["new", "backlog", "--title", "Recovery", "--index"], {runtime});
    assert.equal(partial.status, 1);
    assert.match(partial.stderr, /文書は作成済み.*index --write/);
    assert.equal(fs.existsSync(path.join(root, "docs/backlog/B-0002-recovery.md")), true);
  }
});

test("both CLIs prune code glob directories and flag only known placeholders", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    init(root, runtime);
    put(root, "src/app/node_modules/pkg/vendored.ts", "code\n");
    put(root, "src/app/dist/bundled.ts", "code\n");
    put(root, "src/app/local/generated.ts", "code\n");
    fs.symlinkSync(path.join(root, "src", "app"), path.join(root, "src", "app", "cycle"), "junction");
    const config = path.join(root, "okf.yml");
    fs.appendFileSync(config, "\ncode_glob_exclude: [src/app/local/**]\nexclude: [agents, agents/**]\n");
    put(root, "docs/agents/tool.md", "# Tool config without frontmatter\n");
    put(root, "docs/api/explicit.md", document().replace("src/**", "src/app/dist/**"));
    put(root, "docs/api/broad.md", document());
    put(root, "docs/api/known.md", document().replace("description: One sentence.", "description: <一文で何の一覧かを説明する。>"));
    put(root, "docs/api/examples.md", document("", "# Example\n\n<https://example.com> <div>HTML</div> `<path>`\n\n~~~md\n<一文で何の一覧かを説明する。>\n~~~\n").replace("src/**", "src/app/dist/**"));
    ok(run(root, ["index", "--write"], {runtime}));
    const result = run(root, ["lint", "--strict"], {runtime});
    assert.equal(result.status, 1);
    assert.match(result.stdout, /docs\/api\/known\.md:\d+ warn L15/);
    assert.match(result.stdout, /docs\/api\/broad\.md:\d+ warn L10.*走査除外/);
    assert.doesNotMatch(result.stdout, /docs\/api\/(?:examples|explicit)\.md:|docs\/agents\//);
    assert.equal(fs.existsSync(path.join(root, "docs/agents/index.md")), false);
  }
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


test("Python and Node render identical readonly backlog progress sections", t => {
  const py = temp(t), js = temp(t);
  init(py, "python"); init(js);
  for (const root of [py, js]) put(root, "docs/index.md", "# Docs\n");
  for (const root of [py, js]) {
    const config = fs.readFileSync(path.join(root, "okf.yml"), "utf8");
    put(root, "okf.yml", config + "\nbacklog:\n  dir: work/tasks\n  states: [queued, doing, done, dropped]\n  state_order: [done, queued, doing, dropped]\n  priorities: [urgent]\n  efforts: [small]\n");
    put(root, "docs/work/tasks/index.md", "# Tasks\n");
    for (const [index, state] of ["queued", "doing", "done", "dropped", "unexpected", null].entries())
      put(root, `docs/work/tasks/B-000${index + 1}-x #%.md`, document((state ? `state: ${state}\n` : "")+"priority: urgent\neffort: small\n").replace("type: Reference", "type: Backlog Item"));
  }
  ok(run(py, ["render", "--output", "_site"], {runtime: "python"}));
  ok(run(js, ["render", "--output", "_site"]));
  for (const file of ["index.html", "work/tasks/index.html"]) {
    const summary = root => fs.readFileSync(path.join(root, "_site", file), "utf8").split('<section class="backlog-progress"')[1].split('</section>')[0];
    assert.equal(summary(py), summary(js));
  }
});


test("Python and Node hierarchical nav and source metadata remain identical", t => {
  const py=temp(t),js=temp(t);init(py,"python");init(js);
  for (const root of [py,js]) {
    const config=YAML.parse(fs.readFileSync(path.join(root,"okf.yml"),"utf8"));
    config.layers=["preferred","secondary"];config.layer_dirs={preferred:"z-team",secondary:"a-team"};
    put(root,"okf.yml",YAML.stringify(config));
    put(root,"docs/index.md","# Docs\n");
    put(root,"docs/z-team/deep/a #%.md",document());put(root,"docs/a-team/b.md",document());
  }
  ok(run(py,["render","--output","_site"],{runtime:"python"}));ok(run(js,["render","--output","_site"]));
  const read=root=>fs.readFileSync(path.join(root,"_site/z-team/deep/a #%.html"),"utf8");
  const nav=text=>text.split('<nav class="site-nav"')[1].split('</nav>')[0];
  const source=text=>text.split('<p class="source-meta">')[1].split('</p>')[0];
  assert.equal(nav(read(py)),nav(read(js)));assert.equal(source(read(py)),source(read(js)));
});

test("default render output and explicit legacy layout agree across runtimes", (t) => {
  const root = temp(t);
  init(root);
  ok(run(root, ["index", "--write"]));
  for (const [args, output] of [[[], "_site"], [["--output", "docs"], "docs"]]) {
    ok(run(root, ["render", ...args], { runtime: "python" }));
    const golden = snapshot(root, output);
    ok(run(root, ["render", ...args]));
    assert.deepEqual(snapshot(root, output), golden);
    assert.equal(fs.existsSync(path.join(root, output, "index.html")), true);
  }
});

test("command help has Python/Node option and purpose parity without writes", (t) => {
  const root = temp(t);
  init(root);
  ok(run(root, ["index", "--write"]));
  ok(run(root, ["render"]));
  const capture = () => {
    const files = {};
    const visit = (dir) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.name === ".git") continue;
        const file = path.join(dir, entry.name);
        if (entry.isDirectory()) visit(file);
        else files[path.relative(root, file)] = fs.readFileSync(file).toString("base64");
      }
    };
    visit(root);
    return files;
  };
  const before = capture();
  const commands = [[], ["init"], ["index"], ["log"], ["lint"], ["stale"],
    ["affected"], ["new"], ["new", "doc"], ["new", "backlog"], ["status"], ["render"], ["sync"]];
  const flags = text => [...new Set(text.match(/--[a-z][a-z-]*/g))].sort();
  for (const command of commands) {
    const args = ["--config", path.join(root, "does-not-exist.yml"), ...command, "--help"];
    const py = ok(run(root, args, { runtime: "python" }));
    const js = ok(run(root, args));
    assert.deepEqual(flags(js), flags(py), command.join(" "));
    const purpose = py.split("\n\n")[1].trim();
    assert.ok(js.includes(purpose), command.join(" "));
    if (command.length) assert.match(js, /例:/);
    assert.deepEqual(capture(), before);
  }
});
