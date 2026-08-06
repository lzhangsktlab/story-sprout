# Content-constraint audit

Does the one-line constraint the platform appends to every image request (§3.2
of the paper) keep the scary, sad, and mildly gross content children legitimately
author, while blocking what violates the content line? Two measured rounds, run
2026-08-04 and 2026-08-05. **Start with `FINDINGS.md`.**

No children were involved. Eighty scripted descriptions, written in child voice,
went straight to the deployed image model through the same API the studio uses.

## Headline (pooled, 480 trials, $15.11)

| | |
|---|---|
| Keep rate | 221/240 = **92.1%** (95% CI 88.0–94.9), zero silent softening |
| Block rate | 124/150 = **82.7%** (95% CI 75.8–87.9) |
| Provider refusals of legitimate child content | **15.0% bare → 0.8%** with the constraint |
| Provider refusals of violating content (like-for-like) | **69.4% bare → 44.4%** with the constraint |

The last two lines are the result with implications beyond this system: the
constraint suppresses the provider's own moderation in *both* directions. It
rescues ordinary childhood content the provider would refuse, and it carries
violating content past the same filter. A constraint that vouches cannot avoid
also laundering, so it must itself name every category it relies on.

## Files

| Path | What |
|---|---|
| `FINDINGS.md` | **The briefing.** Method, every number, interpretations kept separate from facts. Round 2 section supersedes two round-1 claims — read to the end. |
| `PROTOCOL.md` | Pre-registered design, frozen-constraint rule, invalidation conditions |
| `PAPER_EDITS.md` | Drop-in text for the paper: §3.2 fix, §3.3 clause, §4.2 with results |
| `FROZEN.json` | The exact audited constraint string + sha256 |
| `stimuli/*.jsonl` | The three fixed stimulus sets, 80 descriptions |
| `run_audit.py` | The runner (checkpointed, resumable, spend-capped) |
| `summarize.py` | Per-round rates with Wilson intervals |
| `compare_rounds.py` | Round-over-round diff + the bare-vs-constrained analysis |
| `out/`, `out_r2/` | Round 1 and round 2 journals, contact sheets, per-image judgments, cited evidence images |

Bulk images are gitignored (`out*/*/images/`, ~1.3 GB across both rounds).
Contact sheets, journals, and individually cited evidence images are committed.

## Reproducing

Needs `OPENAI_API_KEY` and `OPENAI_API_KEY_AUDIT` in the repo `.env`. **Two keys
on purpose:** the BLOCK set fires violating prompts at the safety stack, and that
traffic must not ride the account that serves children. Without the audit key,
BLOCK trials are skipped rather than silently sent on the production key.

```bash
AUDIT_OUT=out_r3 python3 run_audit.py smoke     # 6 trials, validates everything
AUDIT_OUT=out_r3 python3 run_audit.py heldout   # 240 trials, ~2h
AUDIT_OUT=out_r3 python3 run_audit.py bare      # 240 trials, attribution arm
AUDIT_OUT=out_r3 python3 run_audit.py status    # progress + spend
python3 summarize.py out_r3
```

Every invocation auto-resumes from its journal: finished trials are never
re-run, errored ones are retried, and running a completed phase is a no-op. Both
rounds were interrupted repeatedly and lost nothing. The runner extracts the
constraint and the word filter from `cloudflare-worker/pip-worker.js` at startup
and records their sha256 on every trial, so a mid-run edit to the Worker shows up
as a mismatch rather than as quiet contamination.

Generated images cannot be scored from API responses — an image model can accept
a request and quietly deliver a softened scene. Every generated image was
inspected by eye; judgments are in `out*/heldout/human_pass.jsonl`, one rater,
released for re-adjudication.

## Known gaps

Renderer-only: Pip is not in the loop, so the BLOCK failures overstate real
exposure (Pip's contract declines violent requests conversationally) by an
unmeasured amount. This is the largest limitation and the first thing a round 3
should fix. One rater. Researcher-written stimuli. The provider's layers are
stochastic and can change without notice.
