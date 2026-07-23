# Held-out verification — protocol

Verbatim answers to the six protocol questions in
`CLAUDE_CODE_AUDIT_V3_HELDOUT_INSTRUCTIONS.md`.

1. **Suite roles.** The 200-turn v2 suite (`../model_selection_tests/scribe_audit_v2_out_*`)
   was used for contract development and model selection; this v3 suite was authored
   after selection and supplies the verification numbers. No case in v3 appears in v2.

2. **Case modification.** v3 cases were not modified after any run; authored blind to
   v3 results by construction.

3. **Runs.** Three independent stochastic repetitions; all reported.

4. **Judging.** A deterministic scorer flags candidate deviations; flagged lines are
   adjudicated by the authors, with every per-case judgment released for independent
   re-adjudication. Evaluators are not independent of the authors; this is disclosed.

5. **"Composition turn".** One child turn inside a four-turn additive sequence whose
   response carried `ready=true`; denominators count these.

6. **Case-type distribution** matches the development suite (including the replacement
   subset) to estimate the same construct.

---

## Results — three scorings of the same stored transcripts (no new elicitation)

The same 906 exchanges (model `gpt-5.4-mini`, `reasoning_effort: low`, contract sha
`d01f624b…` freeze-matched to the v2 selection run; all `finish_reason: stop`, zero
parse failures, zero transport retries) were scored three times as the ruler was
corrected. Elicitation never changed — only the scorer. See `run_config.json`
`scorer_errata` (four fixes) and `scorings_released`.

**Original scorer** — `runN/summary.txt`:

| rep | verbatim | addition | omission | rules |
|---|---|---|---|---|
| 1 | 240/240 | 0/240 | 6/240 | 28/28 |
| 2 | 240/240 | 0/240 | 7/240 | 28/28 |
| 3 | 240/240 | 0/240 | 6/240 | 28/28 |

**Pass 1** (patches 1–2: H60 superseded set, possessive normalization) —
`runN/summary_rescored_pass1.txt`. Cleared H60 (9) and H15's `shark` (1); surfaced a
false positive — the child's word "storybook's" tripping the style flag on H17 — which
motivated patches 3–4.

**Final, FROZEN for the paper** (all four patches) — `runN/summary_rescored.txt`,
reproduced by `python3 scribe_audit_v3_heldout.py --rescore`:

| rep | verbatim | addition | omission | rules | style |
|---|---|---|---|---|---|
| 1 | 240/240 | 0/240 | 2/240 | 28/28 | 0 |
| 2 | 240/240 | 0/240 | 2/240 | 28/28 | 0 |
| 3 | 240/240 | 0/240 | 3/240 | 28/28 | 0 |
| **Σ** | **240/240 ×3** | **0/720** | **7/720** | **84/84** | **0** |

**The 7 remaining omissions are all one sequence, H56**, disclosed and genuine: on
"make the treehouse small and cozy **instead**" the model sometimes also shed
"oak"/"rope swing" though only "big" was superseded — a minor, rep-inconsistent
composition wobble on the known-hard replacement subset. Across all three reps and 720
composition turns, no seeded typo was corrected, no unrequested word was added, no
still-current child detail outside H56 was dropped, and no unprompted style word
appeared.

Tripwire on the final re-score (`run_config.json` `rescore_tripwire`): versus the
original, only omission flags changed; verbatim, additions, expected-draw, and every
rule flag are byte-identical. Nothing in this directory is hand-edited; adjudication of
flagged lines is on the paper side.
