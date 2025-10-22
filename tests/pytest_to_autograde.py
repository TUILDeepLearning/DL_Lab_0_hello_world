import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

def sanitize_name(s):
    return s.replace('/', '_').replace('\\', '_').replace('.', '_')

parser = argparse.ArgumentParser()
parser.add_argument('--report', required=True, help='pytest json-report file (from --json-report-file)')
parser.add_argument('--score-map', help='optional JSON file mapping nodeid or filename -> max_score')
parser.add_argument('--out-dir', default='autograde_results', help='directory to write per-runner result JSONs')
args = parser.parse_args()

report = json.load(open(args.report, 'r'))
score_map = {}
if args.score_map:
    score_map = json.load(open(args.score_map, 'r'))

# Flatten test entries
tests = report.get('tests', [])
# Group by test file
groups = defaultdict(list)
for t in tests:
    # nodeid looks like 'tests/test_foo.py::test_bar'
    nodeid = t.get('nodeid')
    file = nodeid.split('::')[0]
    groups[file].append(t)

out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

def make_grader_blob(name, tests_in_group):
    # default: equal weighting across tests in group unless score_map overrides
    max_score = 0.0
    entries = []
    earned = 0.0
    for t in tests_in_group:
        nid = t.get('nodeid')
        outcome = t.get('outcome')  # 'passed'|'failed'|'skipped'
        # score key precedence: exact nodeid -> filename -> default 1.0
        ms = score_map.get(nid, None)
        if ms is None:
            ms = score_map.get(name, None)
        if ms is None:
            ms = 1.0
        max_score += float(ms)
        passed = 1 if outcome == 'passed' else 0
        earned += passed * float(ms)
        message = ''
        if outcome == 'failed':
            # pytest-json-report stores longreprtext or longrepr
            message = t.get('longrepr', '') or t.get('longreprtext', '') or ''
        entries.append({
            'name': nid,
            'status': outcome,
            'message': message,
            'duration': t.get('duration', 0.0),
            'max_score': ms,
            'score': float(ms) if outcome == 'passed' else 0.0
        })
    blob = {
        'score': earned,
        'max_score': max_score,
        'output': f'Passed {sum(1 for e in entries if e["status"]=="passed")} / {len(entries)}',
        'tests': entries
    }
    return blob

# produce one grader JSON per file (runner name = sanitized filename)
runner_files = []
for fname, tlist in groups.items():
    runner_name = sanitize_name(fname)
    blob = make_grader_blob(fname, tlist)
    out_path = out_dir / f'{runner_name}.json'
    with open(out_path, 'w') as f:
        json.dump(blob, f)
    runner_files.append((runner_name, out_path))

# Print small manifest for GitHub Actions consumption
manifest = {name: str(path) for name, path in runner_files}
print(json.dumps({'runners': manifest}))