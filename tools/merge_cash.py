"""Merge the full cash crawl into cash-data.js (new records win), validating every record."""
import collections
import json
import sys

old_js, new_json, out_js = sys.argv[1], sys.argv[2], sys.argv[3]
B64 = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')

with open(old_js, encoding='utf-8') as fh:
    text = fh.read().strip()
old = json.loads(text[len('window.CASH_DATA='):].rstrip(';'))
with open(new_json, encoding='utf-8') as fh:
    new = json.load(fh)


def valid(rec):
    try:
        fam, tag, gt, n, dp, hero, vs, caller, pos, acts, f, l, r, hist, open_ = rec
        return (tag in ('reg', 'str') and n == 8 and isinstance(open_, str) and len(acts) == len(f) == len(l) >= 1
                and all(len(x) == 169 and set(x) <= B64 for x in f + l) and (r == '' or (len(r) == 169 and set(r) <= B64)))
    except Exception:
        return False


merged, bad = {}, 0
for source in (old['spots'], new['spots']):
    for rec in source:
        if not valid(rec):
            bad += 1
            continue
        merged[(rec[2], rec[4], rec[13], rec[0], rec[5], rec[6], rec[7])] = rec

spots = sorted(merged.values(), key=lambda r: (r[1], r[14], r[4], r[0], r[5], r[6], r[7]))
with open(out_js, 'w', encoding='utf-8') as fh:
    fh.write('window.CASH_DATA=' + json.dumps({'v': 1, 'built': new.get('built'), 'source': 'GTO Wizard', 'spots': spots}, separators=(',', ':')) + ';\n')

print(f"old {len(old['spots'])} + new {len(new['spots'])} -> {len(spots)} records ({bad} invalid skipped)")
grid = collections.defaultdict(set)
for r in spots:
    grid[(r[1], r[14])].add(r[4])
for (tag, op), dps in sorted(grid.items(), key=lambda x: (x[0][0], float(x[0][1].rstrip('xb')))):
    cnt = sum(1 for r in spots if r[1] == tag and r[14] == op)
    print(f"  {tag} {op:>5}: {cnt:5} spots at {sorted(dps)}")
