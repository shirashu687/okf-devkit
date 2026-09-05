#!/bin/sh
# okf-devkit: エージェントの Stop hook から閲覧用 HTML を再生成する。
#
# 成功時は空の JSON `{}` を返し、失敗時は終了コード 1 を返す。
# 終了コード 2 や `decision: block` は使わないため、HTML 生成を理由に
# モデルの継続実行が発生することはない。
set -eu

repo_root=$(git rev-parse --show-toplevel)

# git worktree で作業している場合、.venv は主ワークツリー側にあることが多い。
common_git_dir=$(git rev-parse --git-common-dir)
case "$common_git_dir" in
  /* | [A-Za-z]:/*) ;;
  *) common_git_dir="$repo_root/$common_git_dir" ;;
esac
primary_worktree=${common_git_dir%/*}

cd "$repo_root"

# 1. venv 内の okf コマンド
for candidate in \
  "$repo_root/.venv/bin/okf" \
  "$repo_root/.venv/Scripts/okf.exe" \
  "$primary_worktree/.venv/bin/okf" \
  "$primary_worktree/.venv/Scripts/okf.exe"
do
  if [ -x "$candidate" ]; then
    exec "$candidate" render --hook
  fi
done

# 2. venv 内の python から module 実行
for candidate in \
  "$repo_root/.venv/bin/python" \
  "$repo_root/.venv/Scripts/python.exe" \
  "$primary_worktree/.venv/bin/python" \
  "$primary_worktree/.venv/Scripts/python.exe"
do
  if [ -x "$candidate" ] && "$candidate" -c 'import okf_devkit' >/dev/null 2>&1; then
    exec "$candidate" -m okf_devkit render --hook
  fi
done

# 3. PATH 上の okf / python
if command -v okf >/dev/null 2>&1; then
  exec okf render --hook
fi
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import okf_devkit' >/dev/null 2>&1; then
    exec "$candidate" -m okf_devkit render --hook
  fi
done

echo "okf-devkit が見つかりません。プロジェクトの .venv に 'pip install okf-devkit' を実行してください。" >&2
exit 1
