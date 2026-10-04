# Issue12 stage4 Git extraction

Base: 1d039cc635811240fcfddfcf19ae1c9b293156d6

Canonical Git functions receive project root and optional runner explicitly; commit-time cache receives an explicit object. CLI compatibility adapters preserve mutable root/cache and runner seams. Existing Git assertions remain unchanged. Independent review and final verification pending.

## Implementation and evidence

Source commit: d1fd3c9007cce16af15de6211742f78824532ade. Git helpers, pure parsers/Commit, resources and gate probes moved without command-body changes; CLI imports canonical owner and retains current-root/cwd/runner adapters. CommitTimesCache is caller-owned and root-keyed; legacy map/root writes are synchronized. Existing test_git 15 and new owner regression 8 passed.

Initial Python run executed 238 tests with zero failures/errors and 2 skips while npm ci was in parallel; this is not the final acceptance result. Its compact log does not identify the extra skip; dependency-unavailable hook coverage is a hypothesis, not measured proof. Final verbose run below will determine the applicable skip reason after npm ci. npm ci succeeded; Node 30 and compatibility 13 passed, zero skips/failures. Logs: ../issue12-git-npmci.txt, ../issue12-git-node.txt, ../issue12-git-compat.txt.

Independent prereview: Standards blocking0/findings0; Spec source blocking0, one migration-document ambiguity about historical stage3 completion was corrected before source commit. Final exact-SHA review remains pending. docs affected: architecture, commands, migration, output-cleanup, scaffold reference all reviewed with owner/glob/UTC updates. CLI/render/scaffold logs cite the actual source commit.

## Final local verification

After npm ci completed and all source/doc/log content was finalized, `tests/run_all.py -v` executed 238 tests: failures0/errors0/skip1, exit0. The only skipped test is test_render_cleanup.CleanupTests.test_symlink_rejected, reason symlink unavailable on this Windows environment. Hook Node dependency coverage ran successfully; the initial additional skip is not used for acceptance and its exact initial reason remains unobserved. Evidence: ../issue12-git-python-final.txt. Node30/compat13 zero failures/skips remain applicable to unchanged runtime source.

Docs index --write/check latest; lint errors0/warnings0; render --check 31pages/write0/delete0/warn0. Affected docs reviewed; management journals remain outside OKF as configured. Both task and pull-request declaration checks with exact base1d039cc passed; staged/final diff and markers checked. Command/entry AST unchanged; doc/config/yaml/errors/fsutil plus existing test_git/test_cli_context Git blobs equal to base.

Evidence SHA256:
- issue12-git-python-final.txt: 6ecbebbb0dce96bb51d07e0eacee1db23c9ba62f0c8ddbb971f292b54bd12a5f
- issue12-git-npmci.txt: 0e2ab4a1d188cc257a39fb74e6244a7fa2816bb4da631b08212b80b2e32bdc48
- issue12-git-node.txt: cad18519ddd743c0e977f1ded0e2c262be924306f0249eba18d335d84eaa38e2
- issue12-git-compat.txt: e7fb251e8a3057c66c06ecae0f47ffc771e8967181f18eb420d316ad4cc6ee56
- issue12-git-affected-final.txt: e4dec9a0149e26015c7a1e21ebefed4c0741cad10857d4356f417adcc533d26c

This final commit records validation and actual source-commit layer logs only; it changes no runtime, tests, or explanatory documentation. Final exact-SHA independent Spec/Standards review and remote CI are parent-owned and pending. Stages5/6 commands/entry remain outstanding; no push or GitHub operation performed by this agent.
