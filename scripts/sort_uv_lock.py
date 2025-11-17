import sys
import re
from pathlib import Path
from difflib import unified_diff

def sort_uv_lock(path: Path) -> int:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)

    # find indices of top-level '[[package]]' lines
    package_starts = [i for i,l in enumerate(lines) if l.strip() == '[[package]]']
    if not package_starts:
        print('No [[package]] blocks found.')
        return 1

    header_lines = lines[:package_starts[0]]

    blocks = []
    for idx, start in enumerate(package_starts):
        end = package_starts[idx+1] if idx+1 < len(package_starts) else len(lines)
        block_lines = lines[start:end]
        block_text = ''.join(block_lines)
        # extract name = "..." from the block
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', block_text, re.MULTILINE)
        name = m.group(1) if m else ''
        blocks.append((name, block_text))

    # sort by name (case-insensitive but stable)
    blocks_sorted = sorted(blocks, key=lambda x: x[0].lower())

    new_text = ''.join(header_lines) + ''.join(b for _,b in blocks_sorted)

    # produce unified diff
    orig = text.splitlines(keepends=True)
    new = new_text.splitlines(keepends=True)
    diff = ''.join(unified_diff(orig, new, fromfile=str(path), tofile=str(path) + '.sorted'))

    # write sorted content back to file
    path.write_text(new_text, encoding='utf-8')

    # also write a .sorted copy for inspection
    (path.parent / (path.name + '.sorted')).write_text(new_text, encoding='utf-8')

    if diff:
        print(diff)
    else:
        print('No changes (already sorted).')
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python sort_uv_lock.py <path-to-uv.lock>')
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.exists():
        print(f'File not found: {p}')
        sys.exit(2)
    sys.exit(sort_uv_lock(p))
