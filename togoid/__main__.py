"""
TogoID package entry point for python -m togoid
"""

from .cli import main

if __name__ == '__main__':
    import sys
    sys.exit(main())
