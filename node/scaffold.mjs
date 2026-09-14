import fs from "node:fs";
import path from "node:path";
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
      lines[i] = `${key}: ${value}`;
      break;
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
  return lines.join("\n");
}
export function cmdInit(repo, args) {
  const layers = [],
    seen = new Set();
  for (const spec of args.layer || []) {
    const eq = spec.indexOf("="),
      name = spec.slice(0, eq).trim(),
      rest = spec.slice(eq + 1),
      colon = rest.indexOf(":");
    if (
      eq < 1 ||
      !rest.trim() ||
      !/^[a-z0-9][a-z0-9_-]*$/.test(name) ||
      name === "shared" ||
      seen.has(name)
    )
      throw new OkfError(`--layer の書式または層名が不正です: ${spec}`);
    const glob = (colon < 0 ? rest : rest.slice(0, colon)).trim(),
      dir = validDir((colon < 0 ? "" : rest.slice(colon + 1)).trim() || name);
    if (!glob) throw new OkfError("層の glob が空です");
    seen.add(name);
    layers.push({ name, glob, dir });
  }
  const bundle = validDir(slash(args.bundleRoot || "docs").replace(/\/+$/, ""));
  const site = (args.siteName || path.basename(repo)).trim() || "Project";
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
    plan.push([`${bundle}/_templates/${file}`, scaffold(`templates/${file}`)]);
  for (const file of fs
    .readdirSync(path.join(dataDir, "scaffold/hooks"))
    .sort(compare))
    plan.push([`.okf/hooks/${file}`, scaffold(`hooks/${file}`)]);
  const emptyLog = (name) =>
    `# 変更履歴 — ${name}\n\n<!-- \`okf log --write\` が git 履歴からここに追記する。書式は /CONVENTIONS.md §7 を参照。 -->\n`;
  for (const l of layers)
    plan.push([`${bundle}/${l.dir}/log.md`, emptyLog(l.name)]);
  plan.push([`${bundle}/project/log.md`, emptyLog("shared")]);
  // Validate the entire plan (including symlinks) before the first write.
  for (const [file] of plan) inside(repo, path.resolve(repo, file));
  const skipped = [];
  for (const [file, content] of plan) {
    const out = path.resolve(repo, file);
    if (fs.existsSync(out) && !args.force) skipped.push(file);
    else {
      write(out, content);
      console.log(`作成: ${file}`);
    }
  }
  if (skipped.length) {
    console.log(`既存のためスキップ（--force で上書き）: ${skipped.length} 件`);
    skipped.forEach((p) => console.log(`  ${p}`));
  }
  console.log(
    `\n次の手順:\n  1. ${bundle}/CONVENTIONS.md の語彙を確認・調整する\n  2. okf.yml の layer_map が実際のコード配置と合っているか確認する\n  3. okf index --write で目次を生成する\n  4. okf lint で規約違反が無いか確認する`,
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
  const template = b.cfg.templates[type];
  if (!template)
    throw new OkfError(`type '${type}' に対応するテンプレートがありません`);
  let text = read(path.resolve(b.root, template));
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
  text = setField(
    setField(text, "by", scalar("process:okf-cli"), "generated"),
    "at",
    scalar(now()),
    "generated",
  );
  text = text.replace(/^#\s+<[^>\n]*>\s*$/m, () => `# ${args.title}`);
  if (fs.existsSync(out))
    throw new OkfError(`既に存在します: ${rel(out, b.repo)}`);
  write(out, text);
  console.log(rel(out, b.repo));
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
