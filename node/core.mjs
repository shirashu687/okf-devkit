import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import YAML from "yaml";

export const dataDir = fileURLToPath(
  new URL("../src/okf_devkit/", import.meta.url),
);
export class OkfError extends Error {}
export class MarkerError extends OkfError {}
export const slash = (value) => value.replaceAll("\\", "/");
export const rel = (file, root) => slash(path.relative(root, file));
export const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
export const isMap = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);
export const read = (file) =>
  fs
    .readFileSync(file, "utf8")
    .replace(/^\uFEFF/, "")
    .replace(/\r\n?/g, "\n");
export const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
export const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
export const dateOnly = (value) =>
  typeof value === "string" &&
  /^\d{4}-\d{2}-\d{2}$/.test(value) &&
  Number.isFinite(Date.parse(value)) &&
  new Date(value).toISOString().slice(0, 10) === value;
export const extractDate = (value) => {
  const s = String(value ?? "").match(/\d{4}-\d{2}-\d{2}/)?.[0];
  return dateOnly(s) ? s : null;
};
export function timestamp(value) {
  if (typeof value !== "string" || !extractDate(value)) return null;
  if (dateOnly(value)) return Date.parse(value);
  const s = value.replace(" ", "T");
  const time = s.match(/^\d{4}-\d{2}-\d{2}T(\d\d):(\d\d)(?::(\d\d))?/);
  if (
    !time ||
    Number(time[1]) > 23 ||
    Number(time[2]) > 59 ||
    Number(time[3] || 0) > 59
  )
    return null;
  const result = Date.parse(
    /[zZ]|[+-]\d\d:?\d\d$/.test(s.slice(10)) ? s : `${s}Z`,
  );
  return Number.isFinite(result) ? result : null;
}
export function parseYaml(text, source = "<yaml>") {
  try {
    // YAML 1.1 matches PyYAML's booleans, dates and numeric scalars.
    const doc = YAML.parseDocument(text, { version: "1.1", uniqueKeys: true });
    if (doc.errors.length) throw doc.errors[0];
    YAML.visit(doc, {
      Scalar(_key, node) {
        if (node.value instanceof Date) {
          const source = node.source || "";
          const components = source.match(
            /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[Tt\s]+(\d{1,2}):(\d{1,2}):(\d{1,2}))?/,
          );
          if (components) {
            const [, year, month, day, hour, minute, second] = components;
            if (
              !dateOnly(
                `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`,
              ) ||
              Number(hour || 0) > 23 ||
              Number(minute || 0) > 59 ||
              Number(second || 0) > 59
            )
              throw new Error("実在しない日時です");
          }
          if (/^\d{4}-\d{2}-\d{2}$/.test(source)) {
            if (!dateOnly(source)) throw new Error("実在しない日付です");
            node.value = source;
          } else
            node.value = node.value.toISOString().replace(/\.\d{3}Z$/, "Z");
        }
      },
    });
    const value = doc.toJS({ maxAliasCount: 100 });
    const normalize = (v, seen = new Set()) => {
      if (v instanceof Date)
        return v.toISOString().replace(/\.000Z$/, "+00:00");
      if (v && typeof v === "object") {
        if (seen.has(v)) throw new Error("循環する YAML alias は非対応です");
        seen.add(v);
        const result = Array.isArray(v)
          ? v.map((x) => normalize(x, seen))
          : Object.fromEntries(
              Object.entries(v).map(([k, x]) => [k, normalize(x, seen)]),
            );
        seen.delete(v);
        return result;
      }
      return v;
    };
    return normalize(value);
  } catch (e) {
    throw new OkfError(`${source}: YAML を読めません: ${e.message}`);
  }
}
export function scalar(value) {
  if (value === null) return "null";
  if (typeof value !== "string") return String(value);
  if (/[\r\n]/.test(value))
    throw new OkfError("frontmatter の値に改行は使えません");
  if (!value) return '""';
  let ambiguous =
    !/^[^\s"'#&*!|>%@`\[\]{},:][^:#]*$/.test(value) ||
    value !== value.trim() ||
    value.endsWith(":") ||
    /^\d{4}-\d{2}-\d{2}/.test(value);
  try {
    ambiguous ||= parseYaml(value) !== value;
  } catch {
    ambiguous = true;
  }
  return ambiguous
    ? `"${value.replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`
    : value;
}
export const flow = (values) => `[${values.map(scalar).join(", ")}]`;
export function write(file, content) {
  const data = Buffer.from(content.replaceAll("\r\n", "\n"));
  if (fs.existsSync(file) && fs.readFileSync(file).equals(data)) return false;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = path.join(
    path.dirname(file),
    `.${path.basename(file)}.${randomUUID()}.okftmp`,
  );
  let fd;
  try {
    fd = fs.openSync(tmp, "wx");
    fs.writeFileSync(fd, data);
    fs.fsyncSync(fd);
    fs.closeSync(fd);
    fd = undefined;
    for (let i = 0; ; i++) {
      try {
        fs.renameSync(tmp, file);
        break;
      } catch (e) {
        if (i >= 4 || !["EPERM", "EACCES", "EBUSY"].includes(e.code)) throw e;
        Atomics.wait(
          new Int32Array(new SharedArrayBuffer(4)),
          0,
          0,
          50 * (i + 1),
        );
      }
    }
    return true;
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
    if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
  }
}
export function realPath(file) {
  const absolute = path.resolve(file);
  if (fs.existsSync(absolute)) return fs.realpathSync(absolute);
  const parent = path.dirname(absolute);
  return parent === absolute
    ? absolute
    : path.join(realPath(parent), path.basename(absolute));
}
export function inside(root, file) {
  const resolved = realPath(file),
    relative = path.relative(realPath(root), resolved);
  if (
    relative === ".." ||
    relative.startsWith(`..${path.sep}`) ||
    path.isAbsolute(relative)
  )
    throw new OkfError(`指定範囲の外には作成できません: ${file}`);
  return resolved;
}
const globCache = new Map();
export function matches(file, pattern) {
  if (!globCache.has(pattern)) {
    let rx = "";
    for (let i = 0; i < pattern.length; ) {
      const c = pattern[i];
      if (pattern.startsWith("**/", i)) {
        rx += "(?:.*/)?";
        i += 3;
      } else if (pattern.startsWith("**", i)) {
        rx += ".*";
        i += 2;
      } else if (c === "*") {
        rx += "[^/]*";
        i++;
      } else if (c === "?") {
        rx += "[^/]";
        i++;
      } else if (c === "[" && pattern.indexOf("]", i + 1) > i + 1) {
        const end = pattern.indexOf("]", i + 1);
        rx += `[${pattern.slice(i + 1, end).replace(/^[!^]/, "^")}]`;
        i = end + 1;
      } else {
        rx += c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        i++;
      }
    }
    globCache.set(pattern, new RegExp(`^${rx}$`));
  }
  return globCache.get(pattern).test(file);
}
export function git(root, ...args) {
  const proc = spawnSync("git", args, {
    cwd: root,
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 64 * 1024 * 1024,
  });
  return [proc.status ?? 127, proc.stdout || ""];
}
export function projectRoot(start = process.cwd()) {
  for (let d = path.resolve(start); ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, "okf.yml"))) return d;
    if (path.dirname(d) === d) break;
  }
  const [code, out] = git(start, "rev-parse", "--show-toplevel");
  return code === 0 && out.trim()
    ? path.resolve(out.trim())
    : path.resolve(start);
}
export function merge(base, override) {
  const result = { ...base };
  for (const [key, value] of Object.entries(override))
    Object.defineProperty(result, key, {
      value:
        isMap(value) && isMap(result[key]) ? merge(result[key], value) : value,
      enumerable: true,
      writable: true,
      configurable: true,
    });
  return result;
}
export class Doc {
  constructor(file, bundle) {
    this.path = file;
    this.repoRel = rel(file, bundle.repo);
    this.bundleRel = "/" + rel(file, bundle.root);
    this.name = path.basename(file);
    this.text = read(file);
    this.body = this.text;
    this.fm = {};
    this.fmLines = [];
    this.hasFm = false;
    this.fmOpened = false;
    this.fmError = null;
    const lines = this.text.split("\n");
    if (lines[0]?.trim() === "---") {
      this.fmOpened = true;
      const end = lines.findIndex(
        (line, i) => i > 0 && ["---", "..."].includes(line.trim()),
      );
      if (end < 0) this.fmError = "frontmatter の終端 `---` がありません";
      else {
        this.hasFm = true;
        this.fmLines = lines.slice(1, end);
        this.body = lines.slice(end + 1).join("\n");
        try {
          const fm = parseYaml(this.fmLines.join("\n"), this.repoRel) ?? {};
          if (!isMap(fm))
            throw new OkfError("frontmatter がマップではありません");
          this.fm = fm;
        } catch (e) {
          this.fmError = e.message;
        }
      }
    }
  }
  get(key, fallback = null) {
    return this.fm[key] ?? fallback;
  }
  line(key) {
    const i = this.fmLines.findIndex((l) => l.startsWith(`${key}:`));
    return i < 0 ? null : i + 2;
  }
  get h1() {
    return this.body.match(/^#\s+(.+?)\s*$/m)?.[1] ?? null;
  }
  get title() {
    return (
      (typeof this.fm.title === "string" && this.fm.title.trim()) ||
      this.h1 ||
      path.basename(this.path, ".md").replace(/[-_]/g, " ")
    );
  }
  get description() {
    return typeof this.fm.description === "string"
      ? this.fm.description.trim()
      : "";
  }
  get type() {
    return typeof this.fm.type === "string" ? this.fm.type.trim() : "";
  }
  get status() {
    return typeof this.fm.status === "string"
      ? this.fm.status.trim()
      : "stable";
  }
  get globs() {
    return Array.isArray(this.fm.code_globs)
      ? this.fm.code_globs
          .filter((x) => typeof x === "string" && x.trim())
          .map((x) => slash(x.trim()))
      : [];
  }
}
export class Bundle {
  constructor(repo, config = path.join(repo, "okf.yml")) {
    this.repo = repo;
    if (!fs.existsSync(config))
      throw new OkfError(
        `設定ファイルが見つかりません: ${config}（okf init で生成してください）`,
      );
    const project = parseYaml(read(config), config) ?? {};
    if (!isMap(project))
      throw new OkfError("設定ファイルはマップで指定してください");
    this.cfg = merge(
      parseYaml(read(path.join(dataDir, "defaults.yml"))),
      project,
    );
    this.root = inside(repo, path.resolve(repo, this.cfg.bundle_root));
    if (!fs.existsSync(this.root))
      throw new OkfError(`バンドルルートがありません: ${this.root}`);
    this.index = this.cfg.index;
    if (
      !isMap(this.index) ||
      !["bundle-absolute", "relative"].includes(this.index.link_style)
    )
      throw new OkfError(
        "設定 `index.link_style` は bundle-absolute / relative のいずれかで指定してください",
      );
    this.backlog = this.cfg.backlog;
    this.log = this.cfg.log;
    this.types = this.cfg.types;
    this.layers = this.cfg.layers;
    this.siteName = this.cfg.site_name || path.basename(repo);
  }
  excluded(file) {
    return (this.cfg.exclude || []).some((p) =>
      matches(rel(file, this.root), p),
    );
  }
  dirs() {
    const found = [];
    const walk = (d) => {
      found.push(d);
      for (const e of fs.readdirSync(d, { withFileTypes: true }))
        if (
          e.isDirectory() &&
          !/^[_.]/.test(e.name) &&
          !this.excluded(path.join(d, e.name))
        )
          walk(path.join(d, e.name));
    };
    walk(this.root);
    return found.sort((a, b) => compare(rel(a, this.root), rel(b, this.root)));
  }
  files(reserved = false) {
    return this.dirs().flatMap((d) =>
      fs
        .readdirSync(d, { withFileTypes: true })
        .filter(
          (e) =>
            e.isFile() &&
            e.name.endsWith(".md") &&
            (reserved || !this.cfg.reserved.includes(e.name)),
        )
        .map((e) => path.join(d, e.name))
        .filter((p) => !this.excluded(p))
        .sort(compare),
    );
  }
  docs() {
    return this.files().map((p) => new Doc(p, this));
  }
  backlogDir() {
    return inside(this.root, path.resolve(this.root, this.backlog.dir));
  }
  logPath(layer) {
    return inside(
      this.root,
      path.resolve(this.root, this.log.paths?.[layer] || `${layer}/log.md`),
    );
  }
  resources(pattern) {
    pattern = slash(pattern).replace(/^\/+/, "");
    if (!pattern) return [];
    if (!/[*?[]/.test(pattern)) {
      const file = path.resolve(this.repo, pattern);
      return fs.existsSync(file) && fs.statSync(file).isFile() ? [pattern] : [];
    }
    const parts = pattern.split("/"),
      found = new Set();
    const walk = (directory, index, relative, ancestors) => {
      if (!fs.existsSync(directory)) return;
      const stat = fs.statSync(directory);
      if (index === parts.length) {
        if (stat.isFile() && matches(relative, pattern)) found.add(relative);
        return;
      }
      if (!stat.isDirectory()) return;
      const segment = parts[index];
      const childRel = (name) => (relative ? `${relative}/${name}` : name);
      if (segment === "**") {
        walk(directory, index + 1, relative, ancestors);
        const canonical = fs.realpathSync(directory);
        if (ancestors.has(canonical)) return;
        const next = new Set([...ancestors, canonical]);
        for (const entry of fs.readdirSync(directory, {
          withFileTypes: true,
        })) {
          if (entry.name.startsWith(".")) continue;
          const child = path.join(directory, entry.name);
          if (!fs.existsSync(child)) continue;
          if (fs.statSync(child).isDirectory())
            walk(child, index, childRel(entry.name), next);
          else if (index === parts.length - 1)
            walk(child, index + 1, childRel(entry.name), next);
        }
      } else if (!/[*?[]/.test(segment)) {
        walk(
          path.join(directory, segment),
          index + 1,
          childRel(segment),
          new Set(),
        );
      } else {
        for (const entry of fs.readdirSync(directory)) {
          if (entry.startsWith(".") && !segment.startsWith(".")) continue;
          if (matches(entry, segment))
            walk(
              path.join(directory, entry),
              index + 1,
              childRel(entry),
              new Set(),
            );
        }
      }
    };
    walk(this.repo, 0, "", new Set());
    return [...found].sort(compare);
  }
}
