# Issue #12 stage5b: remaining command extraction

Fixed author base: `3c97cf0383652b8ca072540fe59e6877383dbbd2`. Each command is extracted and committed only after full Python and compatibility checks. All remaining constructor/global/callback sites were audited before editing (external issue12-commands-b-preaudit.json). Status has one direct Doc constructor; render uses a Doc factory callback; stale requires one caller-owned cache shared across its document loop. Canonical commands must not import CLI or copy its mutable root.

## stale
Canonical stale uses one invocation-local CommitTimesCache for all document resources and explicit Bundle.repo_root Git calls. Legacy root/helper seams are passed as resource/time/report/Git callbacks. Owner/cache regression passed; full Python 244 run, failures 0, errors 0, skipped 1; compatibility 13 pass. Evidence: task/issue12-commands-b-stale-python.log and -stale-compat.log. No Doc/Bundle constructors in this moved block.

## affected
Canonical affected obtains changed paths once before the document loop, using explicit Bundle.repo_root Git calls; matching uses the shared pure glob owner. Legacy changed_paths callback is retained. Owner Git and actual document/path mapping regression passed. Full Python 245 run, failures 0, errors 0, skipped 1; compatibility 13 pass. No Doc/Bundle constructors in this moved block. Evidence: task/issue12-commands-b-affected-python.log and -affected-compat.log.

## new
Canonical new uses Bundle.repo_root for output/error paths and keeps creation inside bundle.root. Template/path/writer callbacks preserve legacy CLI override seams. Canonical writer and output-root regression passed. Full Python 246 run, failures 0, errors 0, skipped 1; compatibility 13 pass. No Doc/Bundle constructors in the moved block. Evidence: task/issue12-commands-b-new-python.log and -new-compat.log.
