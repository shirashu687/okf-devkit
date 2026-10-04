import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { command, npm, isolatedEnvironment, inspectTarball, installedCli, runSmoke } from '../../scripts/package-smoke.mjs';

const repo = fileURLToPath(new URL('../../', import.meta.url));
let scratch, artifact, version, digest, previous, packEnv;
test.before(() => {
  scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'okf-distribution-test-'));
  packEnv = isolatedEnvironment({npm_config_cache:path.join(scratch,'pack-cache'), npm_config_userconfig:path.join(scratch,'empty.npmrc'), npm_config_globalconfig:path.join(scratch,'global.npmrc')});
  fs.writeFileSync(packEnv.npm_config_userconfig,'');fs.writeFileSync(packEnv.npm_config_globalconfig,'');
  version = JSON.parse(fs.readFileSync(path.join(repo, 'package.json'), 'utf8')).version;
  const packed = JSON.parse(npm(['pack', '--ignore-scripts', '--json', '--pack-destination', scratch], repo, packEnv));
  assert.equal(packed.length, 1);
  artifact = path.join(scratch, packed[0].filename);
  digest = crypto.createHash('sha256').update(fs.readFileSync(artifact)).digest('hex');
  inspectTarball(artifact, version, digest);
  // This second pack is a test-only synthetic predecessor, not another release build.
  const older = path.join(scratch, 'synthetic-older'); fs.mkdirSync(older);
  command('tar', ['-xzf', artifact, '-C', older], scratch);
  const source = path.join(older, 'package');
  const metadata = JSON.parse(fs.readFileSync(path.join(source, 'package.json'), 'utf8'));
  metadata.version = '0.0.0'; metadata.private = true;
  fs.writeFileSync(path.join(source, 'package.json'), JSON.stringify(metadata, null, 2));
  const fixturePack = JSON.parse(npm(['pack', '--ignore-scripts', '--json', '--pack-destination', older], source, packEnv));
  previous = path.join(older, fixturePack[0].filename);
});
test.after(() => { if (scratch) fs.rmSync(scratch, { recursive: true, force: true }); });

test('real packed artifact installs locally/globally, preserves documents and rolls back saved lock', () => {
  const keys = Object.keys(process.env).filter(key=>/^npm_config_/i.test(key));
  const saved = Object.fromEntries(keys.map(key=>[key,process.env[key]]));
  for(const key of keys) delete process.env[key];
  const forbidden=path.join(scratch,'forbidden-prefix');
  fs.mkdirSync(forbidden);fs.writeFileSync(path.join(forbidden,'sentinel'),'untouched user-like prefix');
  process.env.NPM_CONFIG_GLOBAL='true';process.env.NPM_CONFIG_PREFIX=forbidden;process.env.NPM_CONFIG_WORKSPACE='hostile';process.env.NPM_CONFIG_LOCATION='global';
  process.env.NPM_CONFIG_CACHE=path.join(forbidden,'cache');process.env.NPM_CONFIG_USERCONFIG=path.join(forbidden,'user.npmrc');process.env.NPM_CONFIG_GLOBALCONFIG=path.join(forbidden,'global.npmrc');
  let result;
  try { result=runSmoke({ tarball: artifact, expectedVersion: version, expectedSha256: digest, previousTarball: previous }); }
  finally { for(const key of Object.keys(process.env)) if(/^npm_config_/i.test(key)) delete process.env[key];Object.assign(process.env,saved); }
  assert.deepEqual(fs.readdirSync(forbidden),['sentinel'],'Inherited npm environment escaped isolated prefix');
  assert.equal(fs.readFileSync(path.join(forbidden,'sentinel'),'utf8'),'untouched user-like prefix');
  assert.equal(result.uninstallPreservation, true);
  assert.equal(result.local, true); assert.equal(result.global, true); assert.equal(result.preservation, true);
  assert.equal(result.sha256, digest);
  assert.match(result.lifecycle, /saved manifest\/lock npm ci rollback/);
  assert.match(result.lifecycle, /real historical releases unverified/);
  assert.equal(result.actualStopEvent, 'unverified');
});

test('wrong version/hash, malformed artifact and missing installed package fail without fallback', () => {
  assert.throws(() => inspectTarball(artifact, '999.0.0', digest), /version mismatch/);
  assert.throws(() => inspectTarball(artifact, version, '0'.repeat(64)), /SHA256 mismatch/);
  assert.throws(() => inspectTarball(path.basename(artifact), version), /absolute/);
  assert.throws(() => inspectTarball(path.join(scratch, 'absent.tgz'), version));
  const broken = path.join(scratch, 'broken.tgz'); fs.writeFileSync(broken, 'not gzip');
  assert.throws(() => inspectTarball(broken, version), /failed/);
  assert.throws(() => installedCli(path.join(scratch, 'missing-package'), version));
  const missing = path.join(scratch, 'missing-bin'); fs.mkdirSync(missing);
  fs.writeFileSync(path.join(missing, 'package.json'), JSON.stringify({ name:'okf-devkit', version, bin:{okf:'node/cli.mjs'} }));
  assert.throws(() => installedCli(missing, version), /no registry fallback/);
});

test('CLI rejects inconsistent artifact identity before fixture installation', () => {
  const script = path.join(repo, 'scripts/package-smoke.mjs');
  assert.throws(() => command(process.execPath, [script, '--tarball', artifact, '--expected-version', version, '--expected-sha256', 'f'.repeat(64)], scratch), /SHA256 mismatch/);
});
