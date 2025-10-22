#!/usr/bin/env bash
set -euo pipefail

# optional installs
pip install -r requirements.txt || true

# produce manifest.json via the existing parser
python tests/pytest_to_autograde.py \
  --report pytest_report.json \
  --out-dir autograde_results \
  --score-map tests/score_map.json > manifest.json

# read manifest.json and write runner blobs to GITHUB_OUTPUT so workflow step outputs are set
python - <<'PY'
import json, os, sys
gout = os.environ.get('GITHUB_OUTPUT')
if not gout:
    print("GITHUB_OUTPUT not set", file=sys.stderr)
    sys.exit(1)
with open('manifest.json') as f:
    m = json.load(f)
runners = []
for name, path in m.get('runners', {}).items():
    runners.append(name)
    val = open(path).read()
    key = f'RUN_{name}_RESULTS'
    # append to GITHUB_OUTPUT to set step output
    with open(gout, 'a') as g:
        g.write(f"{key}<<EOF\n")
        g.write(val)
        g.write("\nEOF\n")
# set a RUNNERS step output (comma-separated list)
with open(gout, 'a') as g:
    g.write(f"RUNNERS={','.join(runners)}\n")
# also print for logs
print(','.join(runners))
PY