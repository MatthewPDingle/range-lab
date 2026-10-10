"""Merge tournament fill crawls into data.js (new records win), validating every record."""
import collections
import json
import sys

old_js, out_js, *new_jsons = sys.argv[1:]
B64 = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')

with open(old_js, encoding='utf-8') as fh:
    text = fh.read().strip()
old = json.loads(text[len('window.RANGE_DATA='):].rstrip(';'))


def valid(rec):
    try:
        fam, tag, gt, n, dp, hero, vs, caller, pos, acts, f, l, r, hist = rec
        return (tag in ('cev9', 'icm8') and n in (8, 9) and len(acts) == len(f) == len(l) >= 1
                and all(len(a) == 5 for a in acts)
                and all(len(x) == 169 and set(x) <= B64 for x in f + l) and (r == '' or (len(r) == 169 and set(r) <= B64)))
    except Exception:
        return False


sources = [('old', old['spots'])]
for p in new_jsons:
    with open(p, encoding='utf-8') as fh:
        sources.append((p, [r for r in json.load(fh)['spots'] if len(r) == 14]))
merged, bad, replaced = {}, 0, 0
for name, recs in sources:
    for rec in recs:
        if not valid(rec):
            bad += 1
            continue
        k = (rec[2], rec[4], rec[13], rec[0], rec[5], rec[6], rec[7])
        replaced += k in merged
        merged[k] = rec

FAM_ORDER = ['RFI', 'BBvsLimp', 'BBvsOpen', 'vsOpen', 'Squeeze', 'BBvsJam', 'vsJam', 'OpenVsJam', 'OpenVs3bet']
spots = sorted(merged.values(), key=lambda r: (r[1], r[2], r[4], FAM_ORDER.index(r[0]) if r[0] in FAM_ORDER else 99, r[5], r[6], r[7]))
out = dict(old)
out['spots'] = spots
out['built'] = __import__('datetime').date.today().isoformat()
with open(out_js, 'w', encoding='utf-8') as fh:
    fh.write('window.RANGE_DATA=' + json.dumps(out, separators=(',', ':')) + ';\n')
print(f"sources {[ (n, len(r)) for n, r in sources]} -> {len(spots)} records ({bad} invalid, {replaced} replaced)")
print('keys in old meta:', [k for k in old if k != 'spots'])
for tag in ('cev9', 'icm8'):
    sub = [r for r in spots if r[1] == tag]
    print(tag, len(sub), 'depths', sorted({r[4] for r in sub}))
    c = collections.Counter(r[0] for r in sub)
    print('  ', dict(c))
