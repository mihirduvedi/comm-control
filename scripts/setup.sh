#!/bin/zsh
set -e
cd "${0:A:h:h}"
python3 - <<'PY'
import shutil
free=shutil.disk_usage('.').free/1024**3
print(f'Available disk: {free:.1f} GiB. No AI model weights will be downloaded.')
if free<.5:raise SystemExit('Free at least 500 MiB before installing project dependencies.')
PY
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
npm --prefix web ci
npm --prefix web run build
print 'Ready. Configure a Free-tier Groq key: .venv/bin/python scripts/configure_key.py'
print 'Start: scripts/start.sh'
