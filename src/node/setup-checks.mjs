import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Bundle, OkfError, git, inside, isMap, read, rel } from "./core.mjs";
import { agentSettings, scaffoldPlan } from "./scaffold.mjs";

const packageManifest = new URL("../../package.json", import.meta.url);
export const packageVersion = () => JSON.parse(read(fileURLToPath(packageManifest))).version;

function reportHook(root, name, file) {
  try {
    inside(root, path.join(root, file));
    const target = path.join(root, file);
    if (!fs.existsSync(target)) return "未登録";
    const settings = JSON.parse(read(target));
    if (!isMap(settings)) throw new OkfError("設定の形式が不正です");
    if (!Object.hasOwn(settings, "hooks")) return "未登録";
    if (!isMap(settings.hooks)) throw new OkfError("hooks の形式が不正です");
    const eventName = name === "copilot" ? "agentStop" : "Stop";
    if (!Object.hasOwn(settings.hooks, eventName)) return "未登録";
    const event = settings.hooks[eventName];
    if (!Array.isArray(event) || event.some((group) => !isMap(group) ||
        (name !== "copilot" && !Array.isArray(group.hooks))))
      throw new OkfError("hook イベントの形式が不正です");
    const entries = name === "copilot" ? event : event.flatMap((group) => group.hooks);
    return entries.some((entry) => ["command", "commandWindows", "bash", "powershell"].some((key) =>
      typeof entry?.[key] === "string" && /\.okf[\\/]hooks[\\/]agent_stop\.(?:sh|ps1)\b/.test(entry[key]),
    )) ? "登録あり（設定のみ確認）" : "OKF の登録を確認できません";
  } catch {
    return "判定不能（設定を確認してください）";
  }
}

function validatedLayers(bundle) {
  if (!fs.statSync(bundle.root, { throwIfNoEntry: false })?.isDirectory())
    throw new OkfError(`バンドルルートがありません: ${bundle.root}`);
  if (!Array.isArray(bundle.layers) ||
      bundle.layers.some((name) => typeof name !== "string" || !name.trim()))
    throw new OkfError("layers は空でない層名のリストで指定してください");
  const maps = bundle.cfg.layer_map;
  if (!Array.isArray(maps)) throw new OkfError("layer_map はリストで指定してください");
  if (maps.some((entry) => typeof entry?.glob !== "string" || typeof entry?.layer !== "string"))
    throw new OkfError("layer_map の各項目に glob と layer が必要です");
  if (!isMap(bundle.cfg.layer_dirs)) throw new OkfError("layer_dirs はマップで指定してください");
  return maps;
}

export function cmdDoctor(root, config) {
  console.log("CLI: okf-devkit " + packageVersion() + " (Node.js)");
  const entry = process.argv[1] || fileURLToPath(new URL("./cli.mjs", import.meta.url));
  console.log("CLI 実体: " + fs.realpathSync(entry));
  console.log("導入元: 不明");
  let bundle;
  let failed = false;
  try {
    const candidate = new Bundle(root, config);
    const maps = validatedLayers(candidate);
    bundle = candidate;
    console.log("設定: 読み込み成功");
    for (const entry of maps) {
      if (entry.layer === "skip") continue;
      const count = bundle.resources(entry.glob).length;
      console.log("layer_map " + entry.layer + " (" + entry.glob + "): " +
        (count ? count + " 件一致" : "要確認（一致なし）"));
    }
  } catch (error) {
    failed = true;
    console.log("設定 / layer_map: 要確認 (" + error.message + ")");
  }
  for (const [name, file] of agentSettings)
    console.log("hook " + name + " (" + file + "): " + reportHook(root, name, file));
  const ignores = ["_site/index.html", ".okf/render-backups/"];
  if (fs.existsSync(path.join(root, "package.json"))) ignores.push("node_modules/");
  for (const item of ignores) {
    const [code] = git(root, "check-ignore", "--no-index", "-q", "--", item);
    const result = code === 0 ? "除外済み" : code === 1 ? "要確認（除外なし）" : "判定不能（Git）";
    console.log("Git 除外 " + item + ": " + result);
  }
  let legacy = null;
  try {
    if (bundle) {
      legacy = bundle.dirs().flatMap((dir) => fs.readdirSync(dir, { withFileTypes: true })
        .filter((entry) => entry.isFile() && entry.name.endsWith(".html"))
        .map((entry) => path.join(dir, entry.name))
        .filter((file) => !bundle.excluded(file)));
      const oldManifest = path.join(bundle.root, ".okf-render-manifest.json");
      if (fs.lstatSync(oldManifest, { throwIfNoEntry: false })?.isFile()) legacy.push(oldManifest);
      legacy.sort();
    }
  } catch { /* Other checks do not depend on scanning the bundle. */ }
  console.log("旧出力候補: " + (legacy === null ? "判定不能（バンドル）" : legacy.length + " 件"));
  for (const file of legacy || []) console.log("  " + rel(file, root));
  return failed ? 1 : 0;
}

function normalizeScaffold(text) {
  if (!text.startsWith("---\n")) return text;
  const end = text.indexOf("\n---\n", 3);
  if (end < 0) return text;
  const header = text.slice(0, end).replace(
    /^generated:\n( {2}by:[^\n]*\n) {2}at:[^\n]*$/m, "generated:\n$1  at: <timestamp>",
  );
  return header + text.slice(end);
}

export function cmdUpgrade(bundle, args) {
  const maps = validatedLayers(bundle);
  const logFiles = new Map([["log.md", bundle.logPath("shared")]]);
  const layers = bundle.layers.filter((name) => name !== "shared").map((name) => ({
    name,
    glob: maps.find((entry) => entry.layer === name)?.glob || "**",
    dir: bundle.cfg.layer_dirs?.[name] || name,
  }));
  for (const layer of layers) logFiles.set(layer.dir + "/log.md", bundle.logPath(layer.name));
  const bundleRoot = rel(bundle.root, bundle.repo) || ".";
  const { plan } = scaffoldPlan(bundle.repo, {
    bundleRoot,
    siteName: bundle.siteName,
    agent: args.agent,
    runner: args.runner,
  }, layers, { allowRepoRoot: true });
  const counts = { "一致": 0, "追加候補": 0, "差分あり（手動確認）": 0, "比較不能（手動確認）": 0 };
  for (let [file, expected] of plan) {
    const timestamped = [bundleRoot + "/AGENTS.md", bundleRoot + "/CONVENTIONS.md"].includes(file);
    if (file === "okf.yml") file = rel(bundle.configPath, bundle.repo);
    else if (file.startsWith(bundleRoot + "/")) {
      const logFile = logFiles.get(file.slice(bundleRoot.length + 1));
      if (logFile) file = rel(logFile, bundle.repo);
      else if (bundleRoot === ".") file = file.slice(2);
    }
    const target = path.join(bundle.repo, file);
    let status;
    try {
      inside(bundle.repo, target);
      const stat = fs.lstatSync(target, { throwIfNoEntry: false });
      if (!stat) status = "追加候補";
      else if (!stat.isFile()) status = "比較不能（手動確認）";
      else {
        const actual = read(target);
        const equal = timestamped ? normalizeScaffold(actual) === normalizeScaffold(expected) : actual === expected;
        status = equal ? "一致" : "差分あり（手動確認）";
      }
    } catch {
      status = "比較不能（手動確認）";
    }
    counts[status]++;
    console.log(status + ": " + file);
  }
  console.log(Object.entries(counts).map(([status, count]) => status + " " + count + " 件").join(" / "));
  return counts["比較不能（手動確認）"] ? 1 : 0;
}
