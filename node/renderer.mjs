import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import MarkdownIt from "markdown-it";
import {
  Doc,
  OkfError,
  compare,
  dataDir,
  inside,
  read,
  rel,
  write,
} from "./core.mjs";

const owned = "<!-- okf-devkit-owned:v1 -->";
const escape = (s, quotes = true) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', quotes ? "&quot;" : '"')
    .replaceAll("'", quotes ? "&#x27;" : "'");
const htmlPath = (s) => s.replace(/\.[^.\/]+$/, ".html");
const relativeHtml = (from, to) =>
  path.posix.relative(path.posix.dirname(from), htmlPath(to));
const asset = (name) => read(path.join(dataDir, "assets", name));
function* tokens(items) {
  for (const t of items) {
    yield t;
    if (t.children) yield* tokens(t.children);
  }
}
export function rewriteHref(source, output, href, sources) {
  if (!href || /^(?:#|\/\/|[a-zA-Z][a-zA-Z0-9+.-]*:)/.test(href))
    return [href, null, null];
  const match = href.match(/^([^?#]*)(\?[^#]*)?(#.*)?$/),
    raw = match?.[1];
  if (!raw || !(/\.md$/i.test(raw) || raw.endsWith("/")))
    return [href, null, null];
  let decoded;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    decoded = raw;
  }
  let target = decoded.startsWith("/")
    ? decoded.replace(/^\/+/, "")
    : path.posix.join(path.posix.dirname(source), decoded);
  if (decoded.endsWith("/")) target = path.posix.join(target, "index.md");
  target = path.posix.normalize(target);
  if (target === ".." || target.startsWith("../"))
    return [
      href,
      null,
      `${source}: Bundle 外を指すリンクを保持しました: ${href}`,
    ];
  target = target.replace(/^[./]+/, "");
  if (!sources.has(target))
    return [
      href,
      null,
      `${source}: HTML 化できないリンク先を保持しました: ${href}`,
    ];
  const relative = relativeHtml(output, target),
    encoded = encodeURI(relative).replaceAll("#", "%23").replaceAll("?", "%3F");
  return [encoded + (match[2] || "") + (match[3] || ""), target, null];
}
function markdown() {
  const md = new MarkdownIt("commonmark", {
    html: false,
    linkify: false,
    typographer: false,
  }).enable("table");
  const fence = md.renderer.rules.fence;
  md.renderer.rules.fence = (items, i, options, env, self) => {
    const t = items[i],
      language = t.info.trim().split(/\s+/)[0];
    if (language.toLowerCase() === "mermaid")
      return `<figure class="diagram"><div class="mermaid" data-mermaid-source="true">${escape(t.content, false)}</div><figcaption>Mermaid diagram</figcaption></figure>\n`;
    const rendered = fence(items, i, options, env, self);
    return (t.content.match(/\n/g) || []).length > 40
      ? `<details class="long-code"><summary>長いコードを表示（${escape(language || "code")}）</summary>${rendered}</details>\n`
      : rendered;
  };
  md.renderer.rules.table_open = () => '<div class="table-scroll"><table>\n';
  md.renderer.rules.table_close = () => "</table></div>\n";
  return md;
}
function prepare(doc, b, md) {
  const source = rel(doc.path, b.root),
    output = htmlPath(source),
    used = new Map(),
    headings = [],
    parts = [];
  const items = md.parse(
    doc.body.replace(/^\s*<!--\s*okf:auto:(?:start|end)\s*-->\s*$/gm, ""),
    {},
  );
  items.forEach((t, i) => {
    if (t.type === "heading_open" && items[i + 1]) {
      const title = items[i + 1].content.trim(),
        level = Number(t.tag.slice(1));
      const slug =
        title
          .normalize("NFKC")
          .trim()
          .toLowerCase()
          .replace(/[`*_~\[\](){}<>]/g, "")
          .replace(/[^\p{L}\p{N}_\-\u3040-\u30ff\u3400-\u9fff]+/gu, "-")
          .replace(/^[-_]+|[-_]+$/g, "") || "section";
      const count = (used.get(slug) || 0) + 1;
      used.set(slug, count);
      const anchor = slug + (count === 1 ? "" : `-${count}`);
      t.attrSet("id", anchor);
      headings.push({ title, level, anchor });
    }
    if (["inline", "fence", "code_block"].includes(t.type))
      parts.push(t.content);
  });
  return {
    doc,
    source,
    output,
    items,
    headings,
    charCount: [...parts.join("").replace(/\s+/g, "")].length,
    outbound: new Set(),
  };
}
function navigation(pages, current) {
  const groups = new Map(),
    order = ["ルート", "project", "client", "server", "batch", "backlog"];
  const names = {
    ルート: "全体",
    project: "プロジェクト",
    client: "クライアント",
    server: "サーバー",
    batch: "バッチ",
    backlog: "バックログ",
  };
  for (const page of pages) {
    const group = page.source.includes("/")
      ? page.source.split("/")[0]
      : "ルート";
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(page);
  }
  const rank = (g) => (order.includes(g) ? order.indexOf(g) : 99);
  return [...groups.keys()]
    .sort((a, b) => rank(a) - rank(b) || compare(a, b))
    .map((g) => {
      const items = groups
        .get(g)
        .sort(
          (a, b) =>
            Number(a.source !== `${g}/index.md`) -
              Number(b.source !== `${g}/index.md`) ||
            compare(a.source, b.source),
        );
      return (
        `<section><h2>${escape(names[g] || g)}</h2><ul>` +
        items
          .map((p) => {
            const active =
                p.source === current.source
                  ? ' aria-current="page" class="active"'
                  : "",
              tags = p.doc.get("tags", []);
            const search = [
              p.doc.title,
              p.doc.description,
              p.doc.type,
              Array.isArray(tags) ? tags.join(" ") : "",
            ]
              .join(" ")
              .toLowerCase();
            return `<li data-search="${escape(search)}"><a href="${escape(relativeHtml(current.output, p.source))}"${active}>${escape(p.doc.title)}</a></li>`;
          })
          .join("") +
        "</ul></section>"
      );
    })
    .join("");
}
function breadcrumbs(page, sources) {
  const parts = page.source.split("/"),
    crumbs = [
      `<a href="${escape(relativeHtml(page.output, "index.md"))}">docs</a>`,
    ];
  for (let i = 0; i < parts.length - 1; i++) {
    const source = parts.slice(0, i + 1).join("/") + "/index.md";
    crumbs.push(
      sources.has(source)
        ? `<a href="${escape(relativeHtml(page.output, source))}">${escape(parts[i])}</a>`
        : `<span>${escape(parts[i])}</span>`,
    );
  }
  if (page.source !== "index.md")
    crumbs.push(`<span>${escape(page.doc.title)}</span>`);
  return (
    '<nav class="breadcrumbs" aria-label="パンくず">' +
    crumbs.join('<span aria-hidden="true">/</span>') +
    "</nav>"
  );
}
function badges(doc) {
  const type =
      doc.type ||
      (doc.name === "index.md"
        ? "Index"
        : doc.name === "log.md"
          ? "Log"
          : "Document"),
    verified = doc.get("verified", []);
  const trust =
    !Array.isArray(verified) || !verified.length
      ? ["unverified", "未検証"]
      : verified.some((v) => String(v?.by || "").startsWith("human:"))
        ? ["human-reviewed", "人間レビュー済み"]
        : ["machine-confirmed", "機械確認済み"];
  const values = [["type", type], [`status-${doc.status}`, doc.status], trust];
  if (doc.type === "Backlog Item")
    for (const k of ["state", "priority", "effort", "ai"])
      if (doc.get(k) !== null) values.push([k, `${k}: ${doc.get(k)}`]);
  return (
    '<div class="badges">' +
    values
      .map(
        ([css, label]) =>
          `<span class="badge ${escape(css)}">${escape(label)}</span>`,
      )
      .join("") +
    "</div>"
  );
}
function toc(headings) {
  const visible = headings.filter((h) => h.level >= 2);
  if (visible.length < 3) return "";
  return (
    '<nav class="toc" aria-label="ページ内目次"><h2>目次</h2><ol>' +
    visible
      .map(
        (h) =>
          `<li class="toc-level-${Math.max(0, h.level - 2)}"><a href="#${escape(h.anchor)}">${escape(h.title)}</a></li>`,
      )
      .join("") +
    "</ol></nav>"
  );
}
function related(page, sources) {
  const raw = page.doc.get("related", []);
  if (!Array.isArray(raw)) return "";
  const items = raw
    .filter((v) => typeof v === "string")
    .flatMap((v) => {
      const [href, target] = rewriteHref(page.source, page.output, v, sources);
      return target
        ? [`<li><a href="${escape(href)}">${escape(v)}</a></li>`]
        : [];
    });
  return items.length
    ? '<aside class="related"><h2>関連ドキュメント</h2><ul>' +
        items.join("") +
        "</ul></aside>"
    : "";
}
function backlinks(page, pages) {
  const incoming = pages
    .filter((p) => p.outbound.has(page.source))
    .sort((a, b) => compare(a.source, b.source));
  return incoming.length
    ? '<aside class="backlinks"><h2>このページへのリンク</h2><ul>' +
        incoming
          .map(
            (p) =>
              `<li><a href="${escape(relativeHtml(page.output, p.source))}">${escape(p.doc.title)}</a></li>`,
          )
          .join("") +
        "</ul></aside>"
    : "";
}
export function renderBundle(b, output = b.root, doWrite = true) {
  output = inside(b.repo, output);
  const md = markdown(),
    pages = b.files(true).map((p) => prepare(new Doc(p, b), b, md)),
    sources = new Set(pages.map((p) => p.source)),
    warnings = [];
  for (const page of pages) {
    for (const token of tokens(page.items))
      if (token.type === "link_open") {
        const [href, target, warning] = rewriteHref(
          page.source,
          page.output,
          token.attrGet("href"),
          sources,
        );
        token.attrSet("href", href);
        if (target) page.outbound.add(target);
        if (warning) {
          token.attrJoin("class", "is-broken");
          warnings.push(warning);
        }
      }
    const refs = page.doc.get("related", []);
    if (Array.isArray(refs))
      for (const ref of refs.filter((r) => typeof r === "string")) {
        const [, target, warning] = rewriteHref(
          page.source,
          page.output,
          ref,
          sources,
        );
        if (target) page.outbound.add(target);
        if (warning) warnings.push(warning);
      }
    page.body = md.renderer.render(page.items, md.options, {});
  }
  const template = asset("page.html"),
    plan = [];
  for (const p of pages) {
    const target = inside(output, path.join(output, p.output)),
      type = p.doc.type || (p.doc.name === "index.md" ? "Index" : "Log");
    const values = {
      TITLE: escape(p.doc.title),
      DESCRIPTION: escape(
        p.doc.description || `${p.doc.title} — ${b.siteName} documentation`,
      ),
      SITE_NAME: escape(b.siteName),
      LANG: "ja",
      ASSETS: escape(
        path.posix.relative(path.posix.dirname(p.output), "_assets"),
      ),
      SOURCE: escape(p.source),
      SOURCE_LINK: escape(rel(p.doc.path, path.dirname(target))),
      HOME_LINK: escape(relativeHtml(p.output, "index.md")),
      SOURCE_HASH: createHash("sha256")
        .update(p.doc.text)
        .digest("hex")
        .slice(0, 16),
      TYPE_CLASS: escape(
        type
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "") || "document",
      ),
      LONG_CLASS:
        p.headings.filter((h) => h.level >= 2).length >= 5 ||
        p.charCount >= 3000
          ? " long-document"
          : "",
      BREADCRUMBS: breadcrumbs(p, sources),
      BADGES: badges(p.doc),
      NAVIGATION: navigation(pages, p),
      TOC: toc(p.headings),
      CONTENT: p.body,
      RELATED: related(p, sources),
      BACKLINKS: backlinks(p, pages),
    };
    plan.push([
      target,
      template.replace(/\{\{([A-Z0-9_]+)\}\}/g, (_m, k) => {
        if (!(k in values))
          throw new OkfError(`HTML テンプレートに未解決の項目があります: ${k}`);
        return values[k];
      }),
    ]);
  }
  const expected = new Set(plan.map(([p]) => p));
  for (const name of ["docs.css", "docs.js"])
    plan.push([
      inside(output, path.join(output, "_assets", name)),
      asset(name),
    ]);
  let written = 0,
    removed = 0;
  if (doWrite) {
    for (const [file, content] of plan) written += Number(write(file, content));
    const clean = (dir) => {
      for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
        const file = path.join(dir, e.name);
        if (e.isDirectory()) clean(file);
        else if (
          e.isFile() &&
          e.name.endsWith(".html") &&
          !expected.has(file) &&
          read(file).slice(0, 256).includes(owned)
        ) {
          fs.unlinkSync(file);
          removed++;
        }
      }
    };
    clean(output);
  }
  return {
    pages: pages.length,
    written,
    removed,
    warnings: [...new Set(warnings)].sort(compare),
    output,
  };
}
export function cmdRender(b, args) {
  const report = renderBundle(
    b,
    args.output ? path.resolve(b.repo, args.output) : b.root,
    !args.check,
  );
  if (args.hook) {
    console.log("{}");
    return 0;
  }
  report.warnings.forEach((w) => console.error(`warn: ${w}`));
  console.log(
    `HTML ${args.check ? "検証" : "生成"}: ${report.pages} ページ / 書き込み ${report.written} 件 / 削除 ${report.removed} 件 / warn ${report.warnings.length} 件 -> ${report.output}`,
  );
  return 0;
}
