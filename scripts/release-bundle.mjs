import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { resolve, basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const sha256 = data => createHash('sha256').update(data).digest('hex');
const git = (...args) => execFileSync('git', args, { encoding: 'utf8' }).trim();

export function verifySource({ tag, commit, repository }, runGit = git, pkg = JSON.parse(readFileSync('package.json', 'utf8'))) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository ?? '')) throw new Error('Invalid repository');
  if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/.test(pkg.version)) throw new Error('Invalid package version');
  if (tag !== `v${pkg.version}`) throw new Error('Tag must match package version exactly');
  if (!/^[a-f0-9]{40}$/.test(commit ?? '')) throw new Error('Expected full commit SHA');
  if (runGit('status', '--porcelain', '--untracked-files=no')) throw new Error('Tracked source differs from verified commit');
  if (runGit('rev-parse', 'HEAD') !== commit || runGit('rev-parse', `refs/tags/${tag}^{commit}`) !== commit) throw new Error('Checkout/tag commit mismatch');
  const refs = runGit('ls-remote', '--tags', 'origin', `refs/tags/${tag}`, `refs/tags/${tag}^{}`).split('\n').filter(Boolean);
  const remote = new Map(refs.map(line => line.split(/\s+/).reverse()));
  if ((remote.get(`refs/tags/${tag}^{}`) ?? remote.get(`refs/tags/${tag}`)) !== commit) throw new Error('Remote tag changed or missing');
  runGit('merge-base', '--is-ancestor', commit, 'origin/main');
  return { schema: 1, repository, tag, commit, package: pkg.name, version: pkg.version };
}

export function loadBundle(directory, expected = {}) {
  const dir = resolve(directory);
  const manifestBytes = readFileSync(join(dir, 'release-manifest.json'));
  const manifest = JSON.parse(manifestBytes.toString('utf8'));
  if (manifest.schema !== 1 || !Array.isArray(manifest.files) || manifest.files.length !== 1) throw new Error('Invalid manifest');
  for (const key of ['tag', 'commit', 'repository']) if (expected[key] && manifest[key] !== expected[key]) throw new Error(`Manifest ${key} mismatch`);
  if (manifest.tag !== `v${manifest.version}` || !/^[a-f0-9]{40}$/.test(manifest.commit)) throw new Error('Invalid manifest identity');
  const file = manifest.files[0];
  if (basename(file.name) !== file.name || !/^[A-Za-z0-9_.-]+\.tgz$/.test(file.name)) throw new Error('Invalid tarball filename');
  const archive = readFileSync(join(dir, file.name));
  if (file.size !== archive.length || file.sha256 !== sha256(archive)) throw new Error('Tarball checksum mismatch');
  const sums = `${file.sha256}  ${file.name}\n${sha256(manifestBytes)}  release-manifest.json\n`;
  if (readFileSync(join(dir, 'SHA256SUMS'), 'utf8') !== sums) throw new Error('Checksum manifest mismatch');
  if (readdirSync(dir).sort().join('\n') !== [file.name, 'release-manifest.json', 'SHA256SUMS'].sort().join('\n')) throw new Error('Unexpected bundle files');
  return { manifest, tarball: join(dir, file.name), assets: [file.name, 'release-manifest.json', 'SHA256SUMS'].map(name => ({ name, path: join(dir, name), bytes: readFileSync(join(dir, name)) })) };
}

export function prepareBundle(directory, identity) {
  const source = verifySource(identity);
  const dir = resolve(directory);
  mkdirSync(dir, { recursive: true });
  if (readdirSync(dir).length) throw new Error('Pack destination must be empty');
  // Exactly one pack invocation. Matrix jobs consume this resulting archive.
  // Packing is intentionally confined to the Ubuntu bundle job; no shell expansion.
  if (process.platform === 'win32') throw new Error('Prepare the bundle in the Ubuntu pack job');
  const packed = JSON.parse(execFileSync('npm', ['pack', '--json', '--ignore-scripts', '--pack-destination', dir], { encoding: 'utf8' }));
  if (packed.length !== 1 || packed[0].name !== source.package || packed[0].version !== source.version) throw new Error('Packed package identity mismatch');
  const name = packed[0].filename;
  if (basename(name) !== name) throw new Error('Unsafe pack output');
  const bytes = readFileSync(join(dir, name));
  const manifest = { ...source, files: [{ name, size: bytes.length, sha256: sha256(bytes) }] };
  const manifestBytes = Buffer.from(JSON.stringify(manifest, null, 2) + '\n');
  writeFileSync(join(dir, 'release-manifest.json'), manifestBytes);
  writeFileSync(join(dir, 'SHA256SUMS'), `${sha256(bytes)}  ${name}\n${sha256(manifestBytes)}  release-manifest.json\n`);
  return loadBundle(dir, identity);
}

function identityFromEnvironment() {
  return { tag: process.env.GITHUB_REF_NAME, commit: process.env.GITHUB_SHA, repository: process.env.GITHUB_REPOSITORY };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [command, directory = 'dist'] = process.argv.slice(2);
  if (command === 'prepare') prepareBundle(directory, identityFromEnvironment());
  else if (command === 'verify') loadBundle(directory, identityFromEnvironment());
  else if (command === 'source') verifySource(identityFromEnvironment());
  else if (command === 'smoke') {
    const { manifest, tarball } = loadBundle(directory, identityFromEnvironment());
    execFileSync(process.execPath, ['scripts/package-smoke.mjs', '--tarball', tarball, '--expected-version', manifest.version, '--expected-sha256', manifest.files[0].sha256], { stdio: 'inherit' });
  } else throw new Error('Expected source, prepare, verify or smoke');
}
