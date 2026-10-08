#!/bin/zsh
# Local presentation server: data queries and acknowledged page commands.
set -e
cd -- "${0:A:h}"
if command -v node >/dev/null 2>&1; then
  exec node src/serve_place.mjs --open
fi
print 'Node.js 22 or newer is required. Install it, then run npm run start:place.'
exit 1
