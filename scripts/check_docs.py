"""Check local inline Markdown file targets in active repository guides.

Historical plans/coursework and external URLs/anchors are intentionally outside
this focused check. It does not parse arbitrary HTML or all Markdown constructs.
"""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = list(ROOT.glob('*.md')) + list((ROOT / 'docs').glob('*.md'))
    files += [ROOT / 'docs/presentation/Presenter-Guide.md', ROOT / 'docs/qa/place-lab.md']
    failures = []
    count = 0
    for path in files:
        text = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        for match in re.finditer(r'\[[^\]\n]*\]\(([^)\n]+)\)', text):
            target = match.group(1).strip().split(' "', 1)[0].strip('<>')
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            count += 1
            if not (path.parent / unquote(parts.path)).exists():
                failures.append(f'{path.relative_to(ROOT)}: {target}')
    for failure in failures:
        print('BROKEN', failure)
    print(f'{len(files)} guides; {count} local file links checked; {len(failures)} broken.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
