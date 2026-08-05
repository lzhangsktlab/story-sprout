# Paper edits for the content-constraint audit

Drop-in text for `story_sprout_v50_candidate`. Placeholders in [brackets] are
filled after the held-out run. The constraint placeholder is filled with the
frozen string from `PROTOCOL.md` §2, which must be byte-identical to what the
audit ran and what the Worker ships.

---

## Edit 1 — §3.2, the composed-prompt example

The current example prints the old suffix, which bans "scary or frightening
imagery" outright. That wording is not what is deployed, and it contradicts the
claim §4.2 makes. Replace the example's final paragraph with:

> Drawing request after the second turn: *a sleepy koala libarian stamping tiny
> books at a desk, add a lamp with a green shade on the desk* [FINAL CONSTRAINT
> — the exact one-line string, frozen and hash-recorded before the §4.2 audit;
> printed here in full, in italics]

Where §3.2 introduces the constraint, add:

> The constraint is written for the 7–9 band: it must block descriptions that
> violate the content line while leaving the scary creatures, mild peril, and
> body humor of ordinary children's stories drawable. §4.2 reports the audit of
> both directions.

## Edit 2 — §3.3, the safety-layers paragraph

In the sentence "Every drawing request also carries a one-line constraint,
shown in place (§3.2)", append:

> …shown in place (§3.2) and audited in §4.2. The provider runs its own
> moderation: classifiers check the prompt before generation, and a safety
> model checks the finished image [OpenAI, 2026]. Those checks enforce the
> provider's universal policies. The platform's constraint is the layer written
> for the age band.

## Edit 3 — retitle §4 and add §4.2

Retitle current §4 from "Auditing the scribe contract" to **"4 Audits"**, make
the existing body **"4.1 The scribe contract"** (text unchanged), and add:

---

### 4.2 The content constraint

The one-line constraint (§3.2) makes two promises. Descriptions that violate
the platform's content line must not be drawn. Descriptions within a
7–9-year-old's ordinary range must be drawn as asked. The second promise is
easy to lose. Children's own stories are dominated by monsters, villains, and
battles between good and evil [Sutton-Smith, 1981], and research on fright
reactions ties lasting harm to graphic gore, realistic injury, and intensity
beyond the child's stage, not to dark themes or sadness [Harrison & Cantor,
1999]. A constraint that removes all of it also removes the mismatch the child
was supposed to debug (§2).

We tested the constraint the way §4.1 tests the scribe contract: scripted
requests, the real deployed models, no children. Two stimulus sets were written
in advance and fixed. A keep set holds 40 descriptions within the ordinary
range: storybook-scary creatures, stated mild intensity ("a little bit scary"),
body content at a story's dose (a scraped knee, a bloody nose), sad scenes, and
adventure themes. A block set holds 25 descriptions that violate the line:
firearms, graphic gore, realistic horror, adult content, cruelty. A 15-item
edge set sits between the two and is reported item by item, not as a rate. Each
description ran three times with the constraint appended and once without it.
The run without the constraint attributes each refusal to a layer: the
platform's word filter, the provider's check of the prompt, or the provider's
check of the finished image; the three are separable in the logs [OpenAI,
2026]. Blocking is read from the API outcome. Keeping is not: an image model
can accept a request and deliver a softened scene, and the provider documents
this as designed behavior [OpenAI, 2026]. Every generated keep-set image was
therefore inspected by a human for whether the asked-for element appears.

[RESULTS — filled after the held-out run. Structure: Of 120 keep requests, [k]
generated; inspection confirmed the asked-for element in [k′]; [f] were
refused, [layer breakdown]. Keep rate [x%]. Of 75 block requests, [b] were
refused — [b1] at the platform's filter, [b2] at the provider's prompt check,
[b3] at the provider's image check; [g] generated, [g′] of which depicted the
violating element. Block rate [y%]. One sentence on the edge set. One sentence
stating what the numbers support.]

The audit measures the system, not children. It does not test how a child
experiences a refusal, and it does not decide whether the calibration suits a
particular class; that stays with the supervising adult and the planned study
(§6). The stimulus sets, the frozen constraint and its hash, the outcomes, the
images, and the per-image judgments are released with the code (§1).

---

## References to add

> Harrison, K., & Cantor, J. (1999). Tales from the screen: Enduring fright
> reactions to scary media. *Media Psychology*, 1(2), 97–116.
>
> OpenAI. (2026). *System card: ChatGPT Images 2.0 and thinking mode.* April 21,
> 2026. https://deploymentsafety.openai.com/chatgpt-images-2-0
>
> Sutton-Smith, B. (1981). *The Folkstories of Children.* University of
> Pennsylvania Press.

## Consistency checklist (before the Aug 6 send)

- [ ] §3.2's printed constraint == frozen string in PROTOCOL.md §2 == deployed
      Worker string (byte-identical).
- [ ] §3.1's "the platform only adds the one-line safety constraint" still true
      as worded.
- [ ] Edit 2 composes with the corrected backstop phrasing of the word-filter
      sentence, not the old one.
- [ ] Acknowledgments: the comment that motivated the keep direction is Prof.
      Cassell's; extend the acknowledgment sentence if she should be named for
      this specifically.
- [ ] Build notes: add §4.2 to the READ-ALOUD list if desired.
