import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { Bundle } from '../../node/core.mjs';
import { renderBundle } from '../../node/renderer.mjs';
import { executeCleanup, planCleanup } from '../../node/render-cleanup.mjs';
import { temp, run, ok, put, snapshot } from './helpers.mjs';

function fixture(t) { const root = temp(t); ok(run(root, ['init'])); put(root,'docs/index.md','# Index\n'); return root; }
test('manifest migration preserves edits, handwritten HTML and Markdown, backs up stale artifacts', t => {
  const root = fixture(t);
  put(root, 'docs/retired.md', '# Retired\n');
  ok(run(root, ['render', '--output', 'old']));
  fs.unlinkSync(path.join(root, 'docs/retired.md'));
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'old/.okf-render-manifest.json')));
  const html = manifest.files.filter(e => e.path.endsWith('.html'));
  const edited = html.find(e => !['index.html','retired.html'].includes(e.path)).path;
  fs.appendFileSync(path.join(root, 'old', edited), '\nmanual edit');
  put(root, 'old/manual.html', '<h1>handwritten</h1>');
  const markdown = fs.readFileSync(path.join(root, 'docs/index.md'));
  ok(run(root, ['render', '--output', 'new', '--cleanup-from', 'old']));
  assert.equal(fs.existsSync(path.join(root, 'old/index.html')), false);
  assert.equal(fs.existsSync(path.join(root, 'old/retired.html')), false);
  assert.equal(fs.existsSync(path.join(root, 'old', edited)), true);
  assert.equal(fs.existsSync(path.join(root, 'old/manual.html')), true);
  assert.deepEqual(fs.readFileSync(path.join(root, 'docs/index.md')), markdown);
  const dirs = fs.readdirSync(path.join(root, '.okf/render-backups'));
  const receipt = JSON.parse(fs.readFileSync(path.join(root, '.okf/render-backups', dirs[0], 'receipt.json')));
  assert.equal(receipt.status, 'complete');
  assert.ok(receipt.moves.some(e => e.path === 'old/index.html'));
  assert.ok(receipt.moves.some(e => e.path === 'old/retired.html'));
  ok(run(root, ['render', '--output', 'new', '--cleanup-from', 'old']));
  assert.deepEqual(fs.readdirSync(path.join(root, '.okf/render-backups')), dirs);
});
test('exact legacy output migrates; edited/version-different output stays; check and hook do not write', t => {
  const root = fixture(t), bundle = new Bundle(root);
  renderBundle(bundle, path.join(root, 'old'));
  const before = snapshot(root,'.');
  const result = run(root, ['render', '--output', 'new', '--cleanup-from', 'old', '--check']);
  ok(result); assert.match(result.stdout, /cleanup move: old\/index.html/);
  assert.deepEqual(snapshot(root,'.'), before);
  assert.notEqual(run(root, ['render', '--output', 'new', '--cleanup-from', 'old', '--hook']).status, 0);
  assert.deepEqual(snapshot(root,'.'), before);
  fs.appendFileSync(path.join(root, 'old/index.html'), '\nold version');
  ok(run(root, ['render', '--output', 'new', '--cleanup-from', 'old']));
  assert.equal(fs.existsSync(path.join(root, 'old/index.html')), true);
});
test('invalid roots, tampered manifests, conflicting targets are refused before writes', t => {
  const root = fixture(t); ok(run(root, ['render', '--output', 'old']));
  for (const [old, output] of [['old','old'], ['old','old/nested'], ['old/nested','old'], ['.','new'], ['../escape','new'], ['.okf','new'], ['old','.okf/render-backups/new']]) {
    const before = snapshot(root,'.');
    assert.notEqual(run(root, ['render','--output',output,'--cleanup-from',old]).status, 0);
    assert.deepEqual(snapshot(root,'.'), before);
  }
  put(root, 'new/index.html', '<h1>user</h1>');
  let before = snapshot(root,'.');
  assert.notEqual(run(root, ['render','--output','new','--cleanup-from','old']).status, 0);
  assert.deepEqual(snapshot(root,'.'), before);
  const file = path.join(root, 'old/.okf-render-manifest.json');
  const manifest = JSON.parse(fs.readFileSync(file));
  for (const invalid of ['../index.html','nested/name:stream.html','nested/nul\u0000.html','nested/line\n.html']) {
    manifest.files[0].path = invalid;
    fs.writeFileSync(file, JSON.stringify(manifest)); before = snapshot(root,'.');
    assert.notEqual(run(root, ['render','--output','clean','--cleanup-from','old']).status, 0);
    assert.deepEqual(snapshot(root,'.'), before);
  }
});
test('partial transaction restores moved artifacts without clobbering recovery conflicts', t => {
  const root = fixture(t); ok(run(root, ['render','--output','old']));
  const b = new Bundle(root), target = renderBundle(b, path.join(root,'new'),false), legacy = renderBundle(b,path.join(root,'old'),false);
  const plan = planCleanup(root,path.join(root,'new'),path.join(root,'old'),target.artifacts,legacy.artifacts);
  let calls = 0;
  assert.throws(() => executeCleanup(plan, { copyFileSync: fs.copyFileSync, unlinkSync(p) { if (++calls === 2) throw new Error('injected'); fs.unlinkSync(p); } }), /rolled-back/);
  for (const move of plan.moves) assert.equal(fs.existsSync(path.join(root,move.path)),true);
  calls = 0;
  assert.throws(() => executeCleanup(plan, { copyFileSync: fs.copyFileSync, unlinkSync(p) { if (++calls === 2) { put(root,plan.moves[0].path,'new user file'); throw new Error('injected'); } fs.unlinkSync(p); } }), /recovery-required/);
  assert.equal(fs.readFileSync(path.join(root,plan.moves[0].path),'utf8'),'new user file');
});
test('symlink and Windows junction paths are refused', t => {
  const root = fixture(t); ok(run(root,['render','--output','old']));
  try { fs.symlinkSync(path.join(root,'old'),path.join(root,'linked'),process.platform === 'win32' ? 'junction' : 'dir'); }
  catch (e) { t.skip(`link unavailable: ${e.code}`); return; }
  assert.notEqual(run(root,['render','--output','new','--cleanup-from','linked']).status,0);
  assert.equal(fs.existsSync(path.join(root,'new')),false);
});
test('rollback detects changed backup and corrupt restore instead of claiming success', t => {
  for (const corrupt of ['backup','restore']) {
    const root = fixture(t); ok(run(root,['render','--output','old']));
    const b = new Bundle(root), target = renderBundle(b,path.join(root,'new'),false), legacy = renderBundle(b,path.join(root,'old'),false);
    const plan = planCleanup(root,path.join(root,'new'),path.join(root,'old'),target.artifacts,legacy.artifacts);
    let copied, unlinks = 0;
    assert.throws(() => executeCleanup(plan, {
      copyFileSync(source,dest,flags) {
        fs.copyFileSync(source,dest,flags);
        if (!copied) copied = dest;
        if (corrupt === 'restore' && source.includes(`${path.sep}render-backups${path.sep}`)) fs.writeFileSync(dest,'corrupted restoration');
      },
      unlinkSync(source) {
        if (++unlinks === 2) { if (corrupt === 'backup') fs.writeFileSync(copied,'corrupted backup'); throw new Error('injected failure'); }
        fs.unlinkSync(source);
      }
    }), /recovery-required/);
    const dir = fs.readdirSync(path.join(root,'.okf/render-backups'))[0];
    const receipt = JSON.parse(fs.readFileSync(path.join(root,'.okf/render-backups',dir,'receipt.json')));
    assert.equal(receipt.status,'recovery-required'); assert.equal(receipt.recovery_paths.length,1);
  }
});
test('receipt writes stay atomic and initial planned metadata identifies interrupted copies', t => {
  for (const failure of ['receipt','copy']) {
    const root = fixture(t); ok(run(root,['render','--output','old']));
    const b = new Bundle(root), target = renderBundle(b,path.join(root,'new'),false), legacy = renderBundle(b,path.join(root,'old'),false);
    const plan = planCleanup(root,path.join(root,'new'),path.join(root,'old'),target.artifacts,legacy.artifacts);
    let writes = 0;
    assert.throws(() => executeCleanup(plan, {
      writeFileSync(fd,data) {
        if (++writes >= 4 && failure === 'receipt') { fs.writeSync(fd,'{partial'); throw new Error('receipt disk failure'); }
        fs.writeFileSync(fd,data);
      },
      copyFileSync(source,dest,flags) {
        if (failure === 'copy') { fs.writeFileSync(dest,'partial copy',{flag:'wx'}); throw new Error('partial copy failure'); }
        fs.copyFileSync(source,dest,flags);
      }, unlinkSync:fs.unlinkSync
    }), failure === 'receipt' ? /receipt disk failure.*recovery receipt update failed/ : /partial copy failure/);
    const dir = fs.readdirSync(path.join(root,'.okf/render-backups'))[0];
    const receipt = JSON.parse(fs.readFileSync(path.join(root,'.okf/render-backups',dir,'receipt.json')));
    assert.equal(receipt.planned.length,plan.moves.length);
    assert.ok(receipt.planned.every(item => item.backup && item.sha256));
    for (const item of plan.moves) assert.equal(fs.existsSync(path.join(root,item.path)),true);
  }
});
test('Windows case and trailing dot/space aliases cannot migrate into themselves', { skip: process.platform !== 'win32' }, t => {
  const root = fixture(t), b = new Bundle(root);
  renderBundle(b,path.join(root,'old'));
  for (const [old,output] of [['old','OLD'], ['old.','new'], ['old ','new'], ['old','new.'], ['old','new '], ['old','OLD/nested']]) {
    const before = snapshot(root,'.');
    for (const mode of [[],['--check']]) {
      assert.notEqual(run(root,['render','--output',output,'--cleanup-from',old,...mode]).status,0);
      assert.deepEqual(snapshot(root,'.'),before);
    }
    if (output.toLowerCase().startsWith('new')) assert.equal(fs.existsSync(path.join(root,output)),false);
  }
});
test('Windows manifest case-only duplicates are refused before any output changes', { skip: process.platform !== 'win32' }, t => {
  const root = fixture(t); ok(run(root,['render','--output','old']));
  const file = path.join(root,'old/.okf-render-manifest.json'), manifest = JSON.parse(fs.readFileSync(file));
  const original = manifest.files.find(item => item.path === 'index.html');
  manifest.files.push({ ...original, path:'INDEX.html' });
  fs.writeFileSync(file,JSON.stringify(manifest));
  const before = snapshot(root,'.');
  for (const mode of [[],['--check']]) {
    assert.notEqual(run(root,['render','--output','new','--cleanup-from','old',...mode]).status,0);
    assert.deepEqual(snapshot(root,'.'),before);
    assert.equal(fs.existsSync(path.join(root,'new')),false);
  }
});
