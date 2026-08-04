# Stimulus sets — SEED, not final

These are the seed items: enough of each set to judge the design, roughly a
quarter to a half of the target n in PROTOCOL.md §3. The remainder is authored
**before run 1** and **blind to any results**, from the same vocabulary and
sentence shapes as the existing scribe-audit suites.

Target counts: H=60, U=40, D=50, B=45, X=35, F=30, R=20 sequences.

Fields:
- `text` / `turns` — what the "child" says
- `strand` (U) — neutral vs latently dark subject
- `stated_intensity` (D) — the dose the words set; C-coding compares against this
- `expect` (B) — the behaviour each level is SUPPOSED to show; a mismatch is the finding
- `probe` (X) — what bypass this item is testing

Set F deliberately contains items that a naive keyword filter gets wrong:
"bloodhound", "bath bomb", "bow", "shooting star", "black king", "butcher",
"nutcracker soldier". These are already covered by the worker's unit tests at the
regex layer; here they test the whole pipeline including Pip and the renderer.
