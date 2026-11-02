"""Merge heads-up / sit & go crawls into sng-data.js (new records win), validating every record.
Usage: python tools/merge_sng.py sng-data.js sng-data.js ranges.json [more.json ...]  (the first file may not exist yet)"""
import collections
import json
import os
import sys

old_js, out_js, *new_jsons = sys.argv[1:]
B64 = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
HEAD = 'window.SNG_DATA='
TAGS = {'mtthu': 2, 'husng': 2, 'spin3': 3}  # tag -> players

if os.path.exists(old_js):
    with open(old_js, encoding='utf-8') as fh:
        text = fh.read().strip()
    old = json.loads(text[len(HEAD):].rstrip(';'))
else:
    old = {'v': 1, 'source': 'solver', 'spots': []}


def valid(rec):
    try:
        fam, tag, gt, n, dp, hero, vs, caller, pos, acts, f, l, r, hist = rec
        return (TAGS.get(tag) == n and 0 < dp <= 200 and 0 <= hero < n and len(acts) == len(f) == len(l) >= 1
                and all(len(a) == 5 for a in acts)
                and all(len(x) == 169 and set(x) <= B64 for x in f + l) and (r == '' or (len(r) == 169 and set(r) <= B64)))
    except Exception:
        return False


def key(rec):
    return (rec[1], rec[2], rec[4], rec[13] or '', rec[0], rec[5], rec[6], rec[7])


merged, invalid, replaced, sources = {}, 0, 0, [('old', len(old['spots']))]
for rec in old['spots']:
    merged[key(rec)] = rec
for path in new_jsons:
    with open(path, encoding='utf-8') as fh:
        recs = json.load(fh)['spots']
    sources.append((path, len(recs)))
    for rec in recs:
        if not valid(rec):
            invalid += 1
            continue
        if key(rec) in merged:
            replaced += 1
        merged[key(rec)] = rec

spots = sorted(merged.values(), key=lambda r: (r[1], r[4], r[13] or ''))
out = {k: v for k, v in old.items() if k != 'spots'}
out['spots'] = spots
with open(out_js, 'w', encoding='utf-8') as fh:
    fh.write(HEAD + json.dumps(out, separators=(',', ':')) + ';\n')
print('sources', sources, '->', len(spots), f'records ({invalid} invalid, {replaced} replaced)')
by = collections.defaultdict(collections.Counter)
for r in spots:
    by[r[1]][r[0]] += 1
for tag, c in by.items():
    print(tag, sum(c.values()), 'depths', sorted({r[4] for r in spots if r[1] == tag}))
    print('  ', dict(c))
