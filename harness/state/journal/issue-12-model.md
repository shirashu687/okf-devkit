# Issue #12 stage3 Doc/config extraction

Base: 111f04ea2ee827e6c6652d24775fbb5c450d4227. Authorized staged model extraction with no public command changes. Canonical models receive repo_root explicitly; temporary CLI subclasses preserve two-argument Doc and injected CLI roots. Preserve all previous tests and YAML owner seams. No Git dependency or cycle.

Planned verification: focused model/context, complete Python, Node native/compat, affected/docs/index/lint/render, task and stacked PR declarations, independent parent review. No release/merge or actual user migration.

## Implemented contract

- Canonical `doc.Doc(path, bundle_root, *, repo_root)` requires explicit project root. `config.Bundle(config_path=None, *, repo_root, doc_factory=Doc, defaults_path=DEFAULTS_PATH)` captures `.repo_root`; `.root` remains the document bundle root. Existing config path interpretation is preserved.
- CLI two-argument Doc and Bundle remain thin subclasses; legacy Bundle passes CLI Doc factory and captured root so cached/new documents remain `isinstance(cli.Doc)` after CLI root changes. No global root-provider registry or model/Git cycle.
- Packaged defaults/scaffold paths, exception identity, YAML owner and legacy parser aliases preserved. All migrated Doc/Bundle methods except constructors/docs factory and merge_config are AST-identical to fixed base. No commands/options removed, no release or user-file migration.
- Protected two new test paths declared before edits. Existing tests/helpers/backend seams unchanged. Five affected docs updated with ownership/globs and actual UTC; unaffected historical declarations unchanged. Git stage4 and command stage5/cli <=200 remain incomplete.

## Verification observations

| Result | Evidence | Limit |
| --- | --- | --- |
| Success | focused `test_doc test_config test_cli_context`:18 pass, skip0 | Explicit two roots, types/cache, foreign CWD/defaults, reserved/excluded files, log paths and actual YAML owner |
| Success | full Python230 tests, failures0/errors0, skip1 | Existing Windows symlink permission skip retained; workspace `issue12-model-python.txt` |
| Success | npm ci8 added/9 audited/0 vulnerabilities; npm native30 pass, skip0 | Workspace `issue12-model-node.txt`; isolated fixtures only |
| Failure, recovered | First source extraction omitted `_yamlio` import; first focused runNameError | Fixed actual owner import, repeated focused18/full230 successful |
| Failure, recovered | First new log-path assertion assumed shared/log.md | Package defaults correctly specify log.md; fixture assertion corrected and tested fallback unmapped/log.md separately |
| Failure, environment correction | First compatibility run5pass/8fail used relative PYTHONPATH=src under fixture CWD | Existing installed older package was imported, evidenced parser rejecting cleanup option and missing _site; rerun uses absolute worktree src and same authorized venv |
| Success | Python/Node lint error0/warn0,index latest, rendercheck31pages/warn0/write0/delete0 | No check creates output/manifest/backup |
| Success | affected source/test coverage complete; only bundle-external journal/declarations uncovered | All five affected docs updated |
| Success | task and stacked PR declarations both result=ok at fixedbase111f04e; diffcheck | Declarations are not semantic approval |
| Not executed | final SHA CI/GitHub push/DraftPR | Parent owns remote operations and independent final review |

No secrets/user data recorded. No global hook/user outputs touched. No full retrospective trigger introduced: ledger historical observations retained, no adopted ID or scoring change. Parent owns independent review and final CI.

Compatibility environment correction completed: absolute PYTHONPATH=C:/Users/rinta/Documents/Codex/2026-10-03/task/issue12-model/src and authorized existing venv; final compatibility13pass/0fail/skip0, workspace issue12-model-compat-final.txt.

## Source freeze and final evidence

Source commit `0fd9627d9d3727e2ac283dda32acff4576a119c2`. Subsequent writes are CLI layer commit-hash log and worklog only; source/tests/docs bodies are frozen for independent parent review. Completing mandatory full Python after final log insertion, then final record commit.

Independent parent reviewers (Spec/Standards) reported findings0/blocking0 before final freeze. Low-level relative config_path remains CWD-relative exactly as before; independent canonical usage should pass an absolute config path. CLI resolves --root/--config before constructing its Bundle. This technical compatibility choice does not add a new product decision.

Final mandatory full Python after source-hash CLI log:230 tests/failures0/errors0/skip1, exit0; Ran 230 tests in 67.372s. Output workspace issue12-model-python-final.txt. Python/Node final lint0error/0warn,index latest,render31pages/warn0/write0/delete0. Task/stacked-PR declarations both result=ok at base111f04ea2ee827e6c6652d24775fbb5c450d4227. Final record commit changes only docs/cli/log.md and this worklog; no source/test change from independently reviewed source0fd9627. Freeze after this record commit; parent final-head review/CI remain not executed by child.
