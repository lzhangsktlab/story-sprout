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

## Results as they fell (auto-scored; flagged lines provisional, see run_config.json)

| rep | verbatim | unrequested addition | omission | interaction rules |
|---|---|---|---|---|
| 1 | 240/240 | 0/240 | 6/240 | 28/28 |
| 2 | 240/240 | 0/240 | 7/240 | 28/28 |
| 3 | 240/240 | 0/240 | 6/240 | 28/28 |

Model `gpt-5.4-mini`, `reasoning_effort: low`, contract sha `d01f624b…` (freeze-matched
to the v2 selection run). 906 exchanges, all `finish_reason: stop`, zero parse failures,
zero unprompted-style flags, zero transport retries.

The 19 omission flags across the three reps are analysed in `run_config.json`
(`adjudication_notes`): all but four are scorer artifacts on the replacement subset
(a superseded "paper lanterns" orphaning "paper"/"lit") or tokenization ("shark" vs
"shark's"); the four genuine ones are a minor, rep-inconsistent wobble on a single
replacement sequence (H56). No rep dropped a still-current child detail outside the
replacement subset, corrected any seeded typo, or added an unrequested one.

Nothing in this directory is hand-edited. Adjudication of flagged lines is on the paper side.
