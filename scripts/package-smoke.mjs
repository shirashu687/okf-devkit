import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export function command(executable, args, cwd, env = process.env) {
  const result = spawnSync(executable, args, { cwd, env, encoding: 'utf8', windowsHide: true, timeout: 180000, maxBuffer: 8 * 1024 * 1024 });
  if (result.error || result.status !== 0) throw new Error(`${path.basename(executable)} failed (${result.status}): ${result.error?.message || result.stderr || result.stdout}`);
  return result.stdout;
}

// Invoke npm's JavaScript entrypoint: .cmd cannot be spawned without a shell on Windows.
// Never interpolate an artifact path into a command shell or call npx.
export function npmCli() {
  const candidates = [process.env.npm_execpath, path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js')];
  for (const directory of (process.env.PATH || '').split(path.delimiter)) {
    candidates.push(path.join(directory, 'node_modules/npm/bin/npm-cli.js'));
    const executable = path.join(directory, 'npm');
    if (fs.existsSync(executable)) candidates.push(fs.realpathSync(executable));
  }
  const found = candidates.find(p => p && p.endsWith('npm-cli.js') && fs.existsSync(p));
  if (!found) throw new Error('Cannot locate installed npm-cli.js');
  return found;
}

export function isolatedEnvironment(overrides = {}) {
  const env = {};
  for(const [key,value] of Object.entries(process.env))
    if(!/^npm_config_/i.test(key) && !/^(NPM_TOKEN|NODE_AUTH_TOKEN)$/i.test(key)) env[key]=value;
  return {...env,...overrides};
}

export function npm(args, cwd, env) { return command(process.execPath, [npmCli(), ...args], cwd, env); }

const required = ['package.json', 'LICENSE', 'README.md', 'node/cli.mjs', 'node/core.mjs', 'node/renderer.mjs', 'node/scaffold.mjs', 'src/okf_devkit/defaults.yml', 'src/okf_devkit/assets/page.html', 'src/okf_devkit/assets/docs.css', 'src/okf_devkit/assets/docs.js', 'src/okf_devkit/scaffold/okf.yml.tmpl', 'src/okf_devkit/scaffold/AGENTS.md.tmpl', 'src/okf_devkit/scaffold/hooks/render_hook.sh', 'src/okf_devkit/scaffold/hooks/render_hook.ps1', 'src/okf_devkit/scaffold/templates/reference.md', 'node/browser.mjs', 'node/checks.mjs', 'node/history.mjs', 'node/index.mjs', 'node/render-cleanup.mjs', 'src/okf_devkit/scaffold/CONVENTIONS.md.tmpl', 'src/okf_devkit/scaffold/templates/architecture.md', 'src/okf_devkit/scaffold/templates/backlog-item.md', 'src/okf_devkit/scaffold/templates/decision-record.md', 'src/okf_devkit/scaffold/templates/glossary.md', 'src/okf_devkit/scaffold/templates/how-to.md', 'src/okf_devkit/scaffold/templates/log.md'];

export function inspectTarball(tarball, expectedVersion, expectedSha256) {
  if (!path.isAbsolute(tarball) || !fs.statSync(tarball).isFile()) throw new Error('Tarball must be an existing absolute file');
  const sha256 = crypto.createHash('sha256').update(fs.readFileSync(tarball)).digest('hex');
  if (expectedSha256 && (!/^[a-f0-9]{64}$/i.test(expectedSha256) || expectedSha256.toLowerCase() !== sha256)) throw new Error('Tarball SHA256 mismatch');
  const files = command('tar', ['-tzf', tarball], path.dirname(tarball)).trim().split(/\r?\n/);
  if (files.some(f => !f.startsWith('package/') || f.split('/').includes('..') || f.includes('\\'))) throw new Error('Unsafe package archive paths');
  for (const file of required) assert.ok(files.includes(`package/${file}`), `Missing packaged asset: ${file}`);
  const metadata = JSON.parse(command('tar', ['-xOf', tarball, 'package/package.json'], path.dirname(tarball)));
  assert.equal(metadata.name, 'okf-devkit', 'Unexpected package name');
  assert.equal(metadata.version, expectedVersion, 'Package version mismatch');
  assert.equal(metadata.bin?.okf, 'node/cli.mjs');
  assert.equal(metadata.type, 'module');
  assert.ok(metadata.engines?.node);
  return { version: metadata.version, sha256, files, required };
}

export function installedCli(packageRoot, version) {
  const metadata = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));
  assert.equal(metadata.name, 'okf-devkit');
  assert.equal(metadata.version, version);
  assert.equal(metadata.bin?.okf, 'node/cli.mjs');
  const entry = path.join(packageRoot, metadata.bin.okf);
  if (!fs.existsSync(entry)) throw new Error('Installed package CLI missing; no registry fallback');
  return entry;
}

function snapshot(root) {
  const result = {};
  for (const name of ['okf.yml', 'docs', '_site', 'README.md', 'AGENTS.md', '.claude', '.codex', '.okf']) {
    const visit = target => {
      if (!fs.existsSync(target)) return;
      if (fs.statSync(target).isDirectory()) for (const file of fs.readdirSync(target).sort()) visit(path.join(target, file));
      else result[path.relative(root, target)] = fs.readFileSync(target).toString('base64');
    };
    visit(path.join(root, name));
  }
  return result;
}

export function runSmoke({ tarball, expectedVersion, expectedSha256, previousTarball }) {
  const artifact = inspectTarball(tarball, expectedVersion, expectedSha256);
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'okf-package-smoke-'));
  const env = isolatedEnvironment({ npm_config_cache: path.join(scratch, 'cache'), npm_config_userconfig: path.join(scratch, 'empty.npmrc'), npm_config_globalconfig: path.join(scratch, 'global.npmrc'), npm_config_audit: 'false', npm_config_fund: 'false', GIT_CONFIG_GLOBAL: path.join(scratch, 'empty.gitconfig'), GIT_CONFIG_NOSYSTEM: '1', PYTHONPATH: '' });
  fs.writeFileSync(env.npm_config_userconfig, '');
  fs.writeFileSync(env.npm_config_globalconfig, '');
  fs.writeFileSync(env.GIT_CONFIG_GLOBAL, '');
  const report = { version: artifact.version, sha256: artifact.sha256, assets: artifact.required.length, local: false, global: false, preservation: false, lifecycle: 'same-artifact reinstall; cross-version unverified', actualStopEvent: 'unverified' };
  try {
    const local = path.join(scratch, 'local'), global = path.join(scratch, 'global-project'), prefix = path.join(scratch, 'prefix');
    for (const root of [local, global]) {
      fs.mkdirSync(root); command('git', ['init', '-q'], root, env);
      fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({ name: 'private-okf-fixture', version: '1.0.0', private: true, description: 'preserve this manifest' }));
    }
    const install = (root, archive, globalInstall = false) => npm(['install', '--ignore-scripts', '--no-audit', '--no-fund', '--prefer-offline', ...(globalInstall ? ['--global', '--prefix', prefix] : ['--global=false', '--prefix', root, '--save-dev']), archive], root, env);
    const localPackage = path.join(local, 'node_modules/okf-devkit');
    const globalPackage = path.join(prefix, process.platform === 'win32' ? 'node_modules/okf-devkit' : 'lib/node_modules/okf-devkit');
    fs.writeFileSync(path.join(local, 'README.md'), '# User edited README\nKeep this text.\n');
    fs.writeFileSync(path.join(local, 'AGENTS.md'), '# User agent instructions\n');
    fs.mkdirSync(path.join(local, '.claude'));
    fs.writeFileSync(path.join(local, '.claude/settings.json'), '{"userSetting":"keep"}\n');
    fs.mkdirSync(path.join(local, 'docs/project'), {recursive:true});
    fs.writeFileSync(path.join(local, 'docs/project/user.md'), '---\ntype: Glossary\ntitle: User terms\ndescription: Preserve user-authored terms.\nlayer: shared\nstatus: stable\ntags: []\nrelated: []\ngenerated:\n  by: process:test\n  at: "2026-01-01T00:00:00Z"\n---\n\n# User terms\n\nUser-edited content.\n');
    const untouched = snapshot(local);
    install(local, tarball); install(global, tarball, true);
    assert.deepEqual(snapshot(local), untouched, 'Install changed user files');
    for(const name of ['okf.yml','docs','.okf','.claude']) assert.equal(fs.existsSync(path.join(global,name)),false,'Global install generated project files');
    for (const [root, packageRoot, globalInstall] of [[local, localPackage, false], [global, globalPackage, true]]) {
      const cli = installedCli(packageRoot, expectedVersion);
      for (const file of artifact.required) assert.ok(fs.existsSync(path.join(packageRoot, file)), `Installed asset missing: ${file}`);
      const run = args => command(process.execPath, [cli, '--root', root, ...args], root, env);
      run(['init', '--site-name', 'Package Smoke', '--layer', 'api=src/**']);
      run(['index', '--write']); run(['lint', '--strict']); run(['render']);
      assert.ok(fs.existsSync(path.join(root, '_site/index.html')));
      fs.appendFileSync(path.join(root, 'okf.yml'), '\n# User-edited configuration preserved\n');
      for (const extension of ['sh','ps1']) fs.appendFileSync(path.join(root, '.okf/hooks', `render_hook.${extension}`), '\n# User-edited hook comment\n');
      const before = snapshot(root);
      run(['init']); // Re-init must preserve configuration and existing documentation.
      assert.deepEqual(snapshot(root), before);
      const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
      assert.equal(manifest.private, true); assert.equal(manifest.description, 'preserve this manifest');
      if (globalInstall) assert.ok(fs.existsSync(path.join(prefix, process.platform === 'win32' ? 'okf.cmd' : 'bin/okf')));
      else {
        const hook = path.join(root, '.okf/hooks', process.platform === 'win32' ? 'render_hook.ps1' : 'render_hook.sh');
        const executable = process.platform === 'win32' ? path.join(process.env.SystemRoot, 'System32/WindowsPowerShell/v1.0/powershell.exe') : '/bin/sh';
        const args = process.platform === 'win32' ? ['-NoProfile', '-File', hook] : [hook];
        assert.equal(command(executable, args, root, env).trim(), '{}');
      }
      install(root, tarball, globalInstall);
      installedCli(packageRoot, expectedVersion); assert.deepEqual(snapshot(root), before);
      report[globalInstall ? 'global' : 'local'] = true;
    }
    if (previousTarball) {
      // Tests may supply a synthetic older fixture; this is not evidence of historical-release compatibility.
      const previousMetadata = JSON.parse(command('tar', ['-xOf', previousTarball, 'package/package.json'], scratch));
      inspectTarball(previousTarball, previousMetadata.version);
      install(local, previousTarball); installedCli(localPackage, previousMetadata.version);
      const savedManifest = fs.readFileSync(path.join(local, 'package.json'));
      const savedLock = fs.readFileSync(path.join(local, 'package-lock.json'));
      const before = snapshot(local);
      install(local, tarball); installedCli(localPackage, expectedVersion); assert.deepEqual(snapshot(local), before);
      fs.writeFileSync(path.join(local, 'package.json'), savedManifest); fs.writeFileSync(path.join(local, 'package-lock.json'), savedLock);
      npm(['ci', '--global=false', '--prefix', local, '--ignore-scripts', '--no-audit', '--no-fund', '--prefer-offline'], local, env);
      installedCli(localPackage, previousMetadata.version); assert.deepEqual(snapshot(local), before);
      assert.deepEqual(fs.readFileSync(path.join(local, 'package.json')), savedManifest);
      assert.deepEqual(fs.readFileSync(path.join(local, 'package-lock.json')), savedLock);
      const globalBefore = snapshot(global);
      install(global, previousTarball, true); installedCli(globalPackage, previousMetadata.version);
      install(global, tarball, true); installedCli(globalPackage, expectedVersion);
      install(global, previousTarball, true); installedCli(globalPackage, previousMetadata.version);
      assert.deepEqual(snapshot(global), globalBefore);
      report.lifecycle = 'synthetic older -> current -> saved manifest/lock npm ci rollback locally, explicit artifact rollback globally; real historical releases unverified';
    }
    for (const [root, packageRoot, globalInstall] of [[local, localPackage, false], [global, globalPackage, true]]) {
      const before = snapshot(root);
      npm(['uninstall', '--ignore-scripts', '--no-audit', '--no-fund', ...(globalInstall ? ['--global','--prefix',prefix] : ['--global=false','--prefix',root]), 'okf-devkit'], root, env);
      assert.equal(fs.existsSync(packageRoot), false);
      assert.deepEqual(snapshot(root), before, 'Uninstall changed user/generated files');
      assert.equal(JSON.parse(fs.readFileSync(path.join(root,'package.json'),'utf8')).private,true);
      if(globalInstall) assert.equal(fs.existsSync(path.join(prefix, process.platform === 'win32' ? 'okf.cmd' : 'bin/okf')),false);
    }
    report.uninstallPreservation = true;
    report.preservation = true;
    return report;
  } finally { fs.rmSync(scratch, { recursive: true, force: true }); }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = {};
    for (let index = 2; index < process.argv.length; index += 2) {
      const key = { '--tarball': 'tarball', '--expected-version': 'expectedVersion', '--expected-sha256': 'expectedSha256' }[process.argv[index]];
      if (!key || !process.argv[index + 1]) throw new Error('Expected --tarball ABSOLUTE --expected-version VERSION [--expected-sha256 HEX]');
      if (options[key]) throw new Error('Duplicate smoke argument');
      options[key] = process.argv[index + 1];
    }
    if (!options.tarball || !options.expectedVersion) throw new Error('Tarball and expected version are required');
    console.log(JSON.stringify(runSmoke(options)));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
