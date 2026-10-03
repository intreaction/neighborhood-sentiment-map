"""Read-only publication checks; reports locations, never matching secret values.

Run python3 scripts/audit_public_repo.py [--history]. This is a focused pattern
scan, not a guarantee that credentials or restricted content are absent.
"""
import argparse
import io
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 10 * 1024 * 1024
PATTERNS = {
    'private-key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'github-token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'aws-access-key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'openai-token': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}\b',
    'slack-token': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
}
FORBIDDEN = re.compile(r'(^|/)(?:\.env(?:\..*)?|id_rsa|id_ed25519|credentials|yelp_academic_dataset[^/]*|yelp_dataset[^/]*\.tar(?:\.gz)?|(?:tl|cb)_[^/]*\.zip|[^/]*\.(?:shp|shx|dbf|prj|cpg)|\.DS_Store)$|^(?:data/(?:raw|interim|external|downloads)/|Yelp JSON/)')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def scan(label, raw):
    found = []
    chunks = [(label, raw)]
    if raw.startswith(b'PK'):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                chunks += [(label + ':' + item.filename, archive.read(item))
                           for item in archive.infolist()
                           if item.filename.endswith(('.xml', '.rels', '.txt', '.json'))]
        except zipfile.BadZipFile:
            pass
    for name, content in chunks:
        for kind, pattern in PATTERNS.items():
            if re.search(pattern, content):
                found.append((kind, name))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    findings = []
    paths = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
    count = 0
    for name in sorted(set(filter(None, paths))):
        path = ROOT / name
        if not path.is_file():
            continue
        count += 1
        if FORBIDDEN.search(name) and not name.endswith('.env.example'):
            findings.append(('excluded-file', name))
        if path.stat().st_size > MAX_FILE_BYTES:
            findings.append(('file-over-10-MiB', name))
            continue
        findings += scan(name, path.read_bytes())
    print(f'Working tree: {count} publishable candidate files checked.')
    if args.history:
        objects = git('rev-list', '--objects', '--all').decode().splitlines()
        blobs = 0
        for row in objects:
            sha, _, name = row.partition(' ')
            if git('cat-file', '-t', sha).strip() != b'blob':
                continue
            blobs += 1
            if FORBIDDEN.search(name):
                findings.append(('historical-excluded-file', f'{sha[:12]} {name}'))
            if int(git('cat-file', '-s', sha)) > MAX_FILE_BYTES:
                findings.append(('historical-file-over-10-MiB', f'{sha[:12]} {name}'))
                continue
            findings += scan(f'{sha[:12]} {name}', git('cat-file', 'blob', sha))
        print(f'History: {blobs} unique reachable blobs checked across local refs.')
    for kind, name in findings:
        print(f'FAIL {kind}: {name}')
    print(f'{len(findings)} credential-pattern / excluded-file / size findings.')
    print('Data licensing, excerpts, personal metadata, remote-only refs and unrecognized secrets require separate review.')
    raise SystemExit(bool(findings))


if __name__ == '__main__':
    main()
