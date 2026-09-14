import fs from "node:fs";
import {
  OkfError,
  compare,
  git,
  matches,
  read,
  rel,
  slash,
  write,
} from "./core.mjs";

export const hasCommits = (root) =>
  git(root, "rev-parse", "--verify", "--quiet", "HEAD")[0] === 0;
export const isShallow = (root) =>
  git(root, "rev-parse", "--is-shallow-repository")[1].trim() === "true";
export const requireGit = (root) => {
  if (git(root, "rev-parse", "--git-dir")[0])
    throw new OkfError(
      "git リポジトリが見つかりません。リポジトリ内で実行してください。",
    );
};
export const resolveCommit = (root, ref) => {
  const [rc, out] = git(
    root,
    "rev-parse",
    "--verify",
    "--quiet",
    "--end-of-options",
    `${ref}^{commit}`,
  );
  return rc === 0 ? out.trim() : null;
};
export function layerOf(b, file) {
  for (const rule of b.cfg.layer_map || [])
    if (matches(file, String(rule.glob || "")))
      return rule.layer === "skip" ? null : rule.layer;
  return null;
}
export function parseLog(out, count) {
  const tokens = out.split("\0"),
    records = [];
  let current;
  for (let i = 0; i < tokens.length; ) {
    let token = tokens[i];
    if (!token) {
      i++;
      continue;
    }
    if (token.startsWith("@@@")) {
      const nl = token.indexOf("\n"),
        head = nl < 0 ? token : token.slice(0, nl),
        fields = head.slice(3).split("\t");
      if (fields.length > count)
        fields.splice(
          count - 1,
          fields.length - count + 1,
          fields.slice(count - 1).join("\t"),
        );
      current = { fields, paths: [] };
      records.push(current);
      if (nl >= 0 && token.slice(nl + 1)) {
        tokens[i] = token.slice(nl + 1);
        continue;
      }
      i++;
      continue;
    }
    if (!current) {
      i++;
      continue;
    }
    token = token.replace(/^\n/, "");
    const n = /^[RC]/.test(token) ? 2 : 1;
    for (let j = 1; j <= n; j++)
      if (tokens[i + j]) current.paths.push(slash(tokens[i + j]));
    i += n + 1;
  }
  return records;
}
export function statusPaths(out) {
  const tokens = out.split("\0"),
    paths = [];
  for (let i = 0; i < tokens.length; i++) {
    if (!tokens[i]) continue;
    paths.push(slash(tokens[i].slice(3)));
    if (/[RC]/.test(tokens[i].slice(0, 2)) && tokens[i + 1])
      paths.push(slash(tokens[++i]));
  }
  return paths;
}
export function changedPaths(root, base) {
  requireGit(root);
  const paths = [];
  if (hasCommits(root)) {
    const ref =
      resolveCommit(root, base) || resolveCommit(root, `origin/${base}`);
    if (!ref) throw new OkfError(`base ref を解決できませんでした: ${base}`);
    const [rc, mb] = git(root, "merge-base", ref, "HEAD");
    const [diffRc, out] =
      rc === 0
        ? git(root, "diff", "--name-only", "-z", mb.trim(), "HEAD")
        : git(root, "diff", "--name-only", "-z", ref);
    if (diffRc) throw new OkfError(`git diff に失敗しました（base: ${base}）`);
    paths.push(...out.split("\0").filter(Boolean).map(slash));
  } else
    console.error(
      "[okf affected] コミットがまだないため、作業ツリーの変更のみを対象にします。",
    );
  const [rc, out] = git(
    root,
    "status",
    "--porcelain",
    "-z",
    "--untracked-files=all",
  );
  if (rc) throw new OkfError("git status に失敗しました");
  return [...new Set([...paths, ...statusPaths(out)])].sort(compare);
}
export function cmdAffected(b, args) {
  const paths = (args.paths || changedPaths(b.repo, args.base || "main"))
    .map(slash)
    .filter((p) => !p.endsWith("/") && layerOf(b, p) !== null);
  if (!paths.length) {
    console.log("変更パスがありません。");
    return 0;
  }
  const mapping = new Map(),
    covered = new Set();
  for (const doc of b.docs()) {
    const hits = paths.filter((p) =>
      doc.globs.some((g) => matches(p, g.replace(/^\//, ""))),
    );
    if (hits.length) {
      mapping.set(doc.repoRel, [...new Set(hits)].sort(compare));
      hits.forEach((p) => covered.add(p));
    }
  }
  for (const p of [...mapping.keys()].sort(compare))
    console.log(`${p}  <- ${mapping.get(p).join(", ")}`);
  if (!mapping.size)
    console.log("更新すべきドキュメントは見つかりませんでした。");
  const uncovered = paths.filter((p) => !covered.has(p)).sort(compare);
  if (uncovered.length) {
    console.log("\n未カバー:");
    uncovered.forEach((p) => console.log(`  ${p}`));
  }
  return 0;
}
export function pathTimes(root) {
  const mapping = new Map();
  if (!hasCommits(root)) return mapping;
  const [rc, out] = git(
    root,
    "log",
    "-z",
    "--pretty=format:@@@%cI",
    "--name-status",
  );
  if (rc) throw new OkfError("git log に失敗しました");
  for (const rec of parseLog(out, 1))
    for (const p of rec.paths)
      if (!mapping.has(p)) mapping.set(p, rec.fields[0]);
  return mapping;
}
export function insertLog(text, entries) {
  const lines = text.split("\n"),
    heading = (line) => line.match(/^##\s+(\d{4}-\d{2}-\d{2})\s*$/)?.[1];
  for (const date of [...entries.keys()].sort(compare).reverse()) {
    const block = entries.get(date),
      same = lines.findIndex((l) => heading(l) === date);
    if (same >= 0) {
      lines.splice(same + 1, 0, ...block);
      continue;
    }
    const at = lines.findIndex((l) => heading(l) && heading(l) < date);
    if (at < 0) {
      while (lines.length && !lines.at(-1).trim()) lines.pop();
      lines.push("", `## ${date}`, ...block);
    } else lines.splice(at, 0, `## ${date}`, ...block, "");
  }
  return lines.join("\n").replace(/\n+$/, "") + "\n";
}
export function cmdLog(b, args = {}) {
  requireGit(b.repo);
  if (!hasCommits(b.repo)) {
    console.log("コミットがまだありません（log.md には何も追記しません）。");
    return 0;
  }
  if (isShallow(b.repo))
    console.error(
      "[okf log] 警告: shallow clone です。取得済みの履歴のみを走査します。",
    );
  const baseline = b.log.baseline
    ? resolveCommit(b.repo, String(b.log.baseline))
    : null;
  if (b.log.baseline && !baseline)
    throw new OkfError(`log.baseline を解決できません: ${b.log.baseline}`);
  if (args.layer && !b.layers.includes(args.layer))
    throw new OkfError(`--layer ${args.layer} は語彙表にありません`);
  const layers = args.layer ? [args.layer] : b.log.layers || b.layers;
  if (args.write && !baseline)
    for (const layer of layers) {
      const p = b.logPath(layer);
      if (
        fs.existsSync(p) &&
        read(p)
          .split("\n")
          .some((l) => /^\s*-\s+\S/.test(l) && !/`[0-9a-f]{7,40}`/.test(l))
      )
        throw new OkfError(
          "log.baseline が未設定で、コミットハッシュを持たない既存エントリがあります。二重追記を避けるため書き込みを中止しました。",
        );
    }
  const range = args.range || "HEAD";
  if (range.startsWith("-")) throw new OkfError("不正なリビジョン範囲です");
  const [rc, out] = git(
    b.repo,
    "log",
    "--first-parent",
    "-z",
    "--pretty=format:@@@%H\t%h\t%cs\t%s",
    "--name-status",
    range,
    ...(baseline ? [`^${baseline}`] : []),
    "--",
  );
  if (rc) throw new OkfError("git log の実行に失敗しました");
  const commits = parseLog(out, 4),
    results = [];
  let changed = 0;
  let web = git(b.repo, "remote", "get-url", "origin")[1]
    .trim()
    .replace(/\.git$/, "")
    .replace(/^git@([^:]+):/, "https://$1/");
  if (!/^https?:\/\//.test(web)) web = null;
  for (const layer of layers) {
    const file = b.logPath(layer);
    let existing = fs.existsSync(file) ? read(file) : "";
    const recorded = [...existing.matchAll(/`([0-9a-f]{7,40})`/g)].map(
        (m) => m[1],
      ),
      entries = new Map();
    let added = 0;
    for (const {
      fields: [sha, short, date, subject],
      paths,
    } of commits) {
      if (
        recorded.some((h) => sha.startsWith(h)) ||
        !paths.some((p) => layerOf(b, p) === layer)
      )
        continue;
      const pr = subject.match(/\s*\(#(\d+)\)\s*$/);
      let title = (pr ? subject.slice(0, pr.index) : subject).trim();
      if (title && !/[。．.!?！？]$/.test(title)) title += "。";
      const kind =
        b.cfg.kind_rules.find((r) => new RegExp(r.pattern, "i").test(title))
          ?.kind || "**Update**";
      const refs = [
        ...(pr
          ? [web ? `[#${pr[1]}](${web}/pull/${pr[1]})` : `#${pr[1]}`]
          : []),
        "`" + (short || sha.slice(0, 7)) + "`",
      ];
      if (!entries.has(date)) entries.set(date, []);
      entries.get(date).push(`- ${kind} ${title} (${refs.join(", ")})`);
      added++;
    }
    if (!added) continue;
    existing ||= `# ${b.log.heading_prefix}${layer}\n`;
    results.push(`${rel(file, b.repo)}: ${added} 件`);
    if (args.dryRun) {
      console.log(`--- ${rel(file, b.repo)} (dry-run) ---`);
      for (const date of [...entries.keys()].sort(compare).reverse())
        console.log(`## ${date}\n${entries.get(date).join("\n")}`);
      console.log();
    } else if (args.write)
      changed += Number(write(file, insertLog(existing, entries)));
  }
  if (!results.length) console.log("log.md に追記すべき変更はありません。");
  else {
    if (args.write)
      console.log(`log.md を更新しました（${changed} ファイル）:`);
    else if (!args.dryRun)
      console.log("追記対象（--write で書き込み / --dry-run で内容確認）:");
    results.forEach((l) => console.log(`  ${l}`));
  }
  return 0;
}
