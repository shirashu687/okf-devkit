import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { resolve, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { sha256 } from './release-bundle.mjs';
import { npm } from './package-smoke.mjs';

// CI provenance is deliberately not a release identity and never invents a tag.
export function writeCiManifest(directory, name, identity, pkg) {
  if (!/^[a-f0-9]{40}$/.test(identity.commit) || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(identity.repository)) throw new Error('Invalid CI provenance');
  if (basename(name) !== name || !/^[A-Za-z0-9_.-]+\.tgz$/.test(name)) throw new Error('Unsafe archive filename');
  const bytes = readFileSync(join(directory, name));
  const manifest = { schema: 1, kind: 'ci-package', repository: identity.repository, commit: identity.commit, package: pkg.name, version: pkg.version, filename: name, size: bytes.length, sha256: sha256(bytes) };
  writeFileSync(join(directory, 'ci-package.json'), JSON.stringify(manifest, null, 2) + '\n');
  return manifest;
}

export function verifyCiBundle(directory, identity) {
  const dir = resolve(directory);
  const manifest = JSON.parse(readFileSync(join(dir, 'ci-package.json'), 'utf8'));
  if (manifest.schema !== 1 || manifest.kind !== 'ci-package' || 'tag' in manifest || manifest.repository !== identity.repository || manifest.commit !== identity.commit || !/^[a-f0-9]{40}$/.test(manifest.commit)) throw new Error('CI provenance mismatch');
  if (basename(manifest.filename) !== manifest.filename || !/^[A-Za-z0-9_.-]+\.tgz$/.test(manifest.filename)) throw new Error('Unsafe archive filename');
  const archive = readFileSync(join(dir, manifest.filename));
  if (archive.length !== manifest.size || sha256(archive) !== manifest.sha256) throw new Error('CI archive checksum mismatch');
  if (readdirSync(dir).sort().join('\n') !== [manifest.filename, 'ci-package.json'].sort().join('\n')) throw new Error('Unexpected CI artifact files');
  return { manifest, tarball: join(dir, manifest.filename) };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [mode, directory] = process.argv.slice(2);
  const dir = resolve(directory ?? 'ci-package');
  const identity = { repository: process.env.GITHUB_REPOSITORY, commit: process.env.GITHUB_SHA };
  if (mode === 'prepare') {
    if (execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim() !== identity.commit) throw new Error('CI checkout SHA mismatch');
    if (execFileSync('git', ['status', '--porcelain', '--untracked-files=no'], { encoding: 'utf8' }).trim()) throw new Error('CI tracked source differs from commit');
    mkdirSync(dir, { recursive: true });
    if (readdirSync(dir).length) throw new Error('CI pack directory must be empty');
    const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
    const packed = JSON.parse(npm(['pack', '--json', '--ignore-scripts', '--pack-destination', dir], process.cwd()));
    if (packed.length !== 1 || packed[0].name !== pkg.name || packed[0].version !== pkg.version) throw new Error('Packed CI identity mismatch');
    writeCiManifest(dir, packed[0].filename, identity, pkg);
    verifyCiBundle(dir, identity);
  } else if (mode === 'smoke') {
    const { manifest, tarball } = verifyCiBundle(dir, identity);
    console.log(JSON.stringify({ ciPackage: manifest.filename, sourceCommit: manifest.commit, sha256: manifest.sha256, os: process.platform, node: process.version }));
    execFileSync(process.execPath, ['scripts/package-smoke.mjs', '--tarball', tarball, '--expected-version', manifest.version, '--expected-sha256', manifest.sha256], { stdio: 'inherit' });
  } else throw new Error('Expected prepare or smoke');
}
