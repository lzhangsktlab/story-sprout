# Model-selection tests (archive)

These are the exploratory runs that led to the choice of chat model and reasoning
effort for Pip. They are **development / selection** artifacts, kept for the record.
The **verification** numbers reported in the paper come from the held-out suite in
`../scribe_audit_v3_heldout_out/`, whose cases share nothing with these runs.

Every run here was executed **locally, direct to OpenAI**, with the worker's exact
request parameters (the Cloudflare relay itself was not in the path — see each
`run_config.json`). All runs used the same frozen contract, `PIP_SYSTEM` sha256
`d01f624ba41465a60ea04f133e982f77fb13bd02e6a76ee16dc2ed9030667154`, extracted
programmatically from `cloudflare-worker/pip-worker.js`.

Each folder holds the harness's own outputs — `summary.txt`, `audit_log.jsonl`,
`transcripts.json` — plus `raw_exchanges.jsonl` (full request params + raw model
output per turn; no `Authorization` header, no keys). Numbers below are the
auto-scored screen; flagged lines are for hand adjudication, not final verdicts.

## Suites

- **`scribe_audit.py`** — v1 exploratory. 22 two-turn scribe sequences (44 draw
  turns) + a small rules set. Used to compare models and effort levels quickly.
- **`scribe_audit_ext.py`** — v1 extended to 100 sequences (200 draw turns); S23–S100
  authored by Claude to raise n (noted in that run's `run_config.json`).
- **`scribe_audit_v2.py`** — the development suite proper: 50 **four-turn** additive
  sequences (accumulation stress + a replacement subset) + 28 rule cases, run on
  both the selected model and its predecessor.

## Runs

| Folder | Suite | Model | reasoning_effort | verbatim | rules |
|---|---|---|---|---|---|
| `scribe_audit_out_gpt-4o-mini` | v1 | gpt-4o-mini | n/a | 0/39 | 55/57 |
| `scribe_audit_out_gpt-5.6-luna` | v1 | gpt-5.6-luna | low | 44/44 | 62/62 |
| `scribe_audit_out_luna-effort-none` | v1 | gpt-5.6-luna | none | 42/44 | 62/62 |
| `scribe_audit_out_luna-effort-low` | v1 | gpt-5.6-luna | low | 44/44 | 62/62 |
| `scribe_audit_out_gpt-5.4-mini` | v1 | gpt-5.4-mini | low | 44/44 | 62/62 |
| `scribe_audit_out_gpt-5.4-mini-n200` | v1-ext | gpt-5.4-mini | low | 200/200 | 218/218 |
| `scribe_audit_v2_out_gpt-4o-mini` | v2 | gpt-4o-mini | n/a | 65/183 | 26/28 |
| `scribe_audit_v2_out_gpt-5.4-mini` | v2 | gpt-5.4-mini | low | 200/200 | 25/28 |

`v2_run_config.json` is the shared config for the two `scribe_audit_v2_out_*` runs.

## What the selection concluded

- **gpt-4o-mini silently corrects children's spelling** — 0/39 verbatim in v1, and on
  the harder four-turn v2 suite it corrected *every* typo it saw (0/118 on turns that
  actually carried one). Carrying the child's exact words is the point of the scribe
  rule, so it was ruled out.
- Among gpt-5.x models, **effort `low` is the floor that keeps verbatim at full marks**;
  `none` dropped two spellings (42/44) for no real latency gain (~2 s across 84 turns).
- **gpt-5.4-mini at `low`** matched the larger gpt-5.6-luna on fidelity, added no
  unrequested words, and is cheaper — so it is the selected configuration.

Both gpt-5.x models reject the worker's original `temperature: 0.5` and `max_tokens`
(reasoning models); those two params are dropped, as each run's `run_config.json`
records. Reported verbatim denominators include free passes from typo-free sequences;
see the per-run configs and the v3 verification suite for the adjudicated view.
