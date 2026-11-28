import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import YAML from "yaml";

export const dataDir = fileURLToPath(
  new URL("../okf_devkit/", import.meta.url),
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
const okfDatetime = /^([0-9]{4}-[0-9]{2}-[0-9]{2})[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(?:\.([0-9]+))?([Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$/;

function okfInstant(value) {
  if (typeof value !== "string") return null;
  if (dateOnly(value)) value += "T00:00:00Z";
  const match = okfDatetime.exec(value);
  if (!match || match[0] !== value || !dateOnly(match[1])) return null;
  const [, date, hour, minute, second, fraction, offset] = match;
  const seconds = Date.parse(`${date}T${hour}:${minute}:${second}${offset}`) / 1000;
  return Number.isFinite(seconds) ? [seconds, (fraction ?? "").replace(/0+$/, "")] : null;
}

const compareInstants = (a, b) => a[0] - b[0] || compare(a[1], b[1]);
export const okfValues = (value) => value == null || value === "" ? [] : Array.isArray(value) ? value : [value];
const okfActor = (value) => typeof value === "string" && /^(?:[A-Za-z][A-Za-z0-9+.-]*:\S+|[^\s/:]+\/[^\s/]+)$/.test(value);

function* usageWindowProblems(value, key, label) {
  if (isMap(value)) {
    for (const name of ["from", "to"])
      if (okfValues(value[name]).length && okfInstant(value[name]) === null)
        yield [key, `\`${label}.${name}\` は RFC 3339 ではありません`];
  }
}

export function parseYaml(text, source = "<yaml>", core = false) {
  try {
    // YAML 1.1 matches PyYAML's booleans, dates and numeric scalars.
    const doc = YAML.parseDocument(text, core
      ? { version: "1.2", schema: "core", uniqueKeys: true }
      : { version: "1.1", uniqueKeys: true });
    if (core && doc.warnings.length) throw doc.warnings[0];
    if (doc.errors.length) throw doc.errors[0];
    YAML.visit(doc, {
      Scalar(_key, node) {
        if (node.value instanceof Date) {
          const source = node.source || "";
          if (core) {
            node.value = source;
            return;
          }
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
  const data = Buffer.isBuffer(content) ? content : Buffer.from(content.replaceAll("\r\n", "\n"));
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
const skippedCodeDirs = new Set(["node_modules", "dist", ".git"]);
export const codeGlobNoMatch = (pattern, exclusions) =>
  "にマッチするファイルがありません" +
  ((/[*?[]/.test(pattern) || exclusions.length) ? "（走査除外と code_glob_exclude を確認してください）" : "");
function runGit(root, args, env) {
  const proc = spawnSync("git", args, {
    cwd: root,
    env,
    encoding: "utf8",
    windowsHide: true,
    maxBuffer: 64 * 1024 * 1024,
  });
  return [proc.status ?? 127, proc.stdout || ""];
}

export function git(root, ...args) {
  return runGit(root, args);
}

// Repository-local settings reported by `git rev-parse --local-env-vars`.
const localGitEnv = new Set([
  "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_CONFIG",
  "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_DIR", "GIT_GRAFT_FILE",
  "GIT_IMPLICIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS",
  "GIT_OBJECT_DIRECTORY", "GIT_PREFIX", "GIT_REPLACE_REF_BASE",
  "GIT_SHALLOW_FILE", "GIT_WORK_TREE",
]);

export function sourceGit(root, ...args) {
  const env = Object.fromEntries(Object.entries(process.env)
    .filter(([key]) => !localGitEnv.has(key.toUpperCase())));
  return runGit(root, args, env);
}

const codeSourceName = /^[A-Za-z][A-Za-z0-9_-]*$/;

export function splitCodeGlob(reference) {
  const separator = reference.indexOf(":");
  const name = reference.slice(0, separator);
  if (separator < 0 || !codeSourceName.test(name) || /^[A-Za-z]:[/\\]/.test(reference))
    return [null, reference];
  const pattern = slash(reference.slice(separator + 1)).replace(/^(?:\.\/)+/, "");
  if (!pattern.trim() || pattern.includes("\0") || pattern.startsWith("/") || /^[A-Za-z]:/.test(pattern) || pattern.split("/").includes(".."))
    return [name, null];
  try {
    matches("", pattern);
  } catch (error) {
    if (!(error instanceof SyntaxError)) throw error;
    return [name, null];
  }
  return [name, pattern];
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
  constructor(file, bundle, okf03 = bundle.okf03) {
    this.okf03 = okf03;
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
    if ((okf03 ? lines[0] : lines[0]?.trim()) === "---") {
      this.fmOpened = true;
      const end = lines.findIndex(
        (line, i) => i > 0 && (okf03 ? line === "---" : ["---", "..."].includes(line.trim())),
      );
      if (end < 0) this.fmError = "frontmatter の終端 `---` がありません";
      else {
        this.hasFm = true;
        this.fmLines = lines.slice(1, end);
        this.body = lines.slice(end + 1).join("\n");
        try {
          const data = parseYaml(this.fmLines.join("\n"), this.repoRel, okf03);
          const fm = okf03 ? data : data ?? {};
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
    const value = this.fm.status;
    if (this.okf03) {
      if (value == null || value === "" || (Array.isArray(value) && !value.length)) return "stable";
      return typeof value === "string" ? value.trim() : String(value);
    }
    return typeof this.fm.status === "string"
      ? this.fm.status.trim()
      : "stable";
  }
  currentTrust() {
    const generated = this.get("generated");
    const generatedAt = okfInstant(generated?.at);
    if (okfValues(generated).length && generatedAt === null) return "unverified";
    let tier = "unverified";
    for (const event of okfValues(this.get("verified"))) {
      if (!isMap(event) || !okfActor(event.by)) continue;
      const at = okfInstant(event.at);
      if (at === null || (generatedAt !== null && compareInstants(at, generatedAt) < 0)) continue;
      if (event.by.startsWith("human:")) return "human-reviewed";
      tier = "machine-confirmed";
    }
    return tier;
  }
  okfFreshness(now) {
    const value = this.get("stale_after");
    if (!okfValues(value).length) return null;
    const expires = okfInstant(value);
    if (expires === null) return "malformed";
    return compareInstants(expires, okfInstant(now.toISOString())) <= 0 ? "stale" : null;
  }
  *okfMetadataProblems() {
    const generated = this.get("generated");
    if (okfValues(generated).length && (!isMap(generated) || !okfActor(generated.by) || okfInstant(generated.at) === null))
      yield ["generated", "`generated` には Actor の by と RFC 3339 の at が必要です"];
    for (const [i, event] of okfValues(this.get("verified")).entries()) {
      if (!isMap(event) || !okfActor(event.by) || okfInstant(event.at) === null)
        yield ["verified", `\`verified[${i + 1}]\` には Actor の by と RFC 3339 の at が必要です`];
    }
    for (const [i, source] of okfValues(this.get("sources")).entries()) {
      if (!isMap(source) || typeof source.resource !== "string" || !source.resource.trim()) {
        yield ["sources", `\`sources[${i + 1}].resource\` が空、または文字列ではありません`];
        continue;
      }
      if (okfValues(source.author).length && !okfActor(source.author))
        yield ["sources", `\`sources[${i + 1}].author\` は Actor 表記ではありません`];
      if (okfValues(source.last_modified).length && okfInstant(source.last_modified) === null)
        yield ["sources", `\`sources[${i + 1}].last_modified\` は RFC 3339 ではありません`];
      yield* usageWindowProblems(source.usage_window, "sources", `sources[${i + 1}].usage_window`);
    }
    yield* usageWindowProblems(this.get("usage_window"), "usage_window", "usage_window");
    const staleAfter = this.get("stale_after");
    if (okfValues(staleAfter).length && okfInstant(staleAfter) === null)
      yield ["stale_after", "`stale_after` は RFC 3339 ではありません"];
  }
  get globs() {
    return Array.isArray(this.fm.code_globs)
      ? this.fm.code_globs
          .filter((x) => typeof x === "string" && x.trim())
          .map((x) => slash(x.trim()))
      : [];
  }
}
export function legacyPathFields(version) {
  if (version === null) return true;
  const match = /^(\d+)\.(\d+)$/.exec(version);
  return match !== null && Number(match[1]) === 0 && Number(match[2]) <= 2;
}
export function localReference(bundle, source, value, pathField = false) {
  if (!value || /^(?:#|\/\/|[a-zA-Z][a-zA-Z0-9+.-]*:)/.test(value)) return [null, "", null];
  const [, raw, suffix] = /^([^?#]*)(.*)$/s.exec(value);
  if (!raw || /%2f|%5c/i.test(raw)) return [null, suffix, null];
  let decoded;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return [null, suffix, null];
  }
  if (/[\\\x00]/.test(decoded)) return [null, suffix, null];
  const absolute = raw.startsWith("/");
  const relative = decoded.replace(/^\/+/, "");
  const primary = path.posix.normalize(absolute ? relative : path.posix.join(path.posix.dirname(source), relative)).replace(/\/$/, "");
  if (primary === ".." || primary.startsWith("../")) return [null, suffix, "outside"];
  const candidates = new Set([primary]);
  if (pathField && !absolute && legacyPathFields(bundle.declaredVersion))
    candidates.add(path.posix.normalize(relative).replace(/\/$/, ""));
  for (const candidate of candidates) {
    const parts = candidate === "." ? [] : candidate.split("/");
    if (parts.some((part) => part.startsWith("."))) continue;
    let current = bundle.root;
    let present = true;
    for (const part of parts) {
      if (!fs.lstatSync(current, { throwIfNoEntry: false })?.isDirectory()) {
        present = false;
        break;
      }
      const entry = fs.readdirSync(current, { withFileTypes: true }).find((item) => item.name === part);
      if (!entry) {
        present = false;
        break;
      }
      if (entry.isSymbolicLink()) return [null, suffix, "outside"];
      current = path.join(current, part);
    }
    if (present) return [candidate, suffix, null];
  }
  return [null, suffix, "missing"];
}

export class Bundle {
  constructor(repo, config = path.join(repo, "okf.yml")) {
    this.repo = repo;
    this.configPath = config;
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
    this.codeSourceRoots = new Map();
    this.codeGlobExclude = this.cfg.code_glob_exclude;
    if (!Array.isArray(this.codeGlobExclude) ||
        this.codeGlobExclude.some((rule) => typeof rule !== "string" || !rule.trim()))
      throw new OkfError("code_glob_exclude は空でない glob 文字列のリストで指定してください");
    try {
      for (const rule of this.codeGlobExclude) matches("", rule);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      throw new OkfError("code_glob_exclude に不正な glob があります");
    }
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
    this.declaredVersion = null;
    const rootIndex = path.join(this.root, "index.md");
    if (fs.lstatSync(rootIndex, { throwIfNoEntry: false })?.isFile()) {
      let metadata = new Doc(rootIndex, this, true);
      if (!metadata.hasFm || metadata.fmError) metadata = new Doc(rootIndex, this, false);
      const value = metadata.get("okf_version");
      if (["string", "number"].includes(typeof value) && String(value).trim())
        this.declaredVersion = String(value).trim();
    }
    const version = this.declaredVersion ?? (fs.existsSync(rootIndex) ? null : String(this.index.okf_version));
    const parts = /^(\d+)\.(\d+)$/.exec(version ?? "");
    this.okf03 = version !== null && (!parts || Number(parts[1]) > 0 || Number(parts[2]) >= 3);
  }

  codeSourceRoot(name) {
    if (this.codeSourceRoots.has(name)) return this.codeSourceRoots.get(name);
    if (!codeSourceName.test(name)) throw new OkfError(`ソース名 \`${name}\` が不正です`);
    const declarations = Object.hasOwn(this.cfg, "code_sources") ? this.cfg.code_sources : [];
    if (!Array.isArray(declarations)) throw new OkfError("`code_sources` はリストで指定してください");
    const entries = declarations.filter((entry) => isMap(entry) && entry.name === name);
    if (!entries.length) throw new OkfError(`ソース \`${name}\` が code_sources に登録されていません`);
    if (entries.length > 1) throw new OkfError(`ソース \`${name}\` の宣言が重複しています`);
    const entry = entries[0];
    let location = entry.path;
    if (typeof location !== "string" || !location.trim())
      throw new OkfError(`ソース \`${name}\` の path を指定してください`);
    if (Object.hasOwn(entry, "path_env")) {
      if (typeof entry.path_env !== "string" || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(entry.path_env))
        throw new OkfError(`ソース \`${name}\` の path_env は環境変数名で指定してください`);
      const override = process.env[entry.path_env];
      if (typeof override === "string" && override) location = override;
    }
    try {
      const absolute = path.resolve(this.repo, location);
      if (!fs.statSync(absolute, { throwIfNoEntry: false })?.isDirectory())
        throw new OkfError(`ソース \`${name}\` のチェックアウトが見つかりません`);
      const root = fs.realpathSync(absolute);
      const [rc, output] = sourceGit(root, "rev-parse", "--show-toplevel");
      const top = output.replace(/[\r\n]+$/, "");
      if (rc || !top || path.relative(root, fs.realpathSync(top)))
        throw new OkfError(`ソース \`${name}\` の配置先は Git の作業ツリールートではありません`);
      this.codeSourceRoots.set(name, root);
      return root;
    } catch (error) {
      if (error instanceof OkfError) throw error;
      throw new OkfError(`ソース \`${name}\` の配置先を確認できません`);
    }
  }
  excluded(file) {
    const relative = rel(file, this.root);
    if (this.okf03 && relative.split("/").some((part) => part.startsWith("."))) return true;
    return (this.cfg.exclude || []).some((p) => matches(relative, p));
  }
  dirs() {
    const found = [];
    const walk = (d) => {
      found.push(d);
      for (const e of fs.readdirSync(d, { withFileTypes: true }))
        if (
          e.isDirectory() &&
          this.includesDir(path.join(d, e.name))
        )
          walk(path.join(d, e.name));
    };
    walk(this.root);
    return found.sort((a, b) => compare(rel(a, this.root), rel(b, this.root)));
  }
  includesDir(directory) {
    return (this.okf03 || !/^[_.]/.test(path.basename(directory))) && !this.excluded(directory);
  }
  isReserved(name) {
    return this.cfg.reserved.includes(name) || (this.okf03 && ["index.md", "log.md"].includes(name));
  }
  files(reserved = false, directory = null) {
    return (directory ? [directory] : this.dirs()).flatMap((d) =>
      fs
        .readdirSync(d, { withFileTypes: true })
        .filter(
          (e) =>
            e.isFile() &&
            e.name.endsWith(".md") &&
            (reserved || !this.isReserved(e.name)),
        )
        .map((e) => path.join(d, e.name))
        .filter((p) => !this.excluded(p))
        .sort(compare),
    );
  }
  docs(directory = null) {
    const docs = this.files(false, directory).map((p) => new Doc(p, this));
    return this.okf03 ? docs.filter((doc) => doc.type) : docs;
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
  resources(pattern, { root = this.repo, confined = false } = {}) {
    pattern = slash(pattern).replace(/^\/+/, "");
    if (!pattern) return [];
    try {
      matches("", pattern);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      return [];
    }
    const excluded = (relative) => {
      const normalized = path.posix.normalize(relative).replace(/\/$/, "");
      return normalized !== "." && this.codeGlobExclude.some((rule) =>
        matches(normalized, rule) || matches(normalized + "/", rule),
      );
    };
    const withinSource = (file) => {
      if (!confined) return true;
      try {
        const relative = path.relative(root, fs.realpathSync(file));
        return relative !== ".." && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
      } catch (error) {
        if (["ENOENT", "ENOTDIR", "ELOOP"].includes(error.code)) return false;
        throw error;
      }
    };
    if (!/[*?[]/.test(pattern)) {
      const components = pattern.split("/");
      if (components.some((_, index) => excluded(components.slice(0, index + 1).join("/"))))
        return [];
      const file = path.resolve(root, pattern);
      return withinSource(file) && fs.existsSync(file) && fs.statSync(file).isFile() ? [pattern] : [];
    }
    const parts = pattern.split("/"),
      found = new Set();
    const walk = (directory, index, relative, ancestors) => {
      if (excluded(relative) || !withinSource(directory)) return;
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
          if (excluded(childRel(entry.name)) || !withinSource(child)) continue;
          if (!fs.existsSync(child)) continue;
          if (fs.statSync(child).isDirectory()) {
            if (!skippedCodeDirs.has(entry.name))
              walk(child, index, childRel(entry.name), next);
          }
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
          const child = path.join(directory, entry);
          if (excluded(childRel(entry)) || !withinSource(child)) continue;
          if (skippedCodeDirs.has(entry) &&
              fs.statSync(child, { throwIfNoEntry: false })?.isDirectory()) continue;
          if (matches(entry, segment))
            walk(
              child,
              index + 1,
              childRel(entry),
              new Set(),
            );
        }
      }
    };
    walk(root, 0, "", new Set());
    return [...found].sort(compare);
  }
}
