"""Helpers for reading list inputs given on the command line."""

import sys
from typing import List


def read_list_file(path: str) -> List[str]:
    """
    Read a list file with one entry per line.

    Blank lines are skipped and surrounding whitespace is stripped; commas are
    kept as part of an entry. A path of ``-`` reads from standard input.
    """
    if path == "-":
        return [line.strip() for line in sys.stdin if line.strip()]
    with open(path, "r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]
