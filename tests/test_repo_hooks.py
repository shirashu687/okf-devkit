"""Repository-only hook contracts; no agent/model sessions or user settings."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RepoHookTests(unittest.TestCase):
    def test_tool_configs_are_bounded_advisory_completion_events(self):
        copilot = json.loads((ROOT / '.github/hooks/okf-render.json').read_text())
        self.assertEqual(copilot['version'], 1)
        self.assertEqual(set(copilot['hooks']), {'agentStop'})
        handler = copilot['hooks']['agentStop'][0]
        self.assertEqual(handler['cwd'], '.')
        self.assertEqual(handler['timeoutSec'], 60)
        self.assertIn('agent_stop.sh', handler['bash'])
        self.assertIn('agent_stop.ps1', handler['powershell'])
        codex = json.loads((ROOT / '.codex/hooks.json').read_text())
        self.assertEqual(set(codex['hooks']), {'Stop'})
        handler = codex['hooks']['Stop'][0]['hooks'][0]
        self.assertEqual(handler['timeout'], 60)
        self.assertIn('agent_stop.ps1', handler['commandWindows'])
        self.assertNotIn('Bypass', handler['commandWindows'])

    def _shell(self):
        found = shutil.which('sh') or shutil.which('bash')
        if found:
            return found
        git = shutil.which('git')
        if git and os.name == 'nt':
            candidate = Path(git).resolve().parents[1] / 'bin/sh.exe'
            if candidate.is_file():
                return str(candidate)
        return None

    def test_posix_advisory_success_failure_and_stderr(self):
        shell = self._shell()
        if not shell:
            self.skipTest('POSIX shell unavailable')
        for status in (0, 1, 2):
            with self.subTest(status=status), tempfile.TemporaryDirectory(prefix='okf hook ') as tmp:
                folder = Path(tmp)
                shutil.copyfile(ROOT / '.okf/hooks/agent_stop.sh', folder / 'agent_stop.sh')
                (folder / 'render_hook.sh').write_text(
                    f"printf 'untrusted output\\n'; printf 'diagnostic\\n' >&2; exit {status}\n")
                proc = subprocess.run([shell, str(folder / 'agent_stop.sh')], input='{"cwd":"secret; echo EXECUTED"}', capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), '{}')
                self.assertIn('diagnostic', proc.stderr)
                self.assertNotIn('secret', proc.stdout + proc.stderr)
                self.assertNotIn('EXECUTED', proc.stdout + proc.stderr)
                self.assertEqual('generation failed' in proc.stderr, status != 0)

    def test_powershell_advisory_success_failure_and_stderr(self):
        shell = shutil.which('powershell') or shutil.which('pwsh')
        if not shell:
            self.skipTest('PowerShell unavailable')
        for status in (0, 1, 2):
            with self.subTest(status=status), tempfile.TemporaryDirectory(prefix='okf hook ') as tmp:
                folder = Path(tmp)
                shutil.copyfile(ROOT / '.okf/hooks/agent_stop.ps1', folder / 'agent_stop.ps1')
                (folder / 'render_hook.ps1').write_text(
                    f"[Console]::Out.WriteLine('untrusted output'); [Console]::Error.WriteLine('diagnostic'); exit {status}\n")
                proc = subprocess.run([shell, '-NoProfile', '-File', str(folder / 'agent_stop.ps1')], input='{"cwd":"secret; echo EXECUTED"}', capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), '{}')
                self.assertIn('diagnostic', proc.stderr)
                self.assertNotIn('secret', proc.stdout + proc.stderr)
                self.assertNotIn('EXECUTED', proc.stdout + proc.stderr)
                self.assertEqual('generation failed' in proc.stderr, status != 0)

    def test_registered_launchers_resolve_nested_repository_with_spaces(self):
        shell = self._shell()
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        with tempfile.TemporaryDirectory(prefix='okf hook repo ') as tmp:
            folder = Path(tmp)
            subprocess.run(['git', 'init', '-q', str(folder)], check=True, capture_output=True)
            hooks = folder / '.okf/hooks'
            hooks.mkdir(parents=True)
            nested = folder / 'nested folder'
            nested.mkdir()
            for suffix in ('sh', 'ps1'):
                shutil.copyfile(ROOT / f'.okf/hooks/agent_stop.{suffix}', hooks / f'agent_stop.{suffix}')
            (hooks / 'render_hook.sh').write_text("printf '{}\\n'; exit 0\n")
            (hooks / 'render_hook.ps1').write_text("[Console]::Out.WriteLine('{}'); exit 0\n")
            copilot = json.loads((ROOT / '.github/hooks/okf-render.json').read_text())['hooks']['agentStop'][0]
            codex = json.loads((ROOT / '.codex/hooks.json').read_text())['hooks']['Stop'][0]['hooks'][0]
            launchers = []
            if shell:
                launchers += [[shell, '-c', item] for item in (copilot['bash'], codex['command'])]
            # Registration selects the POSIX command on Linux, even when pwsh
            # is installed. commandWindows deliberately invokes Windows
            # PowerShell; the separate adapter test covers portable pwsh.
            if powershell and os.name == 'nt':
                launchers += [[powershell, '-NoProfile', '-Command', item] for item in (copilot['powershell'], codex['commandWindows'])]
                launchers.append(codex['commandWindows'])
            self.assertTrue(launchers, 'No supported command shell available')
            for command in launchers:
                with self.subTest(command=command[0]):
                    proc = subprocess.run(command, shell=isinstance(command, str), cwd=nested, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=20)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    self.assertEqual(proc.stdout.strip(), '{}')
                    self.assertEqual(proc.stderr, '')

    def test_real_common_render_twice_and_failure_remains_strict(self):
        if not shutil.which('node') or not (ROOT / 'node_modules/markdown-it/package.json').is_file():
            self.skipTest('Node development runtime/dependencies unavailable; run npm ci first')
        shells = []
        if self._shell():
            shells.append((self._shell(), 'sh'))
        powershell = shutil.which('powershell') or shutil.which('pwsh')
        if powershell:
            shells.append((powershell, 'ps1'))
        if not shells:
            self.skipTest('No hook command shell available')
        with tempfile.TemporaryDirectory(prefix='okf real hook ') as tmp:
            folder = Path(tmp)
            subprocess.run(['git', 'init', '-q', str(folder)], check=True, capture_output=True)
            hooks = folder / '.okf/hooks'
            hooks.mkdir(parents=True)
            for source in (ROOT / '.okf/hooks').glob('*'):
                shutil.copyfile(source, hooks / source.name)
            # Forward installed-runtime discovery to the real checkout CLI,
            # preserving its implementation and the fixture's --root argument.
            entry = folder / 'node_modules/okf-devkit/node/cli.mjs'
            entry.parent.mkdir(parents=True)
            entry.write_text(f"import {{ main }} from {json.dumps((ROOT / 'node/cli.mjs').as_uri())};\nprocess.exitCode = await main();\n")
            docs = folder / 'docs'
            docs.mkdir()
            source = docs / 'index.md'
            content = b'---\nokf_version: "0.2"\n---\n# Hook fixture\n'
            source.write_bytes(content)
            config = folder / 'okf.yml'
            valid_config = (ROOT / 'src/okf_devkit/defaults.yml').read_bytes()
            config.write_bytes(valid_config)
            for shell, suffix in shells:
                with self.subTest(shell=suffix):
                    flags = [shell] if suffix == 'sh' else [shell, '-NoProfile', '-File']
                    for _ in range(2):
                        proc = subprocess.run(flags + [str(hooks / f'render_hook.{suffix}')], cwd=folder, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25)
                        self.assertEqual(proc.returncode, 0, proc.stderr)
                        self.assertEqual(proc.stdout.strip(), '{}')
                        self.assertTrue((folder / '_site/index.html').is_file())
                        self.assertEqual(source.read_bytes(), content)
                    config.write_text('[invalid yaml')
                    strict = subprocess.run(flags + [str(hooks / f'render_hook.{suffix}')], cwd=folder, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25)
                    advisory = subprocess.run(flags + [str(hooks / f'agent_stop.{suffix}')], cwd=folder, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=25)
                    self.assertEqual(strict.returncode, 1, strict.stderr)
                    self.assertEqual(strict.stdout, '')
                    self.assertEqual(advisory.returncode, 0, advisory.stderr)
                    self.assertEqual(advisory.stdout.strip(), '{}')
                    self.assertIn('generation failed', advisory.stderr)
                    self.assertEqual(source.read_bytes(), content)
                    config.write_bytes(valid_config)
