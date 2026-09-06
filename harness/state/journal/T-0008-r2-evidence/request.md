# R2: rendered heading anchors

Fix the existing page-internal navigation bug in okf-devkit HTML output. Markdown headings `## Foo`, `## Foo`, `## Foo-2` currently render heading IDs `foo`, `foo-2`, `foo-2`; the last two TOC entries consequently target the same element. The reverse order `Foo-2 / Foo / Foo` also collides. This is an existing renderer/TOC behavior defect, not a new output format.

Acceptance:
1. Heading IDs are unique for both collision orders and TOC entries target the corresponding headings.
2. Noncolliding existing `Foo / Foo / Bar` anchors remain `foo / foo-2 / bar`.
3. Repeated rendering is deterministic; repeated/suffixed headings cannot introduce another duplicate. Exact new suffix spelling for collisions is not prescribed.
4. Add meaningful regression coverage through rendered output, preserve existing tests and other renderer behavior.
5. All mandatory local checks from TRIAL.md pass. Environment failures and intentional red tests remain separately recorded. No CI result is inferred.

Scope: renderer and necessary regression tests, relevant documentation only if affected. Existing API/CLI, dependencies, security policy, CI and upstream skills remain unchanged. The coordinator will provide independent review after your first completed submission; do not delegate or contact another agent during implementation. All implementation choices are yours.

Before implementation, read your own AGENTS.md and TRIAL.md. Confirm actual Python version, yaml/markdown-it versions, imported okf_devkit location in your clone, clean status and assigned checkpoint. If any differ from the defined conditions, stop and report. Otherwise perform the task and maintain the common measurement files defined in TRIAL.md. Final response must give measured/self-recorded counts and their limitations, check results, changes, and outstanding issues. Leave changes uncommitted; do not inspect another clone, earlier trial or external source. This file is the complete task request for both implementations.
