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

test("affected only uses changes from the selected code source", (t) => {
  const root = temp(t);
  const app = temp(t);
  init(root);
  fs.appendFileSync(path.join(root, "okf.yml"), `\ncode_sources:\n  - name: app\n    path: missing-checkout\n    path_env: OKF_TEST_APP_REPO\n`);
  put(root, "docs/api/app.md", document().replace("[src/**]", '["app:src/**", "app:docs/examples/**"]'));
  put(root, "docs/api/local.md", document());
  put(root, "src/login.ts", "local login");
  put(root, "src/docs-only.ts", "tracked only in the documentation repository");
  git(root, "add", "src");

  git(app, "init", "-qb", "comparison");
  put(app, "src/login.ts", "first login");
  put(app, "src/unchanged.ts", "unchanged tracked code");
  git(app, "add", ".");
  git(app, "commit", "-qm", "initial app");
  git(app, "branch", "feature");
  put(app, "src/register.ts", "comparison only");
  git(app, "add", ".");
  git(app, "commit", "-qm", "comparison only");
  git(app, "checkout", "-q", "feature");
  put(app, "src/login.ts", "updated login");
  git(app, "commit", "-qam", "feature login");
  put(app, "src/session.ts", "staged session");
  git(app, "add", "src/session.ts");
  put(app, "docs/examples/login.ts", "untracked example");
  put(app, "README.md", "uncovered change");
  const unrelated = git(app, "commit-tree", git(app, "rev-parse", "HEAD^{tree}"), "-m", "unrelated history");

  for (const runtime of ["node", "python"]) {
    const options = { runtime, env: { OKF_TEST_APP_REPO: app } };
    const result = run(root, ["affected", "--source", "app", "--base", "comparison"], options);
    const output = ok(result);
    assert.match(output, /docs\/api\/app\.md\s+<- .*docs\/examples\/login\.ts.*src\/login\.ts.*src\/session\.ts/, `${runtime}: ${result.stderr}`);
    assert.match(output, /未カバー:[\s\S]*README\.md/);
    assert.doesNotMatch(output, /docs\/api\/local\.md|src\/register\.ts/);
    const inheritedIndex = { ...options, env: { ...options.env, GIT_INDEX_FILE: path.join(root, ".git", "index") } };
    assert.equal(ok(run(root, ["affected", "--source", "app", "--base", "comparison"], inheritedIndex)), output);
    const local = ok(run(root, ["affected", "--paths", "src/login.ts"], options));
    assert.match(local, /docs\/api\/local\.md/);
    assert.doesNotMatch(local, /docs\/api\/app\.md/);
    for (const base of ["missing-ref", unrelated]) {
      const result = run(root, ["affected", "--source", "app", "--base", base], options);
      assert.equal(ok(result), "");
      assert.match(result.stderr, /差分未確認/);
    }
    const missing = run(root, ["affected", "--source", "app", "--base", "comparison"], {
      runtime, env: { OKF_TEST_APP_REPO: "" },
    });
    assert.equal(ok(missing), "");
    assert.match(missing.stderr, /差分未確認.*チェックアウト/);
    assert.notEqual(run(root, ["affected", "--source", "app", "--paths", "src/login.ts"], options).status, 0);
  }
});

test("lint and stale distinguish unavailable code sources and unmatched patterns", (t) => {
  const root = temp(t);
  const app = path.join(root, "checkout");
  init(root);
  fs.appendFileSync(path.join(root, "okf.yml"), `\ncode_sources:\n  - name: app\n    path: checkout\n    path_env: OKF_TEST_APP_REPO\n`);
  put(app, "src/login.ts", "external login");
  git(app, "init", "-q");
  put(root, "src/login.ts", "local login");
  put(root, "docs/api/mixed.md", document("stale_after: 2020-01-01\n")
    .replace("[src/**]", '["app:src/login.ts", "src/login.ts"]'));
  put(root, "docs/api/other.md", document().replace("[src/**]", '["app:src/**"]'));
  git(root, "add", "src/login.ts");
  git(root, "commit", "-qm", "local login");
  ok(run(root, ["index", "--write"]));
  for (const runtime of ["node", "python"]) {
    const options = { runtime, env: { OKF_TEST_APP_REPO: "" } };
    assert.match(ok(run(root, ["lint", "--strict"], options)), /warn 0 件/);
    if (process.platform === "win32") {
      // Exercise an alternate spelling even on volumes without DOS short names.
      const alias = { runtime, env: { OKF_TEST_APP_REPO: path.toNamespacedPath(app) } };
      assert.match(ok(run(root, ["lint", "--strict"], alias)), /warn 0 件/);
    }
    const missing = { runtime, env: { OKF_TEST_APP_REPO: path.join(root, "missing") } };
    const warnings = ok(run(root, ["lint"], missing));
    assert.equal((warnings.match(/チェックアウトが見つかりません/g) || []).length, 1);
    assert.doesNotMatch(warnings, /マッチするファイルがありません/);
    assert.equal(run(root, ["lint", "--strict"], missing).status, 1);
    assert.match(ok(run(root, ["lint"], { runtime, env: { OKF_TEST_APP_REPO: path.join(app, "src") } })), /作業ツリールート/);
    const stale = JSON.parse(ok(run(root, ["stale", "--format", "json"], missing)));
    const mixed = stale.filter(({ path }) => path.endsWith("/mixed.md"));
    assert.ok(mixed.some(({ kind, level }) => kind === "external-unverified" && level === "info"));
    assert.ok(mixed.some(({ kind }) => kind === "outdated"));
    assert.ok(mixed.some(({ kind }) => kind === "expired"));
    assert.ok(!stale.some(({ kind }) => kind === "orphan"));
  }

  put(root, "docs/api/mismatch.md", document()
    .replace("[src/**]", '["app:src/missing.ts", "appp:src/login.ts", "app:../src/login.ts"]'));
  ok(run(root, ["index", "--write"]));
  for (const runtime of ["node", "python"]) {
    const output = ok(run(root, ["lint"], { runtime, env: { OKF_TEST_APP_REPO: "" } }));
    assert.match(output, /app:src\/missing\.ts.*マッチするファイルがありません/);
    assert.match(output, /appp.*登録されていません/);
    assert.match(output, /app:\.\.\/src\/login\.ts.*相対/);
  }
});

test("sync reports a missing local code glob once and standalone checks keep their diagnostics", async (t) => {
  for (const runtime of ["node", "python"]) {
    for (const version of ["0.2", "0.3"]) {
      await t.test(`${runtime} OKF ${version}`, (t) => {
        const root = temp(t);
        git(root, "init", "-q");
        put(root, "okf.yml", `bundle_root: docs\nlayers: [api]\nindex:\n  okf_version: "${version}"\n`);
        const verified = 'verified: [{by: "human:reviewer", at: "2026-01-01T00:00:00Z"}]\n';
        const concept = (name, globs, extra = "") =>
          put(root, `docs/api/${name}.md`, document(extra).replace("[src/**]", globs));
        concept("sample", "[src/missing.ts]", verified);
        const options = { runtime };
        const l10 = /^docs\/api\/sample\.md:\d+ warn L10 `code_globs: src\/missing\.ts`.*$/gm;
        const orphan = /^docs\/api\/sample\.md warn orphan .*src\/missing\.ts.*$/m;
        const sync = ok(run(root, ["sync"], options));
        if (version === "0.3")
          assert.match(fs.readFileSync(path.join(root, "docs/index.md"), "utf8"), /okf_version: "0\.3"/);
        assert.equal(sync.match(l10)?.length, 1);
        assert.doesNotMatch(sync, orphan);
        assert.match(sync, /== stale ==\n.*lint 欄で報告済み/);
        assert.doesNotMatch(sync, /陳腐化の兆候はありません/);

        const lintArgs = version === "0.3" ? ["lint", "--project", "--strict"] : ["lint", "--strict"];
        const lint = run(root, lintArgs, options);
        assert.equal(lint.status, 1, lint.stderr);
        assert.match(lint.stdout, l10);
        assert.match(ok(run(root, ["stale"], options)), orphan);
        assert.deepEqual(JSON.parse(ok(run(root, ["stale", "--format", "json"], options))), [{
          path: "docs/api/sample.md",
          kind: "orphan",
          level: "warn",
          message: "code_globs: src/missing.ts にマッチするファイルがありません",
        }]);

        fs.appendFileSync(path.join(root, "okf.yml"), "code_sources:\n  - name: app\n    path: checkout\n");
        const checkout = path.join(root, "checkout");
        fs.mkdirSync(checkout);
        git(checkout, "init", "-q");
        put(root, "src/current.ts", "current code");
        git(root, "add", "src/current.ts");
        git(root, "commit", "-qm", "update current code");
        concept("sample", '[src/missing.ts, src/missing.ts, src/another.ts, "app:src/missing.ts", src/current.ts, 42]',
          verified + 'stale_after: "2020-01-01T00:00:00Z"\n');
        concept("second", "[src/missing.ts]", verified);
        concept("empty", "[]");

        const mixed = run(root, ["sync"], options);
        assert.equal(mixed.status, 1, mixed.stderr);
        const localPairs = [...mixed.stdout.matchAll(/^docs\/api\/(sample|second)\.md:\d+ warn L10 `code_globs: (src\/[^`]+)`/gm)]
          .map(([, name, glob]) => `${name} ${glob}`).sort();
        assert.deepEqual(localPairs, ["sample src/another.ts", "sample src/missing.ts", "second src/missing.ts"]);
        assert.match(mixed.stdout, /sample\.md:\d+ warn L10 `code_globs: app:src\/missing\.ts`/);
        assert.match(mixed.stdout, /sample\.md:\d+ error L10 `code_globs\[6\]`/);
        assert.match(mixed.stdout, /empty\.md:\d+ warn L10 `code_globs` がありません/);
        assert.match(mixed.stdout, /lint: error 1 件 \/ warn 5 件/);
        assert.match(mixed.stdout, /sample\.md info external-unverified/);
        assert.match(mixed.stdout, /sample\.md warn expired/);
        assert.match(mixed.stdout, /sample\.md warn outdated/);
        assert.match(mixed.stdout, /empty\.md info unverified/);
        assert.doesNotMatch(mixed.stdout, / warn orphan |lint 欄で報告済み/);
        const standalone = run(root, lintArgs, options);
        assert.equal(standalone.status, 1, standalone.stderr);
        assert.equal(standalone.stdout.match(l10)?.length, 2);
        const gate = ["sync", "--gate", "--session-id", "sync-diagnostics"];
        assert.equal(run(root, gate, options).status, 2);
        ok(run(root, gate, options));
      });
    }
  }
});

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
    const manifest = JSON.parse(fs.readFileSync(new URL("../../package.json", import.meta.url), "utf8"));
    assert.equal(ok(run(root, ["--version"], {runtime})).trim(), "okf-devkit " + manifest.version);
    const selected = ["--agent", "claude,codex", "--runner", "pnpm run okf"];
    const output = ok(run(root, ["init", "--bundle-root", "knowledge", "--site-name", "Example",
      "--layer", "app=src/**:appClient", ...selected], {runtime}));
    assert.match(output, /pnpm run okf index --write/);
    assert.match(fs.readFileSync(path.join(root, "knowledge/AGENTS.md"), "utf8"), /pnpm run okf lint/);
    assert.match(fs.readFileSync(path.join(root, "knowledge/_templates/log.md"), "utf8"), /pnpm run okf log --write/);
    assert.match(fs.readFileSync(path.join(root, "knowledge/_templates/reference.md"), "utf8"), /layer: <app \| shared>/);
    assert.match(fs.readFileSync(path.join(root, ".gitignore"), "utf8"), /^\/node_modules\/$/m);
    const claude = JSON.parse(fs.readFileSync(path.join(root, ".claude/settings.json"), "utf8"));
    assert.equal(claude.hooks.Stop[0].hooks[0].shell, process.platform === "win32" ? "powershell" : "bash");
    assert.equal(fs.existsSync(path.join(root, ".github/hooks/okf-render.json")), false);
    assert.match(ok(run(root, ["upgrade", "--check", ...selected], {runtime})), /一致: knowledge\/AGENTS\.md/);
    put(root, "knowledge/AGENTS.md", "Maintainer content\n");
    put(root, "knowledge/log.html", "Legacy HTML candidate\n");
    fs.unlinkSync(path.join(root, ".codex/hooks.json"));
    put(root, ".gitignore", "/_site/*\n!/_site/index.html\n/node_modules/\n/.okf/render-backups/\n");
    const reference = path.join(root, "knowledge/_templates/reference.md");
    fs.writeFileSync(reference, fs.readFileSync(reference, "utf8")
      .replace("at: <YYYY-MM-DDTHH:MM:SSZ>", "at: custom maintainer text"));
    fs.writeFileSync(path.join(root, "knowledge/asset.bin"), Buffer.from([0, 255, 10]));
    const before = snapshot(root, ".", null);
    const diff = ok(run(root, ["upgrade", "--check", ...selected], {runtime}));
    assert.match(diff, /差分あり（手動確認）: knowledge\/AGENTS\.md/);
    assert.match(diff, /追加候補: \.codex\/hooks\.json/);
    assert.match(diff, /差分あり（手動確認）: knowledge\/_templates\/reference\.md/);
    assert.match(diff, /差分あり（手動確認）: \.gitignore/);
    const doctor = ok(run(root, ["doctor"], {runtime}));
    assert.match(doctor, /layer_map app \(src\/\*\*\): 1 件一致/);
    assert.match(doctor, /hook claude .*登録あり/);
    assert.match(doctor, /Git 除外 node_modules\/: 除外済み/);
    assert.match(doctor, /Git 除外 _site\/index\.html: 要確認/);
    assert.match(doctor, /knowledge\/log\.html/);
    assert.deepEqual(snapshot(root, ".", null), before);
    assert.equal(fs.existsSync(path.join(root, ".codex/hooks.json")), false);
    const config = path.join(root, "okf.yml");
    fs.writeFileSync(config, fs.readFileSync(config, "utf8").replace(/^    app:.*\/log\.md$/m, "    app: appClient/history.md"));
    fs.renameSync(path.join(root, "knowledge/appClient/log.md"), path.join(root, "knowledge/appClient/history.md"));
    const relocated = ok(run(root, ["upgrade", "--check", ...selected], {runtime}));
    assert.match(relocated, /一致: knowledge\/appClient\/history\.md/);
    assert.doesNotMatch(relocated, /追加候補: knowledge\/appClient\/log\.md/);
    fs.writeFileSync(config, "layers: 123\n");
    const invalid = run(root, ["doctor"], {runtime});
    assert.equal(invalid.status, 1);
    assert.match(invalid.stdout, /設定 \/ layer_map: 要確認/);
    assert.match(invalid.stdout, /hook claude .*登録あり/);
    put(root, ".claude/settings.json", '{"hooks":{"Stop":[{"hooks":{"command":"sh .okf/hooks/agent_stop.sh"}}]}}');
    put(root, "okf.yml", 'bundle_root: "."\nlayers: [app, shared]\nlayer_map: [bad]\n');
    const malformed = run(root, ["doctor"], {runtime});
    assert.match(malformed.stdout, /hook claude .*判定不能/);
    const badUpgrade = run(root, ["upgrade", "--check"], {runtime});
    assert.equal(badUpgrade.status, 1);
    assert.match(badUpgrade.stderr, /layer_map の各項目/);
    put(root, "okf.yml", 'bundle_root: "."\n');
    put(root, "AGENTS.md", "Maintainer root guide\n");
    const rootUpgrade = ok(run(root, ["upgrade", "--check"], {runtime}));
    assert.match(rootUpgrade, /差分あり（手動確認）: AGENTS\.md/);
    assert.doesNotMatch(rootUpgrade, /docs\/AGENTS|\.\/AGENTS/);
    const outside = temp(t);
    put(outside, "unrelated.html", "Outside the project\n");
    put(root, "okf.yml", "bundle_root: " + JSON.stringify(outside) + "\n");
    const outOfBounds = run(root, ["doctor"], {runtime});
    assert.equal(outOfBounds.status, 1);
    assert.match(outOfBounds.stdout, /旧出力候補: 判定不能/);
    assert.doesNotMatch(outOfBounds.stdout + outOfBounds.stderr, /unrelated\.html|Traceback/);

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
    const halfWidth = run(root, ["new", "backlog", "--", "--title", "ﾃｽﾄ API", "--index"], {runtime});
    assert.match(ok(halfWidth), /-api\.md/);
    assert.match(halfWidth.stderr, /--slug/);
    assert.equal(run(root, ["new", "backlog", "--", "--title", "-h"], {runtime}).status, 2);
    assert.equal(run(root, ["affected", "--", "--config=", "--paths", "example.py"], {runtime}).status, 2);
    ok(run(root, ["index", "--check"], {runtime}));
    assert.equal(run(root, ["new", "doc", "--", "--", "--title", "Bad"], {runtime}).status, 2);
    assert.equal(run(root, ["new", "doc", "--title", "--"], {runtime}).status, 2);
    assert.match(ok(run(root, ["affected", "--", "--paths", "src/app.ts"], {runtime})), /docs\/api\/nested\/api\.md/);
    assert.match(ok(run(root, ["affected", "--", "--root", root, "--config", path.join(root, "okf.yml"), "--paths", "src/app.ts"], {runtime})),
      /docs\/api\/nested\/api\.md/);
    put(root, "docs/api/index.md", "# Broken\n\n<!-- okf:auto:start -->\n");
    const partial = run(root, ["new", "backlog", "--title", "Recovery", "--index"], {runtime});
    assert.equal(partial.status, 1);
    assert.match(partial.stderr, /文書は作成済み.*index --write/);
    assert.equal(fs.existsSync(path.join(root, "docs/backlog/B-0003-recovery.md")), true);
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
    put(root, "docs/api/relative.md", document().replace("src/**", "./src/**"));
    put(root, "docs/api/literal.md", document().replace("src/**", "src/app/local/generated.ts"));
    put(root, "docs/api/invalid-glob.md", document().replace("src/**", "'src/app/[z-a]*'"));
    put(root, "docs/api/known.md", document().replace("description: One sentence.", "description: <一文で何の一覧かを説明する。>"));
    const prompt = fs.readFileSync(new URL("../../src/okf_devkit/scaffold/templates/architecture.md", import.meta.url), "utf8")
      .split("\n").find((line) => line.includes("`Decision Record`"));
    const prompted = document("", "# Example\n\n`multiline\ncode example`\n" + prompt + "\n")
      .replace("src/**", "src/app/dist/**");
    put(root, "docs/api/prompt.md", prompted);
    put(root, "docs/api/comment.md", document().replace("src/**", "src/app/dist/**")
      .replace("description: One sentence.", "description: One sentence. # <一文で何の一覧かを説明する。>"));
    const examples = "# Example\n\n<https://example.com> <div>HTML</div> `<path>`\n\n" +
      "> ~~~md\n> <カテゴリ名>\n> ~~~\n\n`multiline\n<カテゴリ名>`\n";
    put(root, "docs/api/examples.md", document("", examples).replace("src/**", "src/app/dist/**"));
    ok(run(root, ["index", "--write"], {runtime}));
    const result = run(root, ["lint", "--strict"], {runtime});
    assert.equal(result.status, 1);
    assert.match(result.stdout, /docs\/api\/known\.md:\d+ warn L15/);
    const promptLine = prompted.split("\n").indexOf(prompt) + 1;
    assert.ok(result.stdout.includes("docs/api/prompt.md:" + promptLine + " warn L15"));
    for (const name of ["broad", "relative", "literal", "invalid-glob"]) {
      assert.match(result.stdout, new RegExp(name + "\\.md:\\d+ warn L10.*走査除外"));
    }
    assert.doesNotMatch(result.stdout, /docs\/api\/(?:comment|examples|explicit)\.md:|docs\/agents\//);
    assert.equal(fs.existsSync(path.join(root, "docs/agents/index.md")), false);
    fs.writeFileSync(config, fs.readFileSync(config, "utf8")
      .replace("code_glob_exclude: [src/app/local/**]", "code_glob_exclude: ['src/[z-a]*']"));
    const invalid = run(root, ["lint"], {runtime});
    assert.equal(invalid.status, 1);
    assert.match(invalid.stderr, /code_glob_exclude に不正な glob/);
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

test("both CLIs preserve YAML-sensitive layer names and directories", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    ok(run(root, ["init", "--layer", "on=src/**:appClient", "--layer", "0x1=lib/**:libCode"], {runtime}));
    const config = YAML.parse(fs.readFileSync(path.join(root, "okf.yml"), "utf8"), { version: "1.1" });
    assert.deepEqual(config.log.layers, ["on", "0x1"]);
    for (const [layer, dir] of [["on", "appClient"], ["0x1", "libCode"]]) {
      assert.equal(config.log.paths[layer], dir + "/log.md");
      const relative = ok(run(root, ["new", "doc", "--layer", layer, "--type", "Glossary", "--title", "Example"], {runtime})).trim();
      assert.equal(relative, "docs/" + dir + "/example.md");
      assert.match(fs.readFileSync(path.join(root, relative), "utf8"), new RegExp('^layer: "' + layer + '"$', "m"));
    }
  }
});

test("OKF 0.3 reads core YAML concepts and preserves the root index metadata", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    init(root, runtime);
    const config = path.join(root, "okf.yml");
    fs.writeFileSync(config, fs.readFileSync(config, "utf8")
      .replace(/^index:\n/m, 'index:\n  okf_version: "0.3"\n'));
    put(root, "docs/api/sample.md", "---\ntype: on\ntitle: yes\ndescription: 00:00\nx-extra: { nested: [false, off, 0o17] }\n---\n\n# Heading\n");
    put(root, "docs/api/readme.md", "# Plain Markdown\n");
    put(root, "docs/api/tool.md", "---\nx-tool: yes\n---\n\n# Tool configuration\n");
    put(root, "docs/api/.hidden.md", "---\ntype: Secret\n---\n# Dot path\n");
    put(root, "docs/api/_nested/note.md", "---\ntype: Note\n---\n# Note\n");
    ok(run(root, ["lint", "--strict"], {runtime}));
    ok(run(root, ["index", "--write"], {runtime}));
    const rootIndex = path.join(root, "docs/index.md");
    assert.match(fs.readFileSync(rootIndex, "utf8"), /okf_version: "0\.3"/);

    const header = '\uFEFF---\r\nokf_version: "0.3"\r\ntitle: yes\r\ndescription: Existing bundle\r\n' +
      'license: CC-BY-4.0\r\nx-team: {keep: [on, false]} # keep comment\r\n---\r\n\r\n# Handwritten heading\r\n\r\n';
    const tail = "\r\n\r\nAfter the marker.\n";
    fs.writeFileSync(rootIndex, header + "<!-- okf:auto:start -->\r\nOld\r\n<!-- okf:auto:end -->" + tail);
    ok(run(root, ["index", "--write"], {runtime}));
    const rebuilt = fs.readFileSync(rootIndex, "utf8");
    assert.ok(rebuilt.startsWith(header));
    assert.ok(rebuilt.endsWith(tail));
    ok(run(root, ["index", "--check"], {runtime}));
    ok(run(root, ["render"], {runtime}));
    const html = fs.readFileSync(path.join(root, "_site/api/sample.html"), "utf8");
    assert.match(html, /<title>yes — Test Site<\/title>/);
    assert.match(html, /OKF <span>v0\.3<\/span>/);
    assert.equal(fs.existsSync(path.join(root, "_site/api/readme.html")), false);
    assert.equal(fs.existsSync(path.join(root, "_site/api/.hidden.html")), false);
    assert.equal(fs.existsSync(path.join(root, "_site/api/_nested/note.html")), true);
    const project = run(root, ["lint", "--project"], {runtime});
    assert.equal(project.status, 1);
    assert.match(project.stdout, /warn L9|error L3/);
    put(root, "docs/api/duplicate.md", "---\ntype: Note\nx-meta: {again: 1, again: 2}\n---\n");
    assert.match(run(root, ["lint"], {runtime}).stdout, /duplicate\.md:1 error L1/);
  }
});

test("OKF resolves path fields, preserves broken links and limits the legacy retry", (t) => {
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    init(root, runtime);
    const declared = (version) => put(root, "docs/index.md", '---\nokf_version: "' + version + '"\n---\n# Bundle\n');
    const concept = (file, title, metadata = "", text = "") =>
      put(root, file, "---\ntype: Reference\ntitle: " + title + "\n" + metadata + "---\n\n" + text);
    concept("docs/root-only.md", "Legacy root target");
    concept("docs/target one.md", "Encoded target");
    concept("docs/duplicate.md", "Root duplicate");
    concept("docs/api/duplicate.md", "Local duplicate");
    concept("docs/api/computation.md", "Computation target");
    concept("docs/api/executor.md", "Executor target");
    concept("docs/api/attester.md", "Attester target");
    concept("docs/api/replacement.md", "Replacement",
      "status: deprecated\nsuperseded_by: ./origin.md\n");
    put(root, "docs/logo.img", "content");
    put(root, "outside.md", "Must never render.");
    concept("docs/api/origin.md", "Origin concept",
      'status: deprecated\ntags: "one,tag"\nresource: duplicate.md\nsources: {resource: root-only.md}\n' +
      'computation: ./computation.md\nexecutor: {resource: ./executor.md}\nattester: {resource: ./attester.md}\n' +
      'superseded_by: ./replacement.md#new\n',
      "# Origin\n\n[encoded](/target%20one%2Emd?x=1#heading) [broken](root-only.md) " +
      "[outside](../../outside.md)\n\n![asset](/logo.img#image)\n\n" +
      "| A | B |\n|---|---|\n| 1 | 2 |\n\nSource.[^origin]\n\n[^origin]: Source note.\n");
    const html = (file) => fs.readFileSync(path.join(root, "_site", file), "utf8");
    const backlinks = (file) => html(file).match(/<aside class="backlinks">.*?<\/aside>/s)?.[0] ?? "";
    for (const version of ["0.2", "0.3", "0.10", null]) {
      if (version === null) fs.rmSync(path.join(root, "docs/index.md"));
      else declared(version);
      ok(run(root, ["render"], {runtime}));
      const legacy = version === "0.2" || version === null;
      assert.equal(backlinks("root-only.html").includes('href="api/origin.html">Origin concept'), legacy);
      assert.match(html("api/origin.html"), /href="root-only\.md"/);
      assert.doesNotMatch(backlinks("duplicate.html"), /href="api\/origin\.html">Origin concept/);
      for (const target of ["duplicate", "computation", "executor", "attester"]) {
        assert.match(backlinks("api/" + target + ".html"), /href="origin\.html">Origin concept/);
      }
      if (!legacy) {
        const page = html("api/origin.html");
        assert.match(page, /href="\.\.\/target%20one\.html\?x=1#heading"/);
        assert.match(page, /src="\.\.\/\.\.\/docs\/logo\.img#image"/);
        assert.match(page, /href="\.\.\/\.\.\/outside\.md"/);
        assert.match(page, /後継文書 — <a href="replacement\.html#new"/);
        assert.match(page, /data-search="[^"]*one,tag"/);
        assert.match(page, /footnote-ref/);
        assert.match(page, /<table>/);
        assert.match(html("api/replacement.html"), /後継文書 — <a href="origin\.html"/);
        assert.equal(fs.existsSync(path.join(root, "_site/outside.html")), false);
      }
    }
    declared("0.3");
    concept("docs/api/broken-replacement.md", "Broken replacement", "status: deprecated\nsuperseded_by: ./missing.md\n");
    ok(run(root, ["render"], {runtime}));
    assert.match(html("api/broken-replacement.html"), /後継文書 — \.\/missing\.md/);
  }
});

test("OKF 0.3 evaluates current trust and RFC 3339 freshness in both CLIs and HTML", (t) => {
  const now = Date.now();
  const future = new Date(now + 10 * 60 * 1000).toISOString();
  const past = new Date(now - 10 * 60 * 1000).toISOString();
  const observed = [];
  for (const runtime of ["python", "node"]) {
    const root = temp(t);
    init(root, runtime);
    put(root, "docs/index.md", '---\nokf_version: "0.3"\n---\n# OKF\n');
    const concept = (name, meta) => put(root, "docs/api/" + name + ".md",
      "---\ntype: Example\n" + meta + "\n---\n\n# " + name + "\n");
    const gen = 'generated: {by: process:write, at: "2026-06-20T12:00:00.000000002Z"}\n';
    concept("team", gen + 'verified:\n  - {by: human:prior, at: "2026-06-20T12:00:00.000000001Z"}\n' +
      '  - {by: team:science, at: "2026-06-20T21:00:00.000000002+09:00"}\n' +
      'sources: {resource: all study records, author: group:science, last_modified: "2026-01-01"}\n' +
      'stale_after: "' + future + '"');
    concept("equal", gen + 'verified: {by: human:equal, at: "2026-06-20T12:00:00.000000002Z"}\n' +
      'stale_after: "' + past + '"');
    concept("no-generated", 'generated: []\nverified: {by: human:other, at: !!timestamp 2026-06-20T12:00:00Z}\n' +
      'stale_after: 2000-06-01');
    concept("only-old", gen + 'verified: {by: human:prior, at: "2026-06-20T12:00:00.000000001Z"}\n' +
      'stale_after: []\nsources: ""');
    concept("bad", 'verified: {by: human:missing}\nstale_after: "2026-12-01T10:00:00"');
    concept("bad-date", 'stale_after: "2026-02-30"');
    const lint = run(root, ["lint"], {runtime});
    assert.equal(lint.status, 0, lint.stderr);
    assert.match(lint.stdout, /bad\.md:3 warn L6/);
    assert.match(lint.stdout, /bad-date\.md:3 warn L14/);
    assert.doesNotMatch(lint.stdout, /(?:team|equal|only-old|no-generated)\.md:/);
    const stale = JSON.parse(ok(run(root, ["stale", "--format", "json"], {runtime})));
    const kinds = (name) => stale.filter((item) => item.path === "docs/api/" + name + ".md").map((item) => item.kind);
    assert.deepEqual(kinds("team"), []);
    assert.deepEqual(kinds("equal"), ["expired"]);
    assert.deepEqual(kinds("no-generated"), ["expired"]);
    assert.deepEqual(kinds("only-old"), ["unverified"]);
    assert.deepEqual(kinds("bad"), ["malformed-stale-after", "unverified"]);
    observed.push([lint.stdout, stale]);
    ok(run(root, ["render"], {runtime}));
    const html = (name) => fs.readFileSync(path.join(root, "_site/api/" + name + ".html"), "utf8");
    assert.match(html("team"), /badge machine-confirmed/);
    assert.match(html("equal"), /badge human-reviewed.*badge stale/);
    assert.match(html("no-generated"), /badge human-reviewed.*badge stale/);
    assert.match(html("only-old"), /badge unverified/);
    assert.match(html("bad"), /badge unverified.*badge malformed/);
  }
  assert.deepEqual(observed[0], observed[1]);
});
