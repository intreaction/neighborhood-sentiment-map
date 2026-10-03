#!/bin/sh
# Finder and Terminal both launch the demo from this repository's own location.
set -eu
DEMO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -x "$DEMO_ROOT/.venv/bin/python3" ]; then
    DEMO_PYTHON="$DEMO_ROOT/.venv/bin/python3"
elif [ -x "$DEMO_ROOT/../.venv/bin/python3" ]; then
    DEMO_PYTHON="$DEMO_ROOT/../.venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    DEMO_PYTHON=$(command -v python3)
else
    printf '%s\n' 'Python 3 is required to start the local demo.' 'Use the screenshots in docs/qa/ as the presentation fallback.'
    exit 1
fi
exec "$DEMO_PYTHON" "$DEMO_ROOT/src/start_demo.py" "$@"
