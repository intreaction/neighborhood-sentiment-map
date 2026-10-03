#!/bin/zsh
# Local launch only. Secrets, when configured, are inherited from the environment.
set -e
cd -- "${0:A:h}"
if command -v python3 >/dev/null 2>&1; then
  exec python3 src/serve_place.py --port 8766 --open
fi
print 'Python 3 is required. Install it, then run python3 src/serve_place.py.'
exit 1
