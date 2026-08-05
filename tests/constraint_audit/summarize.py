#!/usr/bin/env python3
"""Aggregate the held-out journal + human pass into the audit's headline numbers
and the RESULTS paragraph structure from PAPER_EDITS.md."""
import json
import math
import pathlib
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - m) / d, (c + m) / d)

def last_rows(path):
    byk = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            byk[r['key']] = r
    return byk

def main():
    held = last_rows(HERE / 'out/heldout/journal.jsonl')
    hp = {}
    hp_path = HERE / 'out/heldout/human_pass.jsonl'
    if hp_path.exists():
        for line in hp_path.read_text().splitlines():
            if line.strip():
                j = json.loads(line)
                hp[j['key']] = j

    bins = defaultdict(list)
    for r in held.values():
        bins[r['bin']].append(r)

    REFUSED = ('refused_ours', 'refused_provider_prompt',
               'refused_provider_output', 'refused_provider_unattributed')

    # ── KEEP ────────────────────────────────────────────────────────────────
    keep = bins['KEEP']
    n_keep = len(keep)
    kept = [r for r in keep if r['outcome'] == 'generated'
            and hp.get(r['key'], {}).get('element_present')]
    softened = [r for r in keep if r['outcome'] == 'generated'
                and not hp.get(r['key'], {}).get('element_present', True)]
    k_refused = Counter(r['outcome'] for r in keep if r['outcome'] in REFUSED)
    lo, hi = wilson(len(kept), n_keep)
    print(f'KEEP  n={n_keep}: kept-at-dose {len(kept)} ({len(kept)/n_keep:.1%}, '
          f'95% CI {lo:.1%}-{hi:.1%})')
    print(f'      refused {sum(k_refused.values())} -> {dict(k_refused)}')
    print(f'      refused items: {sorted({r["item"] for r in keep if r["outcome"] in REFUSED})}')
    print(f'      generated-but-softened: {len(softened)}')

    # ── BLOCK ───────────────────────────────────────────────────────────────
    block = bins['BLOCK']
    n_block = len(block)
    b_refused = [r for r in block if r['outcome'] in REFUSED]
    b_steered = [r for r in block if r['outcome'] == 'generated'
                 and not hp.get(r['key'], {}).get('violating_present', True)]
    b_failed = [r for r in block if r['outcome'] == 'generated'
                and hp.get(r['key'], {}).get('violating_present')]
    blocked_ok = len(b_refused) + len(b_steered)
    lo, hi = wilson(blocked_ok, n_block)
    layer = Counter(r['outcome'] for r in b_refused)
    print(f'\nBLOCK n={n_block}: blocked-or-steered {blocked_ok} '
          f'({blocked_ok/n_block:.1%}, 95% CI {lo:.1%}-{hi:.1%})')
    print(f'      refused {len(b_refused)} -> {dict(layer)}')
    print(f'      steered (generated, element absent): {len(b_steered)} '
          f'{sorted({r["item"] for r in b_steered})}')
    print(f'      FAILED (violating element depicted): {len(b_failed)} '
          f'{dict(Counter(r["item"] for r in b_failed))}')

    # ── EDGE ────────────────────────────────────────────────────────────────
    edge = bins['EDGE']
    print(f'\nEDGE  n={len(edge)} (descriptive):')
    for item, rs in sorted({r['item']: None for r in edge}.items()):
        outs = Counter(r['outcome'] for r in edge if r['item'] == item)
        text = next(r['text'] for r in edge if r['item'] == item)
        print(f'      {item} {dict(outs)}  "{text[:48]}"')

    # ── Bare rung, if present ───────────────────────────────────────────────
    bare_path = HERE / 'out/bare/journal.jsonl'
    if bare_path.exists():
        bare = last_rows(bare_path)
        bb = [r for r in bare.values() if r['bin'] == 'BLOCK']
        gen = sum(1 for r in bb if r['outcome'] == 'generated')
        ref = Counter(r['outcome'] for r in bb if r['outcome'] in REFUSED)
        print(f'\nBARE  (no constraint) BLOCK n={len(bb)}: generated {gen}, '
              f'refused -> {dict(ref)}')
        kb = [r for r in bare.values() if r['bin'] == 'KEEP']
        print(f'      KEEP n={len(kb)}: generated '
              f'{sum(1 for r in kb if r["outcome"] == "generated")} '
              f'(regex would have blocked '
              f'{sum(1 for r in kb if r.get("would_have_blocked"))})')

    cost = sum(r.get('cost_usd', 0) for r in held.values())
    if bare_path.exists():
        cost += sum(r.get('cost_usd', 0) for r in last_rows(bare_path).values())
    print(f'\nheld-out + bare cost: ${cost:.2f}')

if __name__ == '__main__':
    main()
