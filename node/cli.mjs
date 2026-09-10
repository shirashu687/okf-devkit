#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { Bundle, OkfError, git, now, projectRoot, write } from "./core.mjs";
import { cmdIndex } from "./index.mjs";
import { cmdAffected, cmdLog } from "./history.mjs";
import {
  cmdLint,
  cmdStale,
  findingText,
  runLint,
  runStale,
} from "./checks.mjs";
import { cmdInit, cmdNew, cmdStatus } from "./scaffold.mjs";
import { cmdRender } from "./renderer.mjs";

const commands = {
  init: "bundle-root site-name layer* force!",
  index: "write! check! quiet!",
  log: "write! range layer dry-run!",
  lint: "strict!",
  stale: "format",
  affected: "base paths+",
  new: "title layer type dir slug priority effort",
  status: "format",
  render: "output check! hook!",
  sync: "gate! session-id",
};
const camel = (s) => s.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
function parse(argv) {
  const args = {},
    rest = [...argv];
  // Root/config work before or after the subcommand, including `new doc`.
  for (let i = 0; i < rest.length; i++)
    for (const key of ["root", "config"])
      if (rest[i] === `--${key}` || rest[i]?.startsWith(`--${key}=`)) {
        const eq = rest[i].indexOf("=");
        const value = eq < 0 ? rest[i + 1] : rest[i].slice(eq + 1);
        if (!value || value.startsWith("--"))
          throw new OkfError(`--${key} に値が必要です`);
        args[key] = value;
        rest.splice(i, eq < 0 ? 2 : 1);
        i--;
      }
  args.command = rest.shift();
  if (!args.command || ["--help", "-h"].includes(args.command))
    return { ...args, help: true };
  if (!(args.command in commands))
    throw new OkfError(`未知のコマンド: ${args.command}`);
  if (args.command === "new") args.kind = rest.shift();
  const spec = new Map(
    commands[args.command]
      .split(" ")
      .filter(Boolean)
      .map((s) => [s.replace(/[!*+]$/, ""), s.at(-1)]),
  );
  for (let i = 0; i < rest.length; i++) {
    if (["--help", "-h"].includes(rest[i])) return { ...args, help: true };
    const match = rest[i].match(/^--([^=]+)(?:=(.*))?$/),
      key = match?.[1],
      mode = spec.get(key);
    if (!mode) throw new OkfError(`不明な引数: ${rest[i]}`);
    if (mode === "!") {
      if (match[2] !== undefined)
        throw new OkfError(`--${key} に値は指定できません`);
      args[camel(key)] = true;
      continue;
    }
    const values = match[2] !== undefined ? [match[2]] : [];
    if (!values.length) {
      while (i + 1 < rest.length && !rest[i + 1].startsWith("--")) {
        values.push(rest[++i]);
        if (mode !== "+") break;
      }
    }
    if (!values.length) throw new OkfError(`--${key} に値が必要です`);
    args[camel(key)] =
      mode === "*"
        ? [...(args[camel(key)] || []), ...values]
        : mode === "+"
          ? values
          : values[0];
  }
  args.format ??= "text";
  if (!["text", "json"].includes(args.format))
    throw new OkfError("--format は text / json で指定してください");
  if (args.command === "new") {
    if (!["doc", "backlog"].includes(args.kind))
      throw new OkfError("new doc / new backlog を指定してください");
    if (!args.title || (args.kind === "doc" && (!args.layer || !args.type)))
      throw new OkfError(
        "new には --title（doc では --layer と --type も）が必要です",
      );
    args.layer ??= "shared";
    args.priority ??= "medium";
    args.effort ??= "M";
  }
  return args;
}
async function sessionId(args) {
  const explicit =
    args.sessionId ||
    process.env.CLAUDE_SESSION_ID ||
    process.env.OKF_SESSION_ID;
  if (explicit) return explicit;
  if (process.stdin.isTTY) return null;
  return new Promise((resolve) => {
    const chunks = [];
    let size = 0,
      ended = false;
    const done = () => {
      if (ended) return;
      ended = true;
      clearTimeout(timer);
      process.stdin.pause();
      process.stdin.off("data", data);
      process.stdin.off("end", done);
      process.stdin.off("error", done);
      try {
        resolve(
          JSON.parse(Buffer.concat(chunks).toString("utf8")).session_id || null,
        );
      } catch {
        resolve(null);
      }
    };
    const data = (chunk) => {
      size += chunk.length;
      if (size > 1048576) {
        chunks.length = 0;
        done();
      } else chunks.push(chunk);
    };
    const timer = setTimeout(done, 2000);
    process.stdin.on("data", data);
    process.stdin.once("end", done);
    process.stdin.once("error", done);
    process.stdin.resume();
  });
}
function bump(root, session, fingerprint) {
  const [rc, out] = git(root, "rev-parse", "--git-path", "okf-gate");
  const dir =
    rc === 0 && out.trim()
      ? path.resolve(root, out.trim())
      : path.join(os.tmpdir(), "okf-gate");
  const key =
      String(session || "")
        .replace(/[^A-Za-z0-9_.-]/g, "_")
        .slice(0, 80) || "_nosession",
    file = path.join(dir, key + ".json");
  if (!fingerprint) {
    if (fs.existsSync(file)) fs.unlinkSync(file);
    return 0;
  }
  let prev = {};
  try {
    prev = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {}
  const same =
    prev?.fingerprint === fingerprint &&
    (session || Date.now() - fs.statSync(file).mtimeMs <= 600000);
  const count = same && Number.isInteger(prev.count) ? prev.count + 1 : 1;
  write(
    file,
    JSON.stringify({ session_id: session, fingerprint, count, at: now() }),
  );
  return count;
}
async function cmdSync(b, args) {
  const session = args.gate ? await sessionId(args) : null,
    dirty = () => {
      const [rc, out] = git(b.repo, "status", "--porcelain");
      return rc !== 0 || !!out.trim();
    };
  if (args.gate && !dirty()) return 0;
  console.log("== index ==");
  const indexRc = cmdIndex(b, { write: true });
  console.log("\n== log ==");
  try {
    cmdLog(b, { write: true });
  } catch (e) {
    console.error(`[okf log] スキップしました: ${e.message}`);
  }
  if (dirty())
    console.error(
      "[okf log] 未コミットの変更があります。今回の作業分はコミット後に `okf log --write` を実行してください。",
    );
  console.log("\n== lint ==");
  const findings = runLint(b),
    errors = findings.filter((f) => f.level === "error");
  findings.forEach((f) => console.log(findingText(f)));
  console.log(
    `lint: error ${errors.length} 件 / warn ${findings.length - errors.length} 件`,
  );
  console.log("\n== stale ==");
  const stale = runStale(b);
  if (!stale.length) console.log("陳腐化の兆候はありません。");
  stale.forEach((r) =>
    console.log(`${r.path} ${r.level} ${r.kind} ${r.message}`),
  );
  if (!args.gate) return errors.length || indexRc ? 1 : 0;
  const fingerprint = errors.length
    ? createHash("sha256")
        .update(errors.map(findingText).sort().join("\n"))
        .digest("hex")
        .slice(0, 32)
    : null;
  const count = bump(b.repo, session, fingerprint);
  if (!errors.length) return indexRc ? 2 : 0;
  if (count >= 2) {
    console.error(
      `[okf gate] lint error が ${errors.length} 件残っていますが、同じ内容で 2 回目の差し戻しになるため警告のみとします。`,
    );
    return 0;
  }
  console.error(
    "[okf gate] ドキュメントの規約違反があります。次を修正してから終了してください。\n" +
      errors.map(findingText).join("\n"),
  );
  return 2;
}
export async function main(argv = process.argv.slice(2)) {
  let args;
  try {
    args = parse(argv);
  } catch (e) {
    console.error(`エラー: ${e.message}`);
    return argv.includes("--hook") ? 1 : 2;
  }
  if (args.help) {
    console.log(
      "okf [--root DIR] [--config FILE] <command> [options]\n\n" +
        Object.entries(commands)
          .map(
            ([name, opts]) =>
              `${name.padEnd(10)} ${opts
                .split(" ")
                .map((s) => "--" + s.replace(/[!*+]$/, ""))
                .join(" ")}`,
          )
          .join("\n") +
        "\n\nnew doc: --title TITLE --layer LAYER --type TYPE\nnew backlog: --title TITLE [--layer shared]",
    );
    return 0;
  }
  try {
    const root = args.root
      ? path.resolve(args.root)
      : args.config
        ? path.dirname(path.resolve(args.config))
        : projectRoot();
    if (!fs.existsSync(root) || !fs.statSync(root).isDirectory())
      throw new OkfError(`--root がディレクトリではありません: ${root}`);
    if (args.command === "init") return cmdInit(root, args);
    const b = new Bundle(
      root,
      args.config ? path.resolve(args.config) : undefined,
    );
    return await {
      index: cmdIndex,
      log: cmdLog,
      lint: cmdLint,
      stale: cmdStale,
      affected: cmdAffected,
      new: cmdNew,
      status: cmdStatus,
      render: cmdRender,
      sync: cmdSync,
    }[args.command](b, args);
  } catch (e) {
    console.error(`エラー: ${e.message}`);
    return args.command === "sync" && args.gate ? 2 : 1;
  }
}
if (
  process.argv[1] &&
  fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)
)
  process.exitCode = await main();
