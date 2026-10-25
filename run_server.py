"""Compatibility entry point for python run_server.py --port 8000."""

import sys

from main import main

if __name__ == '__main__':
    raise SystemExit(main(['api', *sys.argv[1:]]))
