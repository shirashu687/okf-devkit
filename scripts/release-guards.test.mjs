import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, rmSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { verifySource, loadBundle, sha256 } from './release-bundle.mjs';
import { ensureDraft, githubTransport } from './release-github.mjs';
import { writeCiManifest, verifyCiBundle } from './ci-package.mjs';

const commit = 'a'.repeat(40);
const manifest = { schema: 1, repository: 'owner/project', tag: 'v1.2.3', version: '1.2.3', commit, package: 'example' };
const assets = ['example-1.2.3.tgz', 'release-manifest.json', 'SHA256SUMS'].map(name => ({ name, path: `/bundle/${name}`, bytes: Buffer.from(name) }));
const bundle = { manifest, assets };

function fake({ draft = true, files = [], target = commit, exists = true, immutable = false } = {}) {
  let release = exists ? { id: 1, draft, immutable, tag_name: manifest.tag, target_commitish: target, html_url: 'https://example.test/draft', assets: files.map((file, index) => ({ id: index + 1, name: file.name, state: file.state ?? 'uploaded' })) } : null;
  const data = new Map(files.map((file, index) => [index + 1, file.bytes]));
  const writes = [];
  return {
    writes,
    async find() { return release; },
    async download(asset) { return data.get(asset.id); },
    async create(identity) { writes.push('create'); release = { id: 1, draft: true, tag_name: identity.tag, target_commitish: identity.commit, html_url: 'draft', assets: [] }; },
    async upload(_release, asset) { writes.push(asset.name); const id = release.assets.length + 1; release.assets.push({ id, name: asset.name, state: 'uploaded' }); data.set(id, asset.bytes); },
  };
}

test('new draft uploads each verified asset and compares resulting bytes', async () => {
  const api = fake({ exists: false });
  assert.equal((await ensureDraft(bundle, api)).status, 'draft');
  assert.deepEqual(api.writes, ['create', ...assets.map(asset => asset.name)]);
});
test('interrupted draft retry only appends missing identical assets', async () => {
  const api = fake({ files: [assets[0]] });
  await ensureDraft(bundle, api);
  assert.deepEqual(api.writes, assets.slice(1).map(asset => asset.name));
  api.writes.length = 0;
  await ensureDraft(bundle, api);
  assert.deepEqual(api.writes, []);
});
test('published release is verified read-only, including when marked immutable', async () => {
  const api = fake({ draft: false, immutable: true, files: assets });
  assert.equal((await ensureDraft(bundle, api)).status, 'already-published');
  assert.deepEqual(api.writes, []);
});
test('published missing assets refuses all writes', async () => {
  const api = fake({ draft: false, files: [assets[0]] });
  await assert.rejects(ensureDraft(bundle, api), /immutable/);
  assert.deepEqual(api.writes, []);
});
test('differing existing asset prevents even otherwise missing draft uploads', async () => {
  const api = fake({ files: [{ ...assets[0], bytes: Buffer.from('different') }] });
  await assert.rejects(ensureDraft(bundle, api), /differs/);
  assert.deepEqual(api.writes, []);
});
test('unexpected, duplicate or incomplete asset is never overwritten', async () => {
  for (const files of [[...assets, { name: 'unrecognized', bytes: Buffer.from('x') }], [assets[0], assets[0]], [{ ...assets[0], state: 'starter' }]]) {
    const api = fake({ files });
    await assert.rejects(ensureDraft(bundle, api), /Conflicting/);
    assert.deepEqual(api.writes, []);
  }
});
test('existing release target mismatch refuses mutation', async () => {
  const api = fake({ target: 'b'.repeat(40) });
  await assert.rejects(ensureDraft(bundle, api), /target/);
  assert.deepEqual(api.writes, []);
});
test('an upload failure is propagated without deletion or blind retry', async () => {
  const api = fake();
  api.upload = async () => { throw new Error('network interruption'); };
  await assert.rejects(ensureDraft(bundle, api), /network/);
  assert.deepEqual(api.writes, []);
});
test('human publication or target change before upload is detected without writes', async () => {
  for (const edit of [release => { release.draft = false; }, release => { release.target_commitish = 'b'.repeat(40); }]) {
    const api = fake();
    const find = api.find;
    let calls = 0;
    api.find = async tag => { const release = await find(tag); if (++calls === 2) edit(release); return release; };
    await assert.rejects(ensureDraft(bundle, api), /changed before upload/);
    assert.deepEqual(api.writes, []);
  }
});
test('remote source guard failure prevents draft creation and upload', async () => {
  for (const exists of [false, true]) {
    const api = fake({ exists });
    api.guard = () => { throw new Error('remote tag moved'); };
    await assert.rejects(ensureDraft(bundle, api), /remote tag moved/);
    assert.deepEqual(api.writes, []);
  }
});
test('CLI transport lists authenticated drafts and uses verify-tag, draft and no clobber', () => {
  const calls = [];
  const api = githubTransport('owner/project', args => { calls.push(args); return Buffer.from(args.includes('--slurp') ? '[[]]' : 'bytes'); });
  assert.equal(api.find(manifest.tag), null);
  api.create(manifest);
  api.upload({ tag_name: manifest.tag }, assets[0]);
  assert.ok(calls[0].includes('--paginate'));
  assert.ok(calls[1].includes('--verify-tag'));
  assert.ok(calls[1].includes('--draft'));
  assert.ok(!calls.flat().includes('--clobber'));
  assert.ok(!calls.some(args => args.includes('delete') || args.includes('edit')));
});
test('manifest/hash verification rejects modified archive, identity and unexpected files', () => {
  const dir = mkdtempSync(join(tmpdir(), 'okf-release-bundle-'));
  try {
    const bytes = Buffer.from('same packaged bytes');
    const entry = { name: 'example-1.2.3.tgz', size: bytes.length, sha256: sha256(bytes) };
    const meta = Buffer.from(JSON.stringify({ ...manifest, files: [entry] }) + '\n');
    writeFileSync(join(dir, entry.name), bytes);
    writeFileSync(join(dir, 'release-manifest.json'), meta);
    writeFileSync(join(dir, 'SHA256SUMS'), `${entry.sha256}  ${entry.name}\n${sha256(meta)}  release-manifest.json\n`);
    assert.equal(loadBundle(dir, { tag: manifest.tag, commit }).manifest.version, '1.2.3');
    assert.throws(() => loadBundle(dir, { commit: 'b'.repeat(40) }), /mismatch/);
    writeFileSync(join(dir, entry.name), 'tampered');
    assert.throws(() => loadBundle(dir), /checksum/);
    writeFileSync(join(dir, entry.name), bytes);
    writeFileSync(join(dir, 'unexpected'), 'x');
    assert.throws(() => loadBundle(dir), /Unexpected/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
test('real Git verifies lightweight/annotated tags, main ancestry and remote movement', () => {
  const root = mkdtempSync(join(tmpdir(), 'okf-release-git-'));
  const repo = join(root, 'work');
  const remote = join(root, 'remote.git');
  mkdirSync(repo);
  const run = (...args) => execFileSync('git', args, { cwd: repo, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  try {
    execFileSync('git', ['init', '--bare', remote], { stdio: 'ignore' });
    run('init', '-b', 'main'); run('config', 'user.email', 'test@example.invalid'); run('config', 'user.name', 'Test');
    writeFileSync(join(repo, 'file'), 'initial'); run('add', 'file'); run('commit', '-m', 'initial');
    run('remote', 'add', 'origin', remote); run('push', '-u', 'origin', 'main');
    const head = run('rev-parse', 'HEAD');
    const pkg = { name: 'example', version: '1.2.3' };
    const identity = { repository: 'owner/project', tag: 'v1.2.3', commit: head };
    run('tag', identity.tag); run('push', 'origin', identity.tag);
    assert.equal(verifySource(identity, run, pkg).commit, head);
    writeFileSync(join(repo, 'file'), 'dirty source');
    assert.throws(() => verifySource(identity, run, pkg), /Tracked source differs/);
    run('checkout', '--', 'file');
    assert.throws(() => verifySource({ ...identity, tag: 'v9.9.9' }, run, pkg), /version/);
    assert.throws(() => verifySource({ ...identity, commit: 'b'.repeat(40) }, run, pkg), /mismatch/);
    run('tag', '-d', identity.tag); run('tag', '-a', identity.tag, '-m', 'annotated'); run('push', '--force', 'origin', identity.tag);
    assert.equal(verifySource(identity, run, pkg).commit, head);
    run('checkout', '-b', 'outside-main'); writeFileSync(join(repo, 'file'), 'outside'); run('commit', '-am', 'outside');
    const outside = run('rev-parse', 'HEAD'); run('tag', '-f', identity.tag); run('push', '--force', 'origin', identity.tag);
    assert.throws(() => verifySource(identity, run, pkg), /mismatch/);
    assert.throws(() => verifySource({ ...identity, commit: outside }, run, pkg));
    run('checkout', 'main'); run('tag', '-f', identity.tag);
    assert.throws(() => verifySource(identity, run, pkg), /Remote tag changed/);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
test('shared CI archive validates source SHA and bytes without a release tag', () => {
  const dir = mkdtempSync(join(tmpdir(), 'okf-ci-bundle-'));
  const identity = { repository: 'owner/project', commit };
  try {
    writeFileSync(join(dir, 'example-1.2.3.tgz'), 'shared CI bytes');
    const manifest = writeCiManifest(dir, 'example-1.2.3.tgz', identity, { name: 'example', version: '1.2.3' });
    assert.equal(verifyCiBundle(dir, identity).manifest.sha256, manifest.sha256);
    assert.ok(!('tag' in manifest));
    assert.throws(() => verifyCiBundle(dir, { ...identity, commit: 'b'.repeat(40) }), /provenance/);
    assert.throws(() => loadBundle(dir), /ENOENT/);
    writeFileSync(join(dir, 'example-1.2.3.tgz'), 'changed');
    assert.throws(() => verifyCiBundle(dir, identity), /checksum/);
    writeFileSync(join(dir, 'example-1.2.3.tgz'), 'shared CI bytes');
    writeFileSync(join(dir, 'ci-package.json'), JSON.stringify({ ...manifest, tag: 'v1.2.3' }));
    assert.throws(() => verifyCiBundle(dir, identity), /provenance/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
