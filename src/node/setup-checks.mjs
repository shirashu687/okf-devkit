import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Bundle, OkfError, git, inside, read, rel } from "./core.mjs";
import { agentSettings, scaffoldPlan } from "./scaffold.mjs";

const packageManifest = new URL("../../package.json", import.meta.url);
export const packageVersion = () => JSON.parse(read(fileURLToPath(packageManifest))).version;

function reportHook(root, name, file) {
  try {
    inside(root, path.join(root, file));
    const target = path.join(root, file);
    if (!fs.existsSync(target)) return "未登録";
    const hooks = JSON.parse(read(target))?.hooks;
    const event = hooks?.[name === "copilot" ? "agentStop" : "Stop"];
    if (!Array.isArray(event)) return "未登録";
    const entries = name === "copilot" ? event : event.flatMap((group) => group?.hooks || []);
    return entries.some((entry) => ["command", "commandWindows", "bash", "powershell"].some((key) =>
      typeof entry?.[key] === "string" && /\.okf[\\/]hooks[\\/]agent_stop\.(?:sh|ps1)\b/.test(entry[key]),
    )) ? "登録あり（設定のみ確認）" : "OKF の登録を確認できません";
  } catch {
    return "判定不能（設定を確認してください）";
  }
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
    if (!Array.isArray(candidate.layers) ||
        candidate.layers.some((name) => typeof name !== "string" || !name.trim()))
      throw new OkfError("layers は空でない層名のリストで指定してください");
    bundle = candidate;
    console.log("設定: 読み込み成功");
    if (!Array.isArray(bundle.cfg.layer_map))
      throw new OkfError("layer_map はリストで指定してください");
    for (const entry of bundle.cfg.layer_map) {
      if (typeof entry?.glob !== "string" || typeof entry.layer !== "string")
        throw new OkfError("layer_map の各項目に glob と layer が必要です");
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
  const ignores = ["_site/", ".okf/render-backups/"];
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
      if (fs.statSync(oldManifest, { throwIfNoEntry: false })?.isFile()) legacy.push(oldManifest);
      legacy.sort();
    }
  } catch { /* Other checks do not depend on scanning the bundle. */ }
  console.log("旧出力候補: " + (legacy === null ? "判定不能（バンドル）" : legacy.length + " 件"));
  for (const file of legacy || []) console.log("  " + rel(file, root));
  return failed ? 1 : 0;
}

function normalizeScaffold(text) {
  return text.replace(/^generated:\n( {2}by:[^\n]*\n) {2}at:[^\n]*$/m, "generated:\n$1  at: <timestamp>");
}

export function cmdUpgrade(bundle, args) {
  const logFiles = new Map([["log.md", bundle.logPath("shared")]]);
  const layers = bundle.layers.filter((name) => name !== "shared").map((name) => ({
    name,
    glob: bundle.cfg.layer_map?.find((entry) => entry.layer === name)?.glob || "**",
    dir: bundle.cfg.layer_dirs?.[name] || name,
  }));
  for (const layer of layers) logFiles.set(layer.dir + "/log.md", bundle.logPath(layer.name));
  const bundleRoot = rel(bundle.root, bundle.repo);
  const { plan } = scaffoldPlan(bundle.repo, {
    bundleRoot,
    siteName: bundle.siteName,
    agent: args.agent,
    runner: args.runner,
  }, layers);
  const counts = { "一致": 0, "追加候補": 0, "差分あり（手動確認）": 0, "比較不能（手動確認）": 0 };
  for (let [file, expected] of plan) {
    if (file === "okf.yml") file = rel(bundle.configPath, bundle.repo);
    else if (file.startsWith(bundleRoot + "/")) {
      const logFile = logFiles.get(file.slice(bundleRoot.length + 1));
      if (logFile) file = rel(logFile, bundle.repo);
    }
    const target = path.join(bundle.repo, file);
    let status;
    try {
      inside(bundle.repo, target);
      const stat = fs.lstatSync(target, { throwIfNoEntry: false });
      if (!stat) status = "追加候補";
      else if (!stat.isFile()) status = "比較不能（手動確認）";
      else status = normalizeScaffold(read(target)) === normalizeScaffold(expected)
        ? "一致" : "差分あり（手動確認）";
    } catch {
      status = "比較不能（手動確認）";
    }
    counts[status]++;
    console.log(status + ": " + file);
  }
  console.log(Object.entries(counts).map(([status, count]) => status + " " + count + " 件").join(" / "));
  return counts["比較不能（手動確認）"] ? 1 : 0;
}
