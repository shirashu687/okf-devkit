# Repository work

Read `AGENTS.md`, `harness/core/policy/requirements.md` and
`harness/project/config.md` before working. Follow their verification and reporting
rules; do not treat a completion hook as verification of the change.

The repository completion hook renders the local OKF viewer. When hooks are not
available, run the shared strict command from this repository:

- POSIX: `sh .okf/hooks/render_hook.sh`
- Windows: `powershell -NoProfile -File .okf/hooks/render_hook.ps1`

Record failures honestly. Setup and tool-specific trust prerequisites are in
`docs/agents/completion-hooks.md`; do not change user or global settings.
