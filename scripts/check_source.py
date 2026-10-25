"""Parse every tracked Python source without importing or executing it."""

import ast
import subprocess
import sys
from pathlib import Path


def main() -> int:
    paths = subprocess.check_output(['git', 'ls-files', '-z'], text=True).split('\0')
    errors = []
    count = 0
    for name in paths:
        if not name.endswith('.py'):
            continue
        path = Path(name)
        if not path.is_file():
            continue
        count += 1
        try:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f'{name}: {exc}')
    print('\n'.join(errors) if errors else f'Parsed {count} tracked Python files successfully')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
