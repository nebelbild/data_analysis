import sys
from pathlib import Path
from difflib import unified_diff

if len(sys.argv) != 3:
    print('Usage: show_diff.py <file1> <file2>')
    sys.exit(2)

p1 = Path(sys.argv[1])
p2 = Path(sys.argv[2])
if not p1.exists():
    print(f'File not found: {p1}')
    sys.exit(2)
if not p2.exists():
    print(f'File not found: {p2}')
    sys.exit(2)

orig = p1.read_text(encoding='utf-8').splitlines(keepends=True)
new = p2.read_text(encoding='utf-8').splitlines(keepends=True)

diff = list(unified_diff(orig, new, fromfile=str(p1), tofile=str(p2)))
if diff:
    sys.stdout.writelines(diff)
else:
    print('No differences between the files.')
