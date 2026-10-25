"""Inspect the Git index for runtime files and obvious embedded credentials.

This is a publication guard for the current snapshot, not a full-history audit.
Only paths and line numbers are printed when a finding is detected.
"""

import re
import subprocess
import sys
from pathlib import PurePosixPath


def main() -> int:
    paths = subprocess.check_output(['git', 'ls-files', '-z'], text=True).split('\0')
    findings = []
    patterns = [
        re.compile(r'sk-[A-Za-z0-9_-]{20,}'),
        re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),
        re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        re.compile(r'''(?:api.?key|api.?secret|secret|password|access.?token)["']?\s*[:=]\s*["']([A-Za-z0-9+/=_-]{40,})["']''', re.I),
    ]
    allowed_examples = ('your_', 'your-', 'example', 'test_', '${', '<')
    for name in filter(None, paths):
        path = PurePosixPath(name)
        if path.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.xlsx', '.pem', '.key', '.log'}:
            findings.append(f'{name}: runtime or credential file')
        if any(part in {'.idea', '.vscode', '.venv', 'runtime', 'logs', 'tmp', 'temp', 'cache'} for part in path.parts):
            findings.append(f'{name}: local/runtime directory')
        if path.name in {'.env', '.secret_key', '.encrypted_config'}:
            findings.append(f'{name}: local credential file')
        result = subprocess.run(['git', 'show', f':{name}'], capture_output=True, check=True)
        if b'\0' in result.stdout:
            continue
        text = result.stdout.decode('utf-8-sig', errors='replace')
        for number, line in enumerate(text.splitlines(), 1):
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    value = match.group(1) if match.lastindex else match.group()
                    if not any(value.lower().startswith(prefix) for prefix in allowed_examples):
                        findings.append(f'{name}:{number}: possible embedded credential')
    print('\n'.join(findings) if findings else 'Publication snapshot check passed')
    return bool(findings)


if __name__ == '__main__':
    sys.exit(main())
