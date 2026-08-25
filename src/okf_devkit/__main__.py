"""`python -m okf_devkit` で CLI を起動する。"""

import sys

from .cli import run

if __name__ == "__main__":
    sys.exit(run())
