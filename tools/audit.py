"""Audit both datasets for holes: spots present in sibling setups but missing here, and coverage gaps."""
import collections
import json

WD = str(__import__('pathlib').Path(__file__).resolve().parent.parent) + '/'


def load(name, var):
    t = open(WD + name, encoding='utf-8').read().strip()
    return json.loads(t[len('window.' + var + '='):].rstrip(';'))['spots']


# ---------------- cash ----------------
cash = load('cash-data.js', 'CASH_DATA')
by_cfg = collections.defaultdict(set)
for r in cash:
    fam, tag, gt, n, dp, hero, vs, caller = r[:8]
    by_cfg[(tag, r[14], dp)].add((fam, hero, vs, caller))
print('CASH: setups', len(by_cfg))
union = collections.defaultdict(set)
for (tag, op, dp), sits in by_cfg.items():
    union[tag] |= sits
holes = []
for (tag, op, dp), sits in sorted(by_cfg.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
    missing = union[tag] - sits
    if missing:
        holes.append((tag, op, dp, len(missing), sorted(missing)[:6]))
fam_union = collections.Counter(f for t in union for (f, *_r) in union[t])
print('  sit types per game:', {t: collections.Counter(s[0] for s in union[t]) for t in union})
print('  setups with sits missing vs. the game union:', len(holes))
for h in holes[:40]:
    print('   ', h[0], h[1], h[2], 'missing', h[3], h[4])

# ---------------- tournament ----------------
mtt = load('data.js', 'RANGE_DATA')
sits = collections.defaultdict(set)
for r in mtt:
    fam, tag, gt, n, dp, hero, vs, caller = r[:8]
    sits[(tag, gt, fam, hero, vs, caller)].add(dp)
print('\nTOURNAMENT: spots', len(mtt), 'situations', len(sits))
fams = collections.defaultdict(lambda: collections.defaultdict(list))
for (tag, gt, fam, hero, vs, caller), dps in sits.items():
    fams[(tag, fam)][tuple(sorted(dps))].append((hero, vs, caller))
for (tag, fam), groups in sorted(fams.items()):
    print(f'  {tag} {fam}: {sum(len(v) for v in groups.values())} situations')
    for dps, members in sorted(groups.items(), key=lambda x: -len(x[1]))[:3]:
        print(f'      {len(members)} sits at {len(dps)} depths: {list(dps)}')
