import fs from "node:fs";
import path from "node:path";
import {
  Doc,
  MarkerError,
  compare,
  dateOnly,
  extractDate,
  inside,
  isMap,
  read,
  rel,
  timestamp,
  today,
} from "./core.mjs";
import { renderIndex } from "./index.mjs";
import { isShallow, pathTimes } from "./history.mjs";

export const findingText = (f) =>
  `${f.path}${f.line ? ":" + f.line : ""} ${f.level} ${f.rule} ${f.message}`;
const repr = (value) =>
  value === null || value === undefined
    ? "None"
    : typeof value === "boolean"
      ? value
        ? "True"
        : "False"
      : typeof value === "string"
        ? `'${value}'`
        : JSON.stringify(value);
const typeName = (value) =>
  Array.isArray(value)
    ? "list"
    : value === null
      ? "NoneType"
      : typeof value === "string"
        ? "str"
        : typeof value === "boolean"
          ? "bool"
          : typeof value === "number"
            ? Number.isInteger(value)
              ? "int"
              : "float"
            : "dict";
function actorProblem(value, label) {
  if (!isMap(value))
    return `\`${label}\` はマップ（\`by\` / \`at\`）である必要があります`;
  if (
    typeof value.by !== "string" ||
    !/^(?:human:\S+|process:\S+|[^\s/]+\/[^\s/]+)$/.test(value.by.trim())
  )
    return `\`${label}.by: ${repr(value.by)}\` は Actor 表記（producer/version, human:, process:）ではありません`;
  if (value.at != null && timestamp(value.at) === null)
    return `\`${label}.at: ${repr(value.at)}\` は ISO 8601 ではありません`;
  return null;
}
export function trust(doc) {
  const actors = Array.isArray(doc.fm.verified)
    ? doc.fm.verified
        .filter(isMap)
        .map((v) => v.by)
        .filter((v) => typeof v === "string")
        .map((v) => v.trim())
    : [];
  return !actors.length
    ? "unverified"
    : actors.some((v) => v.startsWith("human:"))
      ? "human-reviewed"
      : "machine-confirmed";
}
export function runLint(b) {
  const findings = [];
  const add = (doc, key, level, rule, message) =>
    findings.push({
      path: doc.repoRel,
      line: typeof key === "number" ? key : key ? doc.line(key) : null,
      level,
      rule,
      message,
    });
  for (const d of b.docs()) {
    if (!d.hasFm || d.fmError) {
      add(
        d,
        1,
        "error",
        "L1",
        `frontmatter を読めません: ${d.fmError || "frontmatter がありません"}`,
      );
      continue;
    }
    if (!d.type) add(d, "type", "error", "L2", "`type` が空です");
    else if (!b.types.includes(d.type))
      add(
        d,
        "type",
        "error",
        "L3",
        `\`type: ${d.type}\` は語彙表にありません（CONVENTIONS.md §2）`,
      );
    if (
      d.fm.status != null &&
      (typeof d.fm.status !== "string" ||
        !b.cfg.statuses.includes(d.fm.status.trim()))
    )
      add(
        d,
        "status",
        "error",
        "L4",
        `\`status: ${repr(d.fm.status)}\` は ${b.cfg.statuses.join("/")} のいずれか（文字列）にしてください`,
      );
    if (typeof d.fm.layer !== "string" || !b.layers.includes(d.fm.layer.trim()))
      add(
        d,
        "layer",
        "error",
        "L5",
        `\`layer\` は ${b.layers.join("/")} のいずれかが必要です（現在: ${repr(d.fm.layer)}）`,
      );
    if (d.fm.generated != null) {
      const p = actorProblem(d.fm.generated, "generated");
      if (p) add(d, "generated", "warn", "L6", p);
    }
    const verified = d.fm.verified;
    if (verified != null) {
      if (!Array.isArray(verified))
        add(
          d,
          "verified",
          "warn",
          "L6",
          `\`verified\` はリストである必要があります（現在: ${typeName(verified)}）`,
        );
      else if (!verified.length)
        add(d, "verified", "warn", "L6", "`verified` が空配列です");
      else
        verified.forEach((v, i) => {
          const p = actorProblem(v, `verified[${i + 1}]`);
          if (p) add(d, "verified", "warn", "L6", p);
        });
    }
    if ((d.description.match(/[。！？]|[.!?](?=\s|$)/g) || []).length > 1)
      add(
        d,
        "description",
        "warn",
        "L9",
        "`description` は一文にしてください（文末記号が 2 つ以上あります）",
      );
    if ([...d.description].length > 120)
      add(
        d,
        "description",
        "warn",
        "L9",
        `\`description\` が 120 字を超えています（${[...d.description].length} 字）`,
      );
    const globs = d.fm.code_globs;
    if (globs != null) {
      if (!Array.isArray(globs))
        add(
          d,
          "code_globs",
          "error",
          "L10",
          `\`code_globs\` はリストである必要があります（現在: ${typeName(globs)}）`,
        );
      else
        globs.forEach((v, i) => {
          if (typeof v !== "string" || !v.trim())
            add(
              d,
              "code_globs",
              "error",
              "L10",
              `\`code_globs[${i + 1}]\` が空、または文字列ではありません`,
            );
        });
    }
    if (
      !d.globs.length &&
      d.status !== "deprecated" &&
      ["Project Overview", "Architecture", "Reference", "How-To"].includes(
        d.type,
      )
    )
      add(
        d,
        "type",
        "warn",
        "L10",
        `\`code_globs\` がありません（type: ${d.type} はコード由来なので更新検知の起点が必要です）`,
      );
    for (const g of d.globs)
      if (!b.resources(g).length)
        add(
          d,
          "code_globs",
          "warn",
          "L10",
          `\`code_globs: ${g}\` にマッチするファイルがありません`,
        );
    const sources = d.fm.sources;
    if (sources != null) {
      if (!Array.isArray(sources))
        add(
          d,
          "sources",
          "warn",
          "L14",
          `\`sources\` はリストである必要があります（現在: ${typeName(sources)}）`,
        );
      else
        sources.forEach((s, i) => {
          if (!isMap(s))
            add(
              d,
              "sources",
              "warn",
              "L14",
              `\`sources[${i + 1}]\` はマップ（\`- resource: ...\`）である必要があります`,
            );
          else if (typeof s.resource !== "string" || !s.resource.trim())
            add(
              d,
              "sources",
              "warn",
              "L14",
              `\`sources[${i + 1}].resource\` が空、または文字列ではありません`,
            );
        });
    }
    const related = d.fm.related;
    if (related != null && !Array.isArray(related))
      add(
        d,
        "related",
        "warn",
        "L11",
        `\`related\` はリストである必要があります（現在: ${typeName(related)}）`,
      );
    else if (Array.isArray(related))
      for (const href of related) {
        if (typeof href !== "string" || !href.trim()) {
          add(
            d,
            "related",
            "warn",
            "L11",
            `\`related\` の要素が文字列ではありません: ${repr(href)}`,
          );
          continue;
        }
        const target = href.split("#")[0].trim();
        if (!target || /^https?:\/\//.test(target)) continue;
        const candidate = path.resolve(
          target.startsWith("/") ? b.root : path.dirname(d.path),
          target.replace(/^\//, ""),
        );
        try {
          inside(b.root, candidate);
        } catch {
          add(
            d,
            "related",
            "warn",
            "L11",
            `\`related\` はバンドル（${rel(b.root, b.repo)}/）内を指す必要があります: ${href}`,
          );
          continue;
        }
        if (!fs.existsSync(candidate))
          add(
            d,
            "related",
            "warn",
            "L11",
            `\`related\` のリンク先が存在しません: ${href}`,
          );
      }
    if (d.type === "Backlog Item") {
      const state = d.fm.state;
      if (typeof state !== "string" || !b.backlog.states.includes(state.trim()))
        add(
          d,
          "state",
          "error",
          "L12",
          `\`state\` は ${b.backlog.states.join("/")} のいずれかが必要です（現在: ${repr(state)}）`,
        );
      else if (state.trim() === "done" && !dateOnly(d.fm.done_at))
        add(
          d,
          "done_at",
          "error",
          "L12",
          `\`state: done\` には \`done_at: YYYY-MM-DD\`（実在する日付）が必要です（現在: ${repr(d.fm.done_at)}）`,
        );
    }
  }
  for (const dir of b.dirs()) {
    const index = path.join(dir, "index.md"),
      log = path.join(dir, "log.md");
    if (fs.existsSync(index)) {
      const d = new Doc(index, b);
      if (d.fmOpened && !d.hasFm)
        add(
          d,
          1,
          "error",
          "L7",
          `index.md の frontmatter が壊れています: ${d.fmError}`,
        );
      else if (d.hasFm && d.fmError)
        add(
          d,
          1,
          "error",
          "L7",
          `index.md の frontmatter を読めません: ${d.fmError}`,
        );
      else if (
        d.hasFm &&
        !(dir === b.root && Object.keys(d.fm).every((k) => k === "okf_version"))
      )
        add(
          d,
          1,
          "error",
          "L7",
          "index.md は frontmatter を持てません（ルートの `okf_version` のみ例外）",
        );
    }
    if (fs.existsSync(log)) {
      const d = new Doc(log, b);
      if (d.fmOpened)
        add(
          d,
          1,
          "error",
          "L7",
          "log.md は frontmatter を持てません（OKF v0.2 §8 の予約ファイル）",
        );
      let prev = null;
      const seen = new Map();
      d.text.split("\n").forEach((line, i) => {
        if (!line.startsWith("## ")) return;
        const heading = line.slice(3).trim();
        if (!dateOnly(heading)) {
          add(
            d,
            i + 1,
            "warn",
            "L8",
            `見出しが ISO 8601 の実在する日付ではありません: ${heading}`,
          );
          return;
        }
        if (seen.has(heading))
          add(
            d,
            i + 1,
            "warn",
            "L8",
            `日付見出しが重複しています: ${heading}（${seen.get(heading)} 行目にもあります）`,
          );
        else seen.set(heading, i + 1);
        if (prev && heading > prev)
          add(
            d,
            i + 1,
            "warn",
            "L8",
            `日付見出しが新しい順になっていません: ${prev} の後に ${heading}`,
          );
        prev = heading;
      });
    }
    try {
      const content = renderIndex(b, dir);
      if (!fs.existsSync(index) || read(index) !== content)
        findings.push({
          path: rel(index, b.repo),
          line: null,
          level: "error",
          rule: "L13",
          message:
            "index.md が最新ではありません（`okf index --write` を実行してください）",
        });
    } catch (e) {
      if (!(e instanceof MarkerError)) throw e;
      findings.push({
        path: rel(index, b.repo),
        line: null,
        level: "error",
        rule: "L13",
        message: e.message,
      });
    }
  }
  return findings.sort(
    (a, c) =>
      compare(a.path, c.path) ||
      (a.line || 0) - (c.line || 0) ||
      compare(a.rule, c.rule),
  );
}
export function cmdLint(b, args = {}) {
  const findings = runLint(b);
  findings.forEach((f) => console.log(findingText(f)));
  const errors = findings.filter((f) => f.level === "error").length,
    warns = findings.length - errors;
  console.log(`\nlint: error ${errors} 件 / warn ${warns} 件`);
  return errors || (warns && args.strict) ? 1 : 0;
}
export function runStale(b) {
  const results = [],
    times = pathTimes(b.repo),
    date = today();
  for (const d of b.docs()) {
    if (!d.hasFm) continue;
    const add = (kind, level, message) =>
      results.push({ path: d.repoRel, kind, level, message });
    const raw = d.fm.generated?.at,
      gen = timestamp(raw),
      genDate = extractDate(raw),
      expiry = extractDate(d.fm.stale_after);
    if (expiry && expiry <= date)
      add("expired", "warn", `stale_after: ${expiry} を過ぎています`);
    for (const g of d.globs) {
      const files = b.resources(g);
      if (!files.length) {
        add(
          "orphan",
          "warn",
          `code_globs: ${g} にマッチするファイルがありません`,
        );
        continue;
      }
      if (gen === null) continue;
      const dates = files
        .map((p) => times.get(p))
        .filter(Boolean)
        .sort((a, c) => timestamp(c) - timestamp(a));
      if (!dates.length) continue;
      const latest = dates[0],
        hasTime = !dateOnly(raw),
        shown = hasTime
          ? new Date(timestamp(latest)).toISOString().replace(/\.000Z$/, "Z")
          : latest.slice(0, 10);
      if (hasTime ? timestamp(latest) > gen : shown > genDate)
        add(
          "outdated",
          "warn",
          `${g} の最終コミット ${shown} > generated.at ${raw}`,
        );
    }
    if (trust(d) === "unverified")
      add(
        "unverified",
        "info",
        "verified がありません（人によるレビュー未実施）",
      );
    const age = genDate
      ? Math.floor((Date.parse(date) - Date.parse(genDate)) / 86400000)
      : 0;
    if (
      d.status === "draft" &&
      genDate &&
      age >= (b.cfg.stale?.draft_days ?? 30)
    )
      add(
        "draft-stale",
        "info",
        `status: draft のまま ${age} 日経過しています`,
      );
  }
  return results.sort(
    (a, c) =>
      Number(a.level !== "warn") - Number(c.level !== "warn") ||
      compare(a.path, c.path) ||
      compare(a.kind, c.kind),
  );
}
export function cmdStale(b, args = {}) {
  if (isShallow(b.repo))
    console.error(
      "[okf stale] 警告: shallow clone のため outdated 判定が不正確になる可能性があります。",
    );
  const result = runStale(b);
  if (args.format === "json") console.log(JSON.stringify(result, null, 2));
  else if (!result.length) console.log("陳腐化の兆候はありません。");
  else {
    result.forEach((r) =>
      console.log(`${r.path} ${r.level} ${r.kind} ${r.message}`),
    );
    const warns = result.filter((r) => r.level === "warn").length;
    console.log(`\nstale: warn ${warns} 件 / info ${result.length - warns} 件`);
  }
  return 0;
}
