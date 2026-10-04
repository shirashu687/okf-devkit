#!/bin/sh
# Advisory agent completion adapter. Keep strict render_hook.sh for manual use.
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || {
  echo "okf-devkit: cannot locate the agent completion adapter." >&2
  printf '{}\n'
  exit 0
}
if sh "$script_dir/render_hook.sh" >/dev/null; then
  :
else
  echo "okf-devkit: HTML generation failed; run the strict render_hook command to diagnose." >&2
fi
printf '{}\n'
exit 0
