import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { OkfError } from './core.mjs';

const manifestName = '.okf-render-manifest.json';
const marker = '<!-- okf-devkit-owned:v1 -->';
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
const posix = (p) => p.split(path.sep).join('/');
const compare = (a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b));
const fail = (message) => { throw new OkfError(`render cleanup: ${message}`); };
const contained = (root, target) => target === root || target.startsWith(root + path.sep);

export function safePath(repo, target) {
  if (/[\x00-\x1f]/.test(String(target))) fail('control character in path');
  if (String(target).split(/[\\/]/).includes('..')) fail('parent traversal in path');
  repo = path.resolve(repo); target = path.resolve(target);
  if (!contained(repo, target)) fail('path outside repository');
  if (path.relative(repo, target).includes(':')) fail('colon in path');
  let current = repo;
  for (const part of ['', ...path.relative(repo, target).split(path.sep).filter(Boolean)]) {
    if (part) current = path.join(current, part);
    let stat;
    try { stat = fs.lstatSync(current); } catch (e) { if (e.code === 'ENOENT') continue; throw e; }
    if (stat.isSymbolicLink() || path.resolve(fs.realpathSync(current)).toLowerCase() !== current.toLowerCase()) fail(`linked path: ${posix(path.relative(repo, current))}`);
  }
  return target;
}
function bytes(repo, file) {
  safePath(repo, file);
  try {
    if (!fs.lstatSync(file).isFile()) fail('artifact is not a regular file');
    return fs.readFileSync(file);
  } catch (e) { if (e.code === 'ENOENT') return null; throw e; }
}
function artifactPath(value) {
  return typeof value === 'string' && value && !/[\\:\x00-\x1f]/.test(value) && !path.posix.isAbsolute(value) && value.split('/').every(p => p && p !== '.' && p !== '..') && (value.endsWith('.html') || ['_assets/docs.css', '_assets/docs.js'].includes(value));
}
export function manifestFor(repo, output, artifacts) {
  return { version: 1, generator: 'okf-devkit', output_root: posix(path.relative(repo, output)), files: Object.keys(artifacts).sort(compare).map(p => ({ path: p, sha256: hash(Buffer.from(artifacts[p])) })) };
}
const json = (value) => JSON.stringify(value, null, 2) + '\n';
export function loadManifest(repo, output) {
  const raw = bytes(repo, path.join(output, manifestName));
  if (raw === null) return null;
  let value;
  try { value = JSON.parse(raw.toString('utf8')); } catch { fail('invalid manifest JSON'); }
  if (Object.keys(value).sort().join() !== 'files,generator,output_root,version' || value.version !== 1 || value.generator !== 'okf-devkit' || value.output_root !== posix(path.relative(repo, output)) || !Array.isArray(value.files)) fail('invalid manifest schema/root');
  const seen = new Set();
  for (const entry of value.files) {
    if (!entry || Object.keys(entry).sort().join() !== 'path,sha256' || !artifactPath(entry.path) || !/^[0-9a-f]{64}$/.test(entry.sha256) || seen.has(entry.path)) fail('invalid manifest artifact');
    seen.add(entry.path);
  }
  return value;
}
export function writeManifest(repo, output, artifacts) {
  safePath(repo, output);
  const dest = path.join(output, manifestName);
  bytes(repo, dest);
  const temp = dest + '.' + randomUUID() + '.tmp';
  try { fs.writeFileSync(temp, json(manifestFor(repo, output, artifacts)), { flag: 'wx' }); safePath(repo, dest); fs.renameSync(temp, dest); }
  finally { if (fs.existsSync(temp)) fs.unlinkSync(temp); }
}
export function planCleanup(repo, output, old, artifacts, legacyArtifacts) {
  repo = path.resolve(repo); output = safePath(repo, output); old = safePath(repo, old);
  const backups = path.join(repo, '.okf', 'render-backups');
  if ([old, output].some(p => p === repo || contained(p, backups) || contained(backups, p)) || contained(old, output) || contained(output, old)) fail('roots must be distinct, non-nested repository directories outside backup storage');
  safePath(repo, backups);
  if (fs.existsSync(backups) && !fs.lstatSync(backups).isDirectory()) fail('backup storage is not a directory');
  const targetManifest = loadManifest(repo, output);
  for (const [p, content] of Object.entries(artifacts)) {
    const existing = bytes(repo, path.join(output, p));
    if (existing !== null && hash(existing) !== hash(Buffer.from(content))) {
      const previous = targetManifest?.files.find(e => e.path === p);
      if (!previous || previous.sha256 !== hash(existing) || (p.endsWith('.html') && !existing.subarray(0, 256).toString().includes(marker))) fail(`conflicting target artifact: ${p}`);
    }
  }
  const oldManifest = loadManifest(repo, old);
  const entries = oldManifest?.files || manifestFor(repo, old, legacyArtifacts).files;
  const moves = [], keeps = [];
  const known = new Set(entries.map(e => e.path));
  for (const entry of entries) {
    const file = path.join(old, entry.path), data = bytes(repo, file);
    const relative = posix(path.relative(repo, file));
    const reason = data === null ? 'missing' : hash(data) !== entry.sha256 ? 'modified' : entry.path.endsWith('.html') && !data.subarray(0, 256).toString().includes(marker) ? 'modified' : null;
    if (reason) keeps.push({ path: relative, reason });
    else moves.push({ path: relative, sha256: entry.sha256 });
  }
  const walk = (dir) => {
    if (!fs.existsSync(dir)) return;
    safePath(repo, dir);
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const file = path.join(dir, entry.name), relative = posix(path.relative(old, file));
      if (entry.isSymbolicLink()) fail(`linked path: ${relative}`);
      if (entry.isDirectory()) walk(file);
      else if (relative !== manifestName && !known.has(relative)) keeps.push({ path: posix(path.relative(repo, file)), reason: 'untracked' });
    }
  };
  walk(old);
  moves.sort((a,b) => compare(a.path,b.path)); keeps.sort((a,b) => compare(a.path,b.path));
  return { repo, output, old, moves, keeps };
}
export function printPlan(plan) {
  const lines = [...plan.moves.map(item => `cleanup move: ${item.path}`), ...plan.keeps.map(item => `cleanup keep: ${item.path} (${item.reason})`)];
  lines.sort(compare).forEach(line => console.log(line));
}
export function executeCleanup(plan, operations = fs) {
  const { repo, output, old, moves } = plan;
  if (!moves.length) return null;
  for (const item of moves) if (hash(bytes(repo, path.join(repo, item.path)) || Buffer.alloc(0)) !== item.sha256) fail(`source changed: ${item.path}`);
  const parent = safePath(repo, path.join(repo, '.okf', 'render-backups'));
  fs.mkdirSync(parent, { recursive: true });
  const backup = path.join(parent, randomUUID()); fs.mkdirSync(backup);
  const receipt = { version: 1, old_root: posix(path.relative(repo, old)), new_root: posix(path.relative(repo, output)), status: 'in-progress', planned: moves.map(item => ({ ...item, backup: posix(path.relative(repo,path.join(backup,item.path))) })), moves: [], copies: [] };
  const receiptFile = path.join(backup, 'receipt.json');
  const save = () => {
    const temp = receiptFile + '.' + randomUUID() + '.tmp';
    let descriptor;
    try {
      descriptor = fs.openSync(temp,'wx');
      (operations.writeFileSync || fs.writeFileSync)(descriptor,json(receipt));
      fs.fsyncSync(descriptor); fs.closeSync(descriptor); descriptor = undefined;
      fs.renameSync(temp,receiptFile);
    } finally {
      if (descriptor !== undefined) fs.closeSync(descriptor);
      if (fs.existsSync(temp)) fs.unlinkSync(temp);
    }
  };
  try {
    save();
    for (const item of moves) {
      const source = path.join(repo, item.path), dest = path.join(backup, item.path);
      const initial = bytes(repo, source), identity = fs.statSync(source);
      if (initial === null || hash(initial) !== item.sha256) fail(`source changed: ${item.path}`);
      safePath(repo, dest); fs.mkdirSync(path.dirname(dest), { recursive: true });
      operations.copyFileSync(source, dest, fs.constants.COPYFILE_EXCL);
      receipt.copies.push({ ...item, backup: posix(path.relative(repo, dest)) }); save();
      const current = fs.statSync(source);
      if (hash(bytes(repo, dest)) !== item.sha256 || hash(bytes(repo, source) || Buffer.alloc(0)) !== item.sha256 || current.ino !== identity.ino || current.dev !== identity.dev || current.size !== identity.size || current.mtimeMs !== identity.mtimeMs) fail(`source changed during backup: ${item.path}`);
      operations.unlinkSync(source);
      receipt.moves.push({ ...item, backup: posix(path.relative(repo, dest)) }); save();
    }
    receipt.status = 'complete'; save();
  } catch (error) {
    const recovery = [];
    for (const item of [...receipt.moves].reverse()) {
      const source = path.join(repo, item.path), dest = path.join(repo, item.backup);
      try {
        safePath(repo, source);
        if (hash(bytes(repo, dest) || Buffer.alloc(0)) !== item.sha256) throw new Error('backup changed');
        operations.copyFileSync(dest, source, fs.constants.COPYFILE_EXCL);
        if (hash(bytes(repo, source) || Buffer.alloc(0)) !== item.sha256) throw new Error('restore verification failed');
      }
      catch { recovery.push(item.backup); }
    }
    receipt.status = recovery.length ? 'recovery-required' : 'rolled-back'; receipt.recovery_paths = recovery;
    let saveError;
    try { save(); } catch (e) { saveError = e; }
    fail(`transaction failed; ${receipt.status}; backup: ${posix(path.relative(repo,backup))}; receipt: ${posix(path.relative(repo, receiptFile))}; ${error.message}${saveError ? `; recovery receipt update failed: ${saveError.message}` : ''}`);
  }
  console.log(`cleanup backup: ${posix(path.relative(repo, backup))}`);
  return backup;
}
