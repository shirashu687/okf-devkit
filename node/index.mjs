import fs from "node:fs";
import path from "node:path";
import {
  Doc,
  MarkerError,
  compare,
  extractDate,
  read,
  rel,
  write,
} from "./core.mjs";

const clean = (value) =>
  String(value)
    .replace(/\s*[\r\n]+\s*/g, " ")
    .trim();
const label = (value) =>
  clean(value)
    .replaceAll("\\", "\\\\")
    .replaceAll("[", "\\[")
    .replaceAll("]", "\\]");
const link = (value) =>
  value
    .replaceAll("%", "%25")
    .replaceAll("(", "%28")
    .replaceAll(")", "%29")
    .replaceAll(" ", "%20");
const displayTitle = (doc) =>
  doc.title + (doc.status === "draft" ? " (draft)" : "");
const entry = (title, href, description, extra = "") =>
  `* [${label(title)}](${link(href)})` +
  ([extra, description].filter(Boolean).map(clean).length
    ? ` - ${[extra, description].filter(Boolean).map(clean).join(" - ")}`
    : "");
function indexLink(b, dir, target) {
  return b.index.link_style === "bundle-absolute"
    ? "/" + rel(target, b.root)
    : "./" + rel(target, dir);
}
function localDocs(b, dir) {
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter(
      (e) =>
        e.isFile() &&
        e.name.endsWith(".md") &&
        !b.cfg.reserved.includes(e.name),
    )
    .map((e) => path.join(dir, e.name))
    .filter((p) => !b.excluded(p))
    .sort(compare)
    .map((p) => new Doc(p, b));
}
export function indexBlock(b, dir) {
  if (dir === b.backlogDir()) return backlogBlock(b, dir);
  const sections = [],
    children = [];
  for (const e of fs
    .readdirSync(dir, { withFileTypes: true })
    .sort((a, c) => compare(a.name, c.name))) {
    const sub = path.join(dir, e.name),
      idx = path.join(sub, "index.md");
    if (!e.isDirectory() || /^[_.]/.test(e.name) || b.excluded(sub)) continue;
    const title =
      (fs.existsSync(idx) ? new Doc(idx, b).h1 : null) ||
      `${e.name}${b.index.heading_suffix}`;
    children.push(entry(title, indexLink(b, dir, idx), ""));
  }
  if (children.length)
    sections.push([b.index.subdir_section, children.sort(compare)]);
  const docs = localDocs(b, dir),
    active = docs.filter((d) => d.status !== "deprecated");
  const lines = (items) =>
    items
      .sort(
        (a, c) =>
          compare(a.title, c.title) || compare(a.bundleRel, c.bundleRel),
      )
      .map((d) =>
        entry(displayTitle(d), indexLink(b, dir, d.path), d.description),
      );
  for (const type of b.types) {
    const group = active.filter((d) => d.type === type);
    if (group.length) sections.push([type, lines(group)]);
  }
  const other = active.filter((d) => !b.types.includes(d.type)),
    old = docs.filter((d) => d.status === "deprecated");
  if (other.length) sections.push([b.index.other_section, lines(other)]);
  if (old.length) sections.push([b.index.deprecated_section, lines(old)]);
  return sections.length
    ? sections
        .map(([name, items]) => `## ${name}\n${items.join("\n")}`)
        .join("\n\n") + "\n"
    : "";
}
function backlogBlock(b, dir) {
  const states = b.backlog.state_order,
    priorities = b.backlog.priorities,
    groups = new Map(states.map((s) => [s, []]));
  for (const d of localDocs(b, dir)) {
    const state = d.get("state", "todo");
    if (!groups.has(state)) groups.set(state, []);
    groups.get(state).push(d);
  }
  const order = [
    ...states,
    ...[...groups.keys()].filter((s) => !states.includes(s)).sort(compare),
  ];
  const sections = [
    [
      "| state | 件数 |",
      "|---|---|",
      ...order.map((s) => `| ${s} | ${groups.get(s).length} |`),
    ].join("\n"),
  ];
  const rank = (d) => {
    const i = priorities.indexOf(d.get("priority", ""));
    return i < 0 ? priorities.length : i;
  };
  for (const state of order) {
    const items = groups.get(state);
    if (!items.length) continue;
    items.sort(
      state === "done"
        ? (a, c) =>
            compare(
              extractDate(c.get("done_at")) || "",
              extractDate(a.get("done_at")) || "",
            ) || compare(c.title, a.title)
        : (a, c) =>
            rank(a) - rank(c) ||
            compare(a.title, c.title) ||
            compare(a.bundleRel, c.bundleRel),
    );
    sections.push(
      `## ${state}\n` +
        items
          .map((d) =>
            entry(
              displayTitle(d),
              indexLink(b, dir, d.path),
              d.description,
              state === "done"
                ? `${extractDate(d.get("done_at")) || "日付不明"} 完了`
                : ["priority", "effort"]
                    .filter((k) => d.get(k))
                    .map((k) => "`" + d.get(k) + "`")
                    .join(" "),
            ),
          )
          .join("\n"),
    );
  }
  return sections.join("\n\n") + "\n";
}
export function renderIndex(b, dir, block = indexBlock(b, dir)) {
  const { start_marker: start, end_marker: end } = b.index,
    file = path.join(dir, "index.md"),
    auto = `${start}\n${block}${end}\n`;
  if (!fs.existsSync(file)) {
    const root = dir === b.root;
    return (
      (root ? `---\nokf_version: "${b.index.okf_version}"\n---\n\n` : "") +
      `# ${root ? b.index.root_heading : path.basename(dir) + b.index.heading_suffix}\n\n${auto}`
    );
  }
  const text = read(file),
    ns = text.split(start).length - 1,
    ne = text.split(end).length - 1;
  if (!ns && !ne) return text.replace(/\n+$/, "") + "\n\n" + auto;
  if (ns === 1 && ne === 1 && text.indexOf(start) < text.indexOf(end))
    return (
      text.slice(0, text.indexOf(start)) +
      auto.slice(0, -1) +
      text.slice(text.indexOf(end) + end.length)
    );
  throw new MarkerError(
    `${rel(file, b.repo)}: 自動生成マーカーが破損しています（start ${ns} 個 / end ${ne} 個）。1 組を正しい順序に修正してください。`,
  );
}
export function planIndex(b) {
  const plan = [],
    errors = [];
  for (const dir of b.dirs()) {
    try {
      plan.push([path.join(dir, "index.md"), renderIndex(b, dir)]);
    } catch (e) {
      if (!(e instanceof MarkerError)) throw e;
      errors.push(e);
    }
  }
  return { plan, errors };
}
export function cmdIndex(b, args = {}) {
  const { plan, errors } = planIndex(b);
  if (errors.length) {
    console.error(
      "index.md の自動生成マーカーが壊れています。書き込みを中止しました:",
    );
    for (const e of errors) console.error(`  ${e.message}`);
    return 1;
  }
  const changed = [];
  for (const [file, content] of plan) {
    if (fs.existsSync(file) && read(file) === content) continue;
    changed.push(rel(file, b.repo));
    if (args.write) write(file, content);
  }
  if (args.check && changed.length) {
    console.log("index.md が最新ではありません:");
    changed.forEach((p) => console.log(`  ${p}`));
    return 1;
  }
  if (changed.length) {
    console.log(
      `index.md を ${changed.length} 件 ${args.write ? "更新しました" : "更新が必要です（--write で書き込み）"}:`,
    );
    changed.forEach((p) => console.log(`  ${p}`));
  } else if (!args.quiet) console.log("index.md はすべて最新です。");
  return 0;
}
