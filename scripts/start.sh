#!/bin/zsh
set -e
cd "${0:A:h:h}"
if [[ ! -x .venv/bin/python ]]; then
  print 'Run scripts/setup.sh first.'
  exit 1
fi
if [[ ! -f web/dist/index.html ]]; then npm --prefix web run build; fi
print 'Comm Control: http://127.0.0.1:8765'
print 'In another Terminal: .venv/bin/python scripts/open_app.py'
exec .venv/bin/uvicorn server.main:create_app --factory --host 127.0.0.1 --port 8765
