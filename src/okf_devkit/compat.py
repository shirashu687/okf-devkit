"""Named legacy adapters reading caller-owned state at invocation time.

Canonical owners never import CLI; no process-global namespace registry is used.
"""
from __future__ import annotations

from typing import get_type_hints
from . import gitutil
from .gitutil import Commit, _parse_log_z, _consume_change, parse_porcelain_z
import argparse
import datetime as _dt
import glob as _glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path, PurePosixPath
from . import yamlio as _yamlio
from . import config as _config
from .doc import Doc as _Doc, CODE_GLOBS_REQUIRED_TYPES
from .config import CONFIG_FILENAME, DEFAULTS_PATH, RESERVED_DEFAULT, INDEX_LINK_STYLES, merge_config
from .errors import OkfError, MarkerError
from .fsutil import rel_posix, read_text, atomic_write_bytes, write_if_changed, today, now_iso, ISO_DATE_RE, is_iso_date, extract_date, parse_datetime, glob_to_regex, path_matches, _GLOB_CACHE
from .yamlio import YamlSubsetError, _normalize, _MINI_BOOL_TRUE, _MINI_BOOL_FALSE, _MINI_NULL, _MINI_INT_RE, _MINI_FLOAT_RE, _MINI_TS_RE, _mini_timestamp, _mini_scalar, _strip_inline_comment, _MiniYaml, _parse_flow, _flow_skip, _flow_value, _flow_scalar, _YAML_PLAIN_SAFE_RE, yaml_scalar, yaml_flow_list
from .commands import index as _index
from .commands.index import md_escape_label, md_escape_link, md_escape_text, _entry_line, _index_link, _display_title, build_index_block, build_backlog_block, split_markers, _plan_index
from .commands import log as _log
from .commands.log import layer_of, kind_of, format_log_line, recorded_hashes, hashless_entries, insert_log_entries, ENTRY_RE, HASH_RE
from .commands import lint as _lint
from .commands.lint import Finding, _check_actor_entry, trust_level, ACTOR_RE, SENTENCE_END_RE
from .commands import stale as _stale
from .commands import affected as _affected
from .commands.affected import compute_affected
from .commands import new as _new
from .commands.new import slugify, validate_slug, validate_subdir, set_fm_field, next_numbered_id, next_backlog_id, _validate_vocab, SLUG_RE
from .commands import status as _status
from .commands import render as _render
from .commands import sync as _sync
from .commands.sync import STDIN_LIMIT, STDIN_TIMEOUT, GATE_TTL, _read_stdin_json, findings_fingerprint
from .commands import init as _init
from .commands.init import _parse_layer_specs


def install_legacy_exports(ns: dict) -> None:
    """Install explicit adapters without capturing mutable state values."""
    aliases = {
        'gitutil': gitutil,
        'Commit': Commit,
        '_parse_log_z': _parse_log_z,
        '_consume_change': _consume_change,
        'parse_porcelain_z': parse_porcelain_z,
        'argparse': argparse,
        '_dt': _dt,
        '_glob': _glob,
        'hashlib': hashlib,
        'json': json,
        'os': os,
        're': re,
        'subprocess': subprocess,
        'sys': sys,
        'tempfile': tempfile,
        'threading': threading,
        'time': time,
        'webbrowser': webbrowser,
        'Path': Path,
        'PurePosixPath': PurePosixPath,
        '_yamlio': _yamlio,
        '_config': _config,
        '_Doc': _Doc,
        'CODE_GLOBS_REQUIRED_TYPES': CODE_GLOBS_REQUIRED_TYPES,
        'CONFIG_FILENAME': CONFIG_FILENAME,
        'DEFAULTS_PATH': DEFAULTS_PATH,
        'RESERVED_DEFAULT': RESERVED_DEFAULT,
        'INDEX_LINK_STYLES': INDEX_LINK_STYLES,
        'merge_config': merge_config,
        'OkfError': OkfError,
        'MarkerError': MarkerError,
        'rel_posix': rel_posix,
        'read_text': read_text,
        'atomic_write_bytes': atomic_write_bytes,
        'write_if_changed': write_if_changed,
        'today': today,
        'now_iso': now_iso,
        'ISO_DATE_RE': ISO_DATE_RE,
        'is_iso_date': is_iso_date,
        'extract_date': extract_date,
        'parse_datetime': parse_datetime,
        'glob_to_regex': glob_to_regex,
        'path_matches': path_matches,
        '_GLOB_CACHE': _GLOB_CACHE,
        'YamlSubsetError': YamlSubsetError,
        '_normalize': _normalize,
        '_MINI_BOOL_TRUE': _MINI_BOOL_TRUE,
        '_MINI_BOOL_FALSE': _MINI_BOOL_FALSE,
        '_MINI_NULL': _MINI_NULL,
        '_MINI_INT_RE': _MINI_INT_RE,
        '_MINI_FLOAT_RE': _MINI_FLOAT_RE,
        '_MINI_TS_RE': _MINI_TS_RE,
        '_mini_timestamp': _mini_timestamp,
        '_mini_scalar': _mini_scalar,
        '_strip_inline_comment': _strip_inline_comment,
        '_MiniYaml': _MiniYaml,
        '_parse_flow': _parse_flow,
        '_flow_skip': _flow_skip,
        '_flow_value': _flow_value,
        '_flow_scalar': _flow_scalar,
        '_YAML_PLAIN_SAFE_RE': _YAML_PLAIN_SAFE_RE,
        'yaml_scalar': yaml_scalar,
        'yaml_flow_list': yaml_flow_list,
        '_index': _index,
        'md_escape_label': md_escape_label,
        'md_escape_link': md_escape_link,
        'md_escape_text': md_escape_text,
        '_entry_line': _entry_line,
        '_index_link': _index_link,
        '_display_title': _display_title,
        'build_index_block': build_index_block,
        'build_backlog_block': build_backlog_block,
        'split_markers': split_markers,
        '_plan_index': _plan_index,
        '_log': _log,
        'layer_of': layer_of,
        'kind_of': kind_of,
        'format_log_line': format_log_line,
        'recorded_hashes': recorded_hashes,
        'hashless_entries': hashless_entries,
        'insert_log_entries': insert_log_entries,
        'ENTRY_RE': ENTRY_RE,
        'HASH_RE': HASH_RE,
        '_lint': _lint,
        'Finding': Finding,
        '_check_actor_entry': _check_actor_entry,
        'trust_level': trust_level,
        'ACTOR_RE': ACTOR_RE,
        'SENTENCE_END_RE': SENTENCE_END_RE,
        '_stale': _stale,
        '_affected': _affected,
        'compute_affected': compute_affected,
        '_new': _new,
        'slugify': slugify,
        'validate_slug': validate_slug,
        'validate_subdir': validate_subdir,
        'set_fm_field': set_fm_field,
        'next_numbered_id': next_numbered_id,
        'next_backlog_id': next_backlog_id,
        '_validate_vocab': _validate_vocab,
        'SLUG_RE': SLUG_RE,
        '_status': _status,
        '_render': _render,
        '_sync': _sync,
        'STDIN_LIMIT': STDIN_LIMIT,
        'STDIN_TIMEOUT': STDIN_TIMEOUT,
        'GATE_TTL': GATE_TTL,
        '_read_stdin_json': _read_stdin_json,
        'findings_fingerprint': findings_fingerprint,
        '_init': _init,
        '_parse_layer_specs': _parse_layer_specs,
    }
    for name, value in aliases.items():
        ns.setdefault(name, value)

    def find_project_root(start: Path | None=None) -> Path:
        """``okf.yml`` を持つ最も近い祖先ディレクトリを返す。

        見つからない場合は git のトップレベルへフォールバックし、それも無ければ
        起点をそのまま返す（``init`` は設定が無い状態から動く必要があるため、
        ここでは例外にしない）。
        """
        here = (start or ns['Path'].cwd()).resolve()
        for candidate in (here, *here.parents):
            if (candidate / ns['CONFIG_FILENAME']).is_file():
                return candidate
        try:
            out = ns['subprocess'].run(['git', 'rev-parse', '--show-toplevel'], cwd=str(here), capture_output=True, text=True, check=True).stdout.strip()
            if out:
                return ns['Path'](out).resolve()
        except Exception:
            pass
        return here

    def parse_yaml(text: str, source: str='<yaml>'):
        """Compatibility adapter for callers overriding cli._pyyaml directly."""
        return ns['_yamlio'].parse_yaml(text, source, backend=ns['_pyyaml'])

    def load_merged_config(cfg_path: Path) -> dict:
        return ns['_config'].load_merged_config(cfg_path, defaults_path=ns['DEFAULTS_PATH'])

    def git(*args: str, cwd: Path | None=None) -> tuple[int, str]:
        return ns['gitutil'].git(ns['REPO_ROOT'], *args, cwd=cwd)

    def git_available() -> bool:
        return ns['gitutil'].git_available(ns['REPO_ROOT'], runner=ns['git'])

    def has_commits() -> bool:
        return ns['gitutil'].has_commits(ns['REPO_ROOT'], runner=ns['git'])

    def is_shallow() -> bool:
        return ns['gitutil'].is_shallow(ns['REPO_ROOT'], runner=ns['git'])

    def repo_web_url() -> str | None:
        return ns['gitutil'].repo_web_url(ns['REPO_ROOT'], runner=ns['git'])

    def resolve_ref(ref: str) -> str | None:
        return ns['gitutil'].resolve_ref(ns['REPO_ROOT'], ref, runner=ns['git'])

    def resolve_commit(ref: str) -> str | None:
        return ns['gitutil'].resolve_commit(ns['REPO_ROOT'], ref, runner=ns['git'])

    def path_commit_times() -> dict[str, str]:
        cache = ns['gitutil'].CommitTimesCache(ns['_PATH_TIME_ROOT'], ns['_PATH_TIME_MAP'])
        result = ns['gitutil'].path_commit_times(ns['REPO_ROOT'], cache, runner=ns['git'])
        ns['_PATH_TIME_MAP'], ns['_PATH_TIME_ROOT'] = (cache.mapping, cache.root)
        return result

    def last_commit_time(paths: list[str]) -> str | None:
        return ns['gitutil'].latest_commit_time(paths, ns['path_commit_times']())

    def resolve_resource(resource: str) -> list[str]:
        return ns['gitutil'].resolve_resource(ns['REPO_ROOT'], resource)

    def render_index(bundle: Bundle, directory: Path, block: str) -> str:
        return ns['_index'].render_index(bundle, directory, block, repo_root=ns['REPO_ROOT'])

    def cmd_index(bundle: Bundle, args) -> int:
        return ns['_index'].cmd_index(bundle, args, repo_root=ns['REPO_ROOT'], writer=ns['write_if_changed'])

    def collect_commits(rev_range: str | None, exclude: str | None=None) -> list[Commit]:
        return ns['gitutil'].collect_commits(ns['REPO_ROOT'], rev_range, exclude, runner=ns['git'])

    def log_baseline_sha(bundle: Bundle) -> str | None:
        return ns['_log'].log_baseline_sha(bundle, repo_root=ns['REPO_ROOT'], runner=ns['git'])

    def cmd_log(bundle: Bundle, args) -> int:
        return ns['_log'].cmd_log(bundle, args, repo_root=ns['REPO_ROOT'], runner=ns['git'], writer=ns['write_if_changed'])

    def run_lint(bundle: Bundle) -> list[Finding]:
        return ns['_lint'].run_lint(bundle, repo_root=ns['REPO_ROOT'], resource_resolver=ns['resolve_resource'], index_renderer=ns['render_index'])

    def cmd_lint(bundle: Bundle, args) -> int:
        return ns['_lint'].cmd_lint(bundle, args, linter=ns['run_lint'])

    def run_stale(bundle: Bundle) -> list[dict]:
        return ns['_stale'].run_stale(bundle, resource_resolver=ns['resolve_resource'], commit_time=ns['last_commit_time'])

    def cmd_stale(bundle: Bundle, args) -> int:
        return ns['_stale'].cmd_stale(bundle, args, runner=ns['git'], reporter=ns['run_stale'])

    def changed_paths(base: str) -> list[str]:
        return ns['gitutil'].changed_paths(ns['REPO_ROOT'], base, runner=ns['git'])

    def cmd_affected(bundle: Bundle, args) -> int:
        return ns['_affected'].cmd_affected(bundle, args, path_provider=ns['changed_paths'])

    def ensure_inside_bundle(bundle: Bundle, path: Path) -> Path:
        return ns['_new'].ensure_inside_bundle(bundle, path, repo_root=ns['REPO_ROOT'])

    def load_template(bundle: Bundle, type_name: str) -> str:
        return ns['_new'].load_template(bundle, type_name, repo_root=ns['REPO_ROOT'])

    def cmd_new(bundle: Bundle, args) -> int:
        return ns['_new'].cmd_new(bundle, args, repo_root=ns['REPO_ROOT'], writer=ns['write_if_changed'], template_loader=ns['load_template'], path_validator=ns['ensure_inside_bundle'])

    def backlog_docs(bundle: Bundle) -> list[Doc]:
        return ns['_status'].backlog_docs(bundle, repo_root=ns['REPO_ROOT'], doc_factory=ns['Doc'])

    def cmd_status(bundle: Bundle, args) -> int:
        return ns['_status'].cmd_status(bundle, args, reader=ns['backlog_docs'])

    def cmd_render(bundle: Bundle, args) -> int:
        return ns['_render'].cmd_render(bundle, args, repo_root=ns['REPO_ROOT'], doc_factory=ns['Doc'])

    def gate_state_dir() -> Path:
        return ns['_sync'].gate_state_dir(ns['REPO_ROOT'], runner=ns['git'])

    def _gate_state_file(session_id: str | None) -> Path:
        return ns['_sync']._gate_state_file(ns['REPO_ROOT'], session_id, state_dir=ns['gate_state_dir'])

    def resolve_session_id(args) -> str | None:
        return ns['_sync'].resolve_session_id(args, payload_reader=ns['_read_stdin_json'])

    def gate_bump(session_id: str | None, fingerprint: str | None) -> int:
        return ns['_sync'].gate_bump(ns['REPO_ROOT'], session_id, fingerprint, state_file_provider=ns['_gate_state_file'], ttl=ns['GATE_TTL'])

    def _has_local_changes() -> bool:
        return ns['_sync']._has_local_changes(ns['REPO_ROOT'], runner=ns['git'])

    def cmd_sync(bundle: Bundle, args) -> int:
        return ns['_sync'].cmd_sync(bundle, args, indexer=ns['cmd_index'], logger=ns['cmd_log'], linter=ns['run_lint'], stale_reporter=ns['run_stale'], dirty_checker=ns['_has_local_changes'], session_resolver=ns['resolve_session_id'], gate_counter=ns['gate_bump'])

    def _scaffold_text(rel: str) -> str:
        return ns['_init']._scaffold_text(rel, scaffold_dir=ns['SCAFFOLD_DIR'])

    def _render_okf_yml(bundle_root: str, site_name: str, layers: list[tuple[str, str, str]]) -> str:
        return ns['_init']._render_okf_yml(bundle_root, site_name, layers, scaffold_reader=ns['_scaffold_text'])

    def cmd_init(args) -> int:
        return ns['_init'].cmd_init(ns['REPO_ROOT'], args, scaffold_dir=ns['SCAFFOLD_DIR'], scaffold_reader=ns['_scaffold_text'], writer=ns['write_if_changed'], config_renderer=ns['_render_okf_yml'])

    adapters = {
        'find_project_root': find_project_root,
        'parse_yaml': parse_yaml,
        'load_merged_config': load_merged_config,
        'git': git,
        'git_available': git_available,
        'has_commits': has_commits,
        'is_shallow': is_shallow,
        'repo_web_url': repo_web_url,
        'resolve_ref': resolve_ref,
        'resolve_commit': resolve_commit,
        'path_commit_times': path_commit_times,
        'last_commit_time': last_commit_time,
        'resolve_resource': resolve_resource,
        'render_index': render_index,
        'cmd_index': cmd_index,
        'collect_commits': collect_commits,
        'log_baseline_sha': log_baseline_sha,
        'cmd_log': cmd_log,
        'run_lint': run_lint,
        'cmd_lint': cmd_lint,
        'run_stale': run_stale,
        'cmd_stale': cmd_stale,
        'changed_paths': changed_paths,
        'cmd_affected': cmd_affected,
        'ensure_inside_bundle': ensure_inside_bundle,
        'load_template': load_template,
        'cmd_new': cmd_new,
        'backlog_docs': backlog_docs,
        'cmd_status': cmd_status,
        'cmd_render': cmd_render,
        'gate_state_dir': gate_state_dir,
        '_gate_state_file': _gate_state_file,
        'resolve_session_id': resolve_session_id,
        'gate_bump': gate_bump,
        '_has_local_changes': _has_local_changes,
        'cmd_sync': cmd_sync,
        '_scaffold_text': _scaffold_text,
        '_render_okf_yml': _render_okf_yml,
        'cmd_init': cmd_init,
    }
    ns.update(adapters)
    for name, adapter in adapters.items():
        adapter.__module__ = ns["__name__"]
        adapter.__qualname__ = name
        # Resolve against this facade's actual legacy classes.
        adapter.__annotations__ = get_type_hints(adapter, globalns=ns, localns=ns)
