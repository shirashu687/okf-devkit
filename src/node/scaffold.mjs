import fs from "node:fs";
import path from "node:path";
import { cmdIndex } from "./index.mjs";
import {
  Doc,
  OkfError,
  compare,
  dataDir,
  flow,
  inside,
  now,
  read,
  rel,
  scalar,
  slash,
  today,
  write,
} from "./core.mjs";

const scaffold = (name) => read(path.join(dataDir, "scaffold", name));
export const agentSettings = new Map([
  ["claude", ".claude/settings.json"],
  ["codex", ".codex/hooks.json"],
  ["copilot", ".github/hooks/okf-render.json"],
]);

function selectedAgents(value) {
  if (value === undefined || value === "all") return [...agentSettings.keys()];
  if (value === "none") return [];
  const names = value.split(",").map((name) => name.trim());
  if (names.some((name) => !agentSettings.has(name)) ||
      new Set(names).size !== names.length)
    throw new OkfError("--agent は claude,codex,copilot から選ぶか、all / none を指定してください");
  return names;
}
const slugify = (title) =>
  title
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
function validSlug(value) {
  if (!/^[a-z0-9]+(?:[-.][a-z0-9]+)*$/.test(value))
    throw new OkfError(`slug は kebab-case で指定してください: ${value}`);
  return value;
}
function validDir(value) {
  const s = slash(value);
  if (
    !s ||
    /^[/.]|:/.test(s) ||
    s.split("/").some((p) => !p || p === "." || p === "..")
  )
    throw new OkfError(`相対ディレクトリが不正です: ${value}`);
  return s;
}
function vocab(value, allowed, label) {
  if (allowed?.length && !allowed.includes(value))
    throw new OkfError(`${label} ${value} は語彙表にありません`);
}
function nextId(dir, prefix = "") {
  const rx = new RegExp(
    `^${prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\d{4})(?:-|\\.md$)`,
  );
  return (
    Math.max(
      0,
      ...(fs.existsSync(dir) ? fs.readdirSync(dir) : [])
        .filter((f) => f.endsWith(".md"))
        .map((f) => Number(f.match(rx)?.[1] || 0)),
    ) + 1
  );
}
export function setField(text, key, value, parent = null) {
  const lines = text.split("\n"),
    end = lines.findIndex((l, i) => i > 0 && l.trim() === "---");
  if (lines[0].trim() !== "---" || end < 0) return text;
  let inParent = false;
  for (let i = 1; i < end; i++) {
    if (!parent && lines[i].startsWith(`${key}:`)) {
      let stop = i + 1;
      while (stop < end && (/^[ \t]/.test(lines[stop]) || !lines[stop].trim())) stop++;
      lines.splice(i, stop - i, `${key}: ${value}`);
      return lines.join("\n");
    }
    if (parent) {
      if (lines[i].startsWith(`${parent}:`)) {
        inParent = true;
        continue;
      }
      if (inParent && !/^[ \t]/.test(lines[i])) break;
      if (inParent && lines[i].trimStart().startsWith(`${key}:`)) {
        lines[i] = lines[i].match(/^\s*/)[0] + `${key}: ${value}`;
        break;
      }
    }
  }
  if (!parent) lines.splice(end, 0, `${key}: ${value}`);
  return lines.join("\n");
}
function parseLayers(specs) {
  const layers = [],
    seen = new Set();
  for (const spec of specs || []) {
    const eq = spec.indexOf("="),
      name = spec.slice(0, eq).trim(),
      rest = spec.slice(eq + 1),
      colon = rest.indexOf(":");
    if (eq < 1 || !name)
      throw new OkfError(`--layer の書式が不正です（name=glob[:dir]）: ${spec}`);
    if (!/^[a-z0-9][a-z0-9_-]*$/.test(name))
      throw new OkfError(`層名は英小文字・数字で始め、英小文字・数字・- _ を使用してください: ${name}`);
    if (name === "shared")
      throw new OkfError("shared は層をまたぐ知識用に予約されています");
    if (seen.has(name)) throw new OkfError(`層名が重複しています: ${name}`);
    const glob = (colon < 0 ? rest : rest.slice(0, colon)).trim(),
      dir = validDir((colon < 0 ? "" : rest.slice(colon + 1)).trim() || name);
    if (!glob) throw new OkfError("層の glob が空です");
    seen.add(name);
    layers.push({ name, glob, dir });
  }
  return layers;
}

export function scaffoldPlan(repo, args, layers = parseLayers(args.layer)) {
  const bundle = validDir(slash(args.bundleRoot || "docs").trim().replace(/\/+$/, ""));
  const site = (args.siteName || path.basename(repo)).trim() || "Project";
  const agents = selectedAgents(args.agent);
  const runner = args.runner?.trim() ?? "okf";
  if (!runner || /[|\x00-\x1f\x60\x7f]/.test(runner))
    throw new OkfError("--runner には1行の実行表記を指定してください（バッククォートと | は使用不可）");
  const config = {
    bundle_root: scalar(bundle),
    site_name: scalar(site),
    root_heading: scalar(`${site} ドキュメント`),
    layers: [...layers.map((l) => `  - ${scalar(l.name)}`), "  - shared"].join(
      "\n",
    ),
    layer_dirs: [
      ...layers.map((l) => `  ${l.name}: ${scalar(l.dir)}`),
      "  shared: project",
    ].join("\n"),
    layer_map: [
      ...layers.map(
        (l) => `  - { glob: ${scalar(l.glob)}, layer: ${scalar(l.name)} }`,
      ),
      `  - { glob: ${scalar(bundle + "/**")}, layer: skip }`,
      '  - { glob: "**", layer: shared }',
    ].join("\n"),
    log_layers: `[${layers.map((l) => l.name).join(", ")}]`,
    log_paths: [
      ...layers.map((l) => `    ${l.name}: ${scalar(l.dir + "/log.md")}`),
      "    shared: log.md",
    ].join("\n"),
  };
  const tokens = {
    GENERATED_AT: now(),
    RUNNER: runner,
    LAYER_EXAMPLE: [...layers.map((l) => l.name), "shared"].join(" | "),
    BUNDLE_ROOT: bundle,
    SITE_NAME: site,
    LAYER_LIST: layers.map((l) => l.name).join("、") || "（層なし）",
    LAYER_DIRS: layers.map((l) => "`" + l.dir + "/`").join(" ") || "—",
    LAYER_TABLE:
      layers
        .map((l) => `| \`${bundle}/${l.dir}/log.md\` | \`${l.glob}\` の変更 |`)
        .join("\n") || "| （層を定義していません） | — |",
  };
  const expand = (text) =>
    text.replace(/\{\{([A-Z_]+)\}\}/g, (m, k) => tokens[k] ?? m);
  const plan = [
    [
      "okf.yml",
      scaffold("okf.yml.tmpl").replace(
        /\{([a-z_]+)\}/g,
        (m, k) => config[k] ?? m,
      ),
    ],
    [`${bundle}/AGENTS.md`, expand(scaffold("AGENTS.md.tmpl"))],
    [`${bundle}/CONVENTIONS.md`, expand(scaffold("CONVENTIONS.md.tmpl"))],
  ];
  for (const file of fs
    .readdirSync(path.join(dataDir, "scaffold/templates"))
    .sort(compare))
    plan.push([`${bundle}/_templates/${file}`, expand(scaffold(`templates/${file}`)).replace(
      "layer: <client | server | batch | shared>",
      () => "layer: <" + tokens.LAYER_EXAMPLE + ">",
    )]);
  for (const file of fs
    .readdirSync(path.join(dataDir, "scaffold/hooks"))
    .sort(compare))
    plan.push([`.okf/hooks/${file}`, scaffold(`hooks/${file}`)]);
  if (agents.length)
    for (const file of ["agent_stop.sh", "agent_stop.ps1"])
      plan.push([`.okf/hooks/${file}`, scaffold(`agent-hooks/${file}`)]);
  for (const name of agents) {
    const template = name === "claude" && process.platform === "win32" ? "claude-windows" : name;
    plan.push([agentSettings.get(name), scaffold(`agent-hooks/${template}.json`), "settings"]);
  }
  const hasNodeDeps = fs.statSync(path.join(repo, "package.json"), { throwIfNoEntry: false })?.isFile() &&
    fs.statSync(path.join(repo, "node_modules"), { throwIfNoEntry: false })?.isDirectory();
  const ignore = "/_site/\n/.okf/render-backups/\n" + (hasNodeDeps ? "/node_modules/\n" : "");
  plan.push([".gitignore", ignore, "ignore"]);
  const emptyLog = (name) =>
    `# 変更履歴 — ${name}\n\n<!-- \`${runner} log --write\` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->\n`;
  for (const l of layers)
    plan.push([`${bundle}/${l.dir}/log.md`, emptyLog(l.name)]);
  plan.push([`${bundle}/log.md`, emptyLog("shared")]);
  return { plan, bundle, runner, agents, hasNodeDeps };
}

export function cmdInit(repo, args) {
  const { plan, bundle, runner, agents, hasNodeDeps } = scaffoldPlan(repo, args);
  // Validate the entire plan (including symlinks) before the first write.
  for (const [file] of plan) inside(repo, path.resolve(repo, file));
  const skipped = [];
  const skippedSettings = [];
  const skippedIgnore = [];
  for (const [file, content, preserve] of plan) {
    const out = path.resolve(repo, file);
    // lstat also detects dangling symlinks; agent settings are never replaced.
    let exists = true;
    try { fs.lstatSync(out); } catch (e) {
      if (e.code === "ENOENT") exists = false;
      else throw e;
    }
    if (exists && (preserve || !args.force))
      (preserve === "settings" ? skippedSettings : preserve === "ignore" ? skippedIgnore : skipped).push(file);
    else {
      write(out, content);
      console.log(`作成: ${file}`);
    }
  }
  if (skipped.length) {
    console.log(`既存のためスキップ（--force で上書き）: ${skipped.length} 件`);
    skipped.forEach((p) => console.log(`  ${p}`));
  }
  if (skippedSettings.length) {
    console.log("既存のエージェント設定は保持しました（--force でも上書きしません）:");
    skippedSettings.forEach((p) => console.log(`  ${p}`));
    console.log("必要なら既存設定に .okf/hooks/agent_stop を手動で登録してください。");
  }
  if (skippedIgnore.length)
    console.log("既存の .gitignore は保持しました。/_site/、/.okf/render-backups/" +
      (hasNodeDeps ? "、/node_modules/" : "") + " の除外を確認してください。");
  console.log("エージェント設定の対象: " + (agents.join(", ") || "なし"));
  console.log("共通の HTML 生成スクリプト: .okf/hooks/render_hook.sh / .ps1");
  if (agents.length)
    console.log("利用するエージェントで hook の信頼設定と実行権限を確認してください。");
  console.log(
    `\n次の手順:\n  1. ${runner} index --write で目次を生成する\n  2. ${runner} lint で規約を確認する\n  3. ${runner} render で HTML を生成する\n  必要な場合だけ okf.yml と ${bundle}/CONVENTIONS.md を調整する\n  エージェント設定と .gitignore の出力を確認する`,
  );
  return 0;
}
export function cmdNew(b, args) {
  if (/[\r\n]/.test(args.title))
    throw new OkfError("--title に改行は使えません");
  vocab(args.layer, b.layers, "--layer");
  const backlog = args.kind === "backlog",
    type = backlog ? "Backlog Item" : args.type;
  vocab(type, b.types, "--type");
  if (backlog) {
    vocab(args.priority, b.backlog.priorities, "--priority");
    vocab(args.effort, b.backlog.efforts, "--effort");
  }
  const codeGlobs = args.codeGlobs || [];
  if (!backlog && ["Project Overview", "Architecture", "Reference", "How-To"].includes(type) && !codeGlobs.length)
    throw new OkfError("この型では --code-globs を指定してください");
  const template = b.cfg.templates[type];
  if (!template)
    throw new OkfError(`type '${type}' に対応するテンプレートがありません`);
  const templatePath = path.resolve(b.root, template);
  if (!fs.existsSync(templatePath))
    throw new OkfError("テンプレートがありません: " + template + "。配布テンプレートをバンドルに追加してください");
  let text = read(templatePath);
  const slug = args.slug ? validSlug(args.slug) : slugify(args.title);
  let dir, filename;
  if (backlog) {
    dir = b.backlogDir();
    const prefix = String(b.backlog.prefix),
      id = String(nextId(dir, `${prefix}-`)).padStart(4, "0");
    filename = `${prefix}-${id}${slug ? "-" + slug : ""}.md`;
  } else {
    if (!slug)
      throw new OkfError(
        "タイトルから slug を生成できませんでした。--slug を指定してください",
      );
    dir = path.resolve(b.root, b.cfg.layer_dirs?.[args.layer] || args.layer);
    if (args.dir) {
      const sub = validDir(args.dir);
      sub.split("/").forEach(validSlug);
      dir = path.join(dir, sub);
    }
    filename =
      (type === "Decision Record"
        ? String(nextId(dir)).padStart(4, "0") + "-"
        : "") +
      slug +
      ".md";
  }
  const out = inside(b.root, path.resolve(dir, filename));
  const fields = {
    title: args.title,
    layer: args.layer,
    ...(backlog
      ? {
          state: "todo",
          priority: args.priority,
          effort: args.effort,
          created: today(),
        }
      : { type }),
  };
  for (const [k, v] of Object.entries(fields))
    text = setField(text, k, scalar(v));
  if (backlog) text = setField(text, "tags", flow([args.layer]));
  else {
    text = setField(text, "code_globs", flow(codeGlobs));
    text = setField(text, "related", "[]");
  }
  text = setField(
    setField(text, "by", scalar("process:okf-cli"), "generated"),
    "at",
    scalar(now()),
    "generated",
  );
  text = text.replace(/^#[ \t]+<[^>\r\n]*>[ \t]*$/m, () => `# ${args.title}`);
  if (fs.existsSync(out))
    throw new OkfError(`既に存在します: ${rel(out, b.repo)}`);
  write(out, text);
  console.log(rel(out, b.repo));
  if (!args.slug && /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(args.title))
    console.error("題名の日本語は自動 slug に入りません。ファイル名を指定するには --slug を使ってください。");
  if (args.index) {
    try {
      if (!cmdIndex(b, { write: true, quiet: true })) return 0;
    } catch (e) {
      console.error(e.message);
    }
    console.error("文書は作成済みです。索引の問題を解消してから okf index --write を実行してください。");
    return 1;
  }
  return 0;
}
export function cmdStatus(b, args) {
  const dir = b.backlogDir(),
    docs = fs.existsSync(dir)
      ? fs
          .readdirSync(dir)
          .filter((f) => f.endsWith(".md") && !b.cfg.reserved.includes(f))
          .sort(compare)
          .map((f) => new Doc(path.join(dir, f), b))
      : [];
  const groups = new Map(b.backlog.state_order.map((s) => [s, []]));
  for (const d of docs) {
    const state = d.get("state", "todo");
    if (!groups.has(state)) groups.set(state, []);
    groups.get(state).push(d);
  }
  const priorities = Object.fromEntries(
    [...groups].map(([s, items]) => [
      s,
      Object.fromEntries(
        b.backlog.priorities.map((p) => [
          p,
          items.filter((d) => d.get("priority") === p).length,
        ]),
      ),
    ]),
  );
  if (args.format === "json")
    console.log(
      JSON.stringify(
        {
          total: docs.length,
          states: Object.fromEntries(
            [...groups].map(([s, items]) => [s, items.length]),
          ),
          priorities,
          doing: (groups.get("doing") || []).map((d) => ({
            path: d.repoRel,
            title: d.title,
            priority: d.get("priority"),
            effort: d.get("effort"),
          })),
        },
        null,
        2,
      ),
    );
  else {
    console.log(`backlog: 全 ${docs.length} 件`);
    for (const s of [
      ...b.backlog.state_order,
      ...[...groups.keys()]
        .filter((s) => !b.backlog.state_order.includes(s))
        .sort(compare),
    ])
      console.log(
        `  ${s.padEnd(8)} ${String(groups.get(s).length).padStart(3)} 件  (${Object.entries(
          priorities[s],
        )
          .map(([p, n]) => `${p}:${n}`)
          .join(" ")})`,
      );
    if (groups.get("doing")?.length) {
      console.log("\ndoing:");
      for (const d of groups.get("doing"))
        console.log(
          `  - ${d.title} ${["priority", "effort"]
            .filter((k) => d.get(k))
            .map((k) => "`" + d.get(k) + "`")
            .join(" ")} (${d.repoRel})`,
        );
    }
  }
  return 0;
}
