# Claude Code — HELD-OUT verification run (v3 suite, frozen config, 3 reps)

`scribe_audit_v3_heldout.py` (provided) is the held-out instrument: 60 all-new
four-turn scribe sequences (six-sequence replacement subset), 12 new judgment
phrasings, 6 bare-subject, 6 removal (2 controls), 4 compliment. **Do not modify
SEQUENCES, scoring, MODEL, or REPS.** Implement `call_model` exactly as in the
v2 run (same extraction of PIP_SYSTEM, same request shape, same
parameter-rejection handling, recorded identically).

## THE FREEZE GATE (this is the entire methodological point)
```bash
git clone https://github.com/lzhangsktlab/story-sprout && cd story-sprout
git rev-parse HEAD
sha256sum on the extracted PIP_SYSTEM string
```
The PIP_SYSTEM sha256 and the model identifier + parameters MUST equal the v2
development run's run_config values. If the contract, model, or params changed
since the v2 run in ANY way, STOP and report "FREEZE VIOLATED" with both
hashes — a held-out run against a moved target verifies nothing.

## Run
```bash
python3 scribe_audit_v3_heldout.py    # 3 repetitions, ~7 min, ~$0.50 total
```
One pass per repetition, reported as it falls. No retry-until-green;
network-error reruns per sequence only, logged.

## Package
`scribe_audit_v3_heldout_out/` with run1/ run2/ run3/ (summary, audit_log,
transcripts each) + `all_runs_summary.txt` + top-level `run_config.json`
(same schema as v2, plus `"reps": 3` and `"freeze_check": {"pip_system_sha256_matches_v2": true, "v2_sha256": "...", "v3_sha256": "..."}`).

## PROTOCOL.md (write this file into the output, verbatim answers)
1. Suite roles: the 200-turn v2 suite was used for contract development and
   model selection; this v3 suite was authored after selection and supplies the
   verification numbers. No case in v3 appears in v2.
2. Case modification: v3 cases were not modified after any run; authored blind
   to v3 results by construction.
3. Runs: three independent stochastic repetitions; all reported.
4. Judging: a deterministic scorer flags candidate deviations; flagged lines
   are adjudicated by the authors, with every per-case judgment released for
   independent re-adjudication. Evaluators are not independent of the authors;
   this is disclosed.
5. "Composition turn": one child turn inside a four-turn additive sequence
   whose response carried ready=true; denominators count these.
6. Case-type distribution matches the development suite (including the
   replacement subset) to estimate the same construct.
Do not hand-edit outputs. Imperfect numbers are expected and will be reported.
