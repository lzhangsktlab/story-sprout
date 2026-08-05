#!/usr/bin/env python3
"""Compare two measured rounds of the same frozen constraint.

Round 1 (out/) and round 2 (out_r2/) ran the identical stimulus sets against the
identical constraint string. Differences between them are the provider's own
stochasticity, not our doing — which is itself a result worth reporting, since a
single-round number would read as more precise than the system actually is.

Usage: python3 compare_rounds.py [round1_dir] [round2_dir]
"""
import json
import math
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
REFUSED = ('refused_ours', 'refused_provider_prompt',
           'refused_provider_output', 'refused_provider_unattributed')


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)


def load(path):
    byk = {}
    p = pathlib.Path(path)
    if not p.exists():
        return byk
    for line in p.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            byk[r['key']] = r
    return byk


def human(path):
    out = {}
    p = pathlib.Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                out[j['key']] = j
    return out


def per_item(rows, bin_name):
    """item -> Counter(outcome) for one bin."""
    d = {}
    for r in rows.values():
        if r['bin'] != bin_name:
            continue
        d.setdefault(r['item'], Counter())[r['outcome']] += 1
    return d


def summarize_round(label, root):
    held = load(f'{root}/heldout/journal.jsonl')
    bare = load(f'{root}/bare/journal.jsonl')
    hp = human(f'{root}/heldout/human_pass.jsonl')
    if not held:
        return None

    keep = [r for r in held.values() if r['bin'] == 'KEEP']
    block = [r for r in held.values() if r['bin'] == 'BLOCK']

    kept = [r for r in keep if r['outcome'] == 'generated'
            and hp.get(r['key'], {}).get('element_present')]
    k_ref = [r for r in keep if r['outcome'] in REFUSED]
    b_ref = [r for r in block if r['outcome'] in REFUSED]
    b_steer = [r for r in block if r['outcome'] == 'generated'
               and not hp.get(r['key'], {}).get('violating_present', True)]
    b_fail = [r for r in block if r['outcome'] == 'generated'
              and hp.get(r['key'], {}).get('violating_present')]

    return {
        'label': label, 'root': root, 'held': held, 'bare': bare, 'hp': hp,
        'n_keep': len(keep), 'kept': len(kept), 'k_ref': len(k_ref),
        'k_ref_items': sorted({r['item'] for r in k_ref}),
        'n_block': len(block), 'b_safe': len(b_ref) + len(b_steer),
        'b_layers': Counter(r['outcome'] for r in b_ref),
        'b_fail_items': Counter(r['item'] for r in b_fail),
        'n_fail': len(b_fail),
        'cost': sum(r.get('cost_usd', 0) for r in held.values())
                + sum(r.get('cost_usd', 0) for r in bare.values()),
    }


def main():
    r1_root = sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'out')
    r2_root = sys.argv[2] if len(sys.argv) > 2 else str(HERE / 'out_r2')
    rounds = [s for s in (summarize_round('round 1', r1_root),
                          summarize_round('round 2', r2_root)) if s]

    print('=' * 74)
    print('HEADLINE RATES')
    print('=' * 74)
    for s in rounds:
        klo, khi = wilson(s['kept'], s['n_keep'])
        blo, bhi = wilson(s['b_safe'], s['n_block'])
        print(f"{s['label']}: keep {s['kept']}/{s['n_keep']} = {s['kept']/s['n_keep']:.1%} "
              f"(CI {klo:.1%}-{khi:.1%})   "
              f"block {s['b_safe']}/{s['n_block']} = {s['b_safe']/s['n_block']:.1%} "
              f"(CI {blo:.1%}-{bhi:.1%})   ${s['cost']:.2f}")

    if len(rounds) == 2:
        a, b = rounds
        # Pooled, since both rounds are the same constraint and same stimuli.
        pk, pkn = a['kept'] + b['kept'], a['n_keep'] + b['n_keep']
        pb, pbn = a['b_safe'] + b['b_safe'], a['n_block'] + b['n_block']
        klo, khi = wilson(pk, pkn)
        blo, bhi = wilson(pb, pbn)
        print(f"\nPOOLED: keep {pk}/{pkn} = {pk/pkn:.1%} (CI {klo:.1%}-{khi:.1%})   "
              f"block {pb}/{pbn} = {pb/pbn:.1%} (CI {blo:.1%}-{bhi:.1%})")

        print('\n' + '=' * 74)
        print('PER-ITEM STABILITY  (items whose outcome pattern moved between rounds)')
        print('=' * 74)
        for bin_name in ('KEEP', 'BLOCK', 'EDGE'):
            ai, bi = per_item(a['held'], bin_name), per_item(b['held'], bin_name)
            moved = []
            for item in sorted(set(ai) | set(bi)):
                if dict(ai.get(item, {})) != dict(bi.get(item, {})):
                    moved.append(item)
            print(f'\n{bin_name}: {len(moved)} of {len(set(ai) | set(bi))} items moved')
            for item in moved:
                txt = next((r['text'] for r in a['held'].values() if r['item'] == item), '')
                print(f'  {item}  r1={dict(ai.get(item, {}))}  r2={dict(bi.get(item, {}))}')
                print(f'        "{txt[:60]}"')

        print('\n' + '=' * 74)
        print('LAYER ATTRIBUTION (BLOCK refusals)')
        print('=' * 74)
        for s in rounds:
            print(f"  {s['label']}: {dict(s['b_layers'])}, failures {dict(s['b_fail_items'])}")

        print('\n' + '=' * 74)
        print('KEEP REFUSALS (should be the blood items only)')
        print('=' * 74)
        for s in rounds:
            print(f"  {s['label']}: {s['k_ref']} trials, items {s['k_ref_items']}")

    # ── bare-vs-constrained flips, per round ────────────────────────────────
    for s in rounds:
        if not s['bare']:
            continue
        print('\n' + '=' * 74)
        print(f"BARE vs CONSTRAINED — {s['label']}")
        print('=' * 74)
        bare_item = {}
        for r in s['bare'].values():
            bare_item.setdefault(r['item'], Counter())[r['outcome']] += 1
        held_item = {}
        for r in s['held'].values():
            held_item.setdefault(r['item'], Counter())[r['outcome']] += 1

        rescued, laundered, ours_only = [], [], []
        for item, bc in sorted(bare_item.items()):
            hc = held_item.get(item, Counter())
            bin_name = next(r['bin'] for r in s['bare'].values() if r['item'] == item)
            bare_gen = bc.get('generated', 0)
            bare_ref = sum(v for k, v in bc.items() if k in REFUSED)
            held_gen = hc.get('generated', 0)
            txt = next(r['text'] for r in s['bare'].values() if r['item'] == item)
            # KEEP refused bare (by provider) but generated with the constraint
            if bin_name == 'KEEP' and bare_ref and held_gen:
                rescued.append((item, dict(bc), dict(hc), txt))
            # BLOCK refused bare (by provider) but generated with the constraint
            if bin_name == 'BLOCK' and bare_ref and held_gen:
                laundered.append((item, dict(bc), dict(hc), txt))
            # BLOCK the provider drew but our filter stops
            if bin_name == 'BLOCK' and bare_gen and hc.get('refused_ours'):
                ours_only.append((item, txt))

        print(f'\n  RESCUED — provider refuses bare, constraint lets it through ({len(rescued)} items):')
        for item, bc, hc, txt in rescued:
            print(f'    {item} bare={bc} constrained={hc}  "{txt[:52]}"')
        print(f'\n  LAUNDERED — provider refuses bare, constraint carries it past ({len(laundered)} items):')
        for item, bc, hc, txt in laundered:
            print(f'    {item} bare={bc} constrained={hc}  "{txt[:52]}"')
        print(f'\n  OUR-FILTER-ONLY — provider draws it, our word filter stops it ({len(ours_only)} items):')
        for item, txt in ours_only:
            print(f'    {item}  "{txt[:60]}"')


if __name__ == '__main__':
    main()
