# StorySprout Studio — Paper Reference

**Status:** current as of the `audit/scribe-contract` branch (23 July 2026). Three things changed since the previous revision and are folded in below: the chat model moved to `gpt-5.4-mini`; the legacy manual drawer was **deleted** (not merely hidden); and the scribe tension the paper worries about has now been **measured** (§3, §4).

**What this is.** A verified account of what the system actually does, written for the paper — whose subject is the **allocation of agency between child and model**. It exists because the manuscript describes a system that has since changed underneath it, and because `RESEARCH_DATA.md` is materially out of date. (`HANDOFF.md` and `STYLE_CONSISTENCY.md` were removed from the repo — both described the retired Stability AI system.)

Every factual claim here was checked against source rather than recalled. Where the manuscript and the code disagree, this document says so plainly.

**Read §7 first if you are revising.** It is a claim-by-claim map of where the paper and the code diverge. Two of those divergences go to the argument, not the details.

**Scope.** This is organised around agency, not around engineering. Teacher Mode — teams, encryption, the sync protocol — appears only in §6, and only where it bears on the paper: **custody** (who ends up holding the child's work) and the **privacy claims** the manuscript makes. Its internals are deliberately out of scope; they live in `CLAUDE.md`.

A naming note: the repo is `story-sprout`, the product is now **StorySprout Studio** (the two live pages were renamed from "Storybook Workshop"), and the paper says **Story Sprout**. The app name is settled; only the manuscript's **Story Sprout** remains to reconcile before submission.

---

## 1. The agency allocation, as actually enforced

The paper's §5 table, checked against the code. This is the section the argument rests on.

| The agency | Paper says | What the code actually enforces |
|---|---|---|
| **Origination** — the story, and every scene description | Child | ✅ **Holds.** There is no text-generation path anywhere. No continue, no title suggester, no rewrite. Pip's system prompt forbids contributing story content and redirects any non-illustration request. |
| **Rendering** | Model | ✅ **Holds.** There are no drawing tools for illustrations. The only way to get a picture is to describe one. |
| **Compiling the render prompt** | *Contested* — mitigated by "the direct drawer remains the unmediated path" | ⚠️ **The mitigation does not exist.** The direct drawer has been **removed from the code**. Pip is the **only** reachable path, so the compilation step is unavoidable, not optional — but the compiled prompt is now bound by an explicit scribe rule and verified against it (§3, §4). See §4. |
| **Judgment / acceptance** | Child | ✅ **Holds.** No score, no praise, no auto-accept. A generated picture lands in Pip's *preview* — not on the canvas — and stays there until the child presses **Add to book**. |
| **Removal** | Child, on request, logged | ✅ **Holds.** A revision is placed *beside* the old picture. Pip may offer removal; it never performs it unprompted. Both add and remove are now logged (§5). |
| **Re-run / attribution** | Child, via the history strip | ❌ **The affordance is gone.** The history strip has been **removed**. The image bank shows past pictures but offers **no re-run**. §5's argument — *"a child can re-run an unchanged description and watch what persists and what varies"* — describes UI that no longer exists. |

**The honest summary:** four of the six allocations are enforced exactly as the paper claims. The two that aren't are both consequences of the same fact — **the direct drawer has been removed** — and they happen to be the two the paper uses to *contain* its central tension. The code decision is now made: there is no escape hatch. What remains is a **prose** fix — rewrite §3, §4.1 and §5 for a Pip-only system, which is stronger ground than the paper currently stands on (§4).

---

## 2. What the child can and cannot do

A story is an ordered list of **pages** on an 800 × 540 canvas (Fabric.js 5.3.1, self-hosted). The child can add text boxes, shapes and imported images; move, scale, rotate, layer and align them; reorder pages by dragging; undo and redo; and export a page as PNG.

**There are no drawing tools for the illustrations.** This is the load-bearing absence. The child cannot draw the picture, only describe it — which is what makes the describing the work, exactly as §3.2 of the paper argues.

The child's written story sits in a side panel as **click-to-copy lines**, so words move from manuscript to prompt without retyping. Nothing flows back the other way.

Two details worth knowing:

- **Undo now covers page deletion.** Until 13 July 2026 it did not: deleting a page destroyed the work on it permanently, with no way back. If any session predates that, it is a silent data-loss path.
- **The app does not auto-resume.** A fresh load starts blank by design; the autosave (5 s debounce) is a safety net, not a session-restore.

---

## 3. Pip — and the scribe tension, precisely

### What Pip is

A chat model (`gpt-5.4-mini`, a reasoning model) behind the worker, governed by a written system prompt and constrained **structurally** by a JSON reply schema. Every turn the model must return exactly:

```json
{ "reply": "...", "ready": true|false, "image_prompt": "...", "remove_old": true|false }
```

The front end acts on those four fields and nothing else. Parameters: `reasoning_effort: low`, `max_completion_tokens 1000`, `response_format: json_object`, `store: false`, and the model's default temperature (this model rejects a custom `temperature`, and rejects `max_tokens` in favour of `max_completion_tokens` — see §7). History is capped at the last **24 turns**, each truncated to 2,000 characters.

The server can **overrule the model**: `ready` is only true if the model said `true` *and* produced a non-empty `image_prompt`. A malformed reply degrades to a friendly fallback rather than an error.

**`PIP_SCOPE.md` is accurate for §4.2, and only for §4.2.** The greeting and all four rotating reflection questions are still used verbatim — verified by exact string match against `PIP_GREETING` and `PIP_IMAGE_CHECKS` in `workshop-plugin.html`. §4.2 of the paper is correct as written and needs no change.

⚠️ It is **not** a current description of Pip's behaviour, and this file used to claim it was "the one document still in sync with the code." That was true when written and is now false: `PIP_SCOPE.md` has not tracked the Worker since June 2026, and is missing the scribe rule, the weapons rules, and the teacher-set content levels. For anything beyond the greeting and the reflection questions, cite `PIP_SYSTEM` in `cloudflare-worker/pip-worker.js`.

### The three rules that do the pedagogical work

- **Draw by default; ask at most one question.** A subject plus *any* concrete detail — colour, place, action, mood, or art style — must be drawn immediately. One clarifying question is permitted only for a bare subject ("a dog") or a pure judgment word ("make it better") with nothing concrete to act on.
- **Complete-scene prompts.** Each render is fresh, so the compiled prompt must restate every detail agreed so far. A requested style is carried forward until the child changes it.
- **Compare, then remove only on request.**

### The tension, stated exactly

The paper's §3 is right that Pip is a scribe, and right to be uneasy about it. Here is precisely what happens, because the wording matters for a paper about agency:

> **The child never writes the image prompt.** They converse with Pip in their own words. `gpt-5.4-mini` decides when it has enough, and *authors* an `image_prompt` — a complete scene description — which is what actually reaches the image model. The child's words and the model's words are different strings.

The system prompt forbids Pip from inventing plot or scene content. Since the scribe-rule update it goes further: the `image_prompt` must **carry the child's details in the child's own words, typos and grammar included, adding nothing** — and it adds **no default style** unless the child asked for one (the earlier "default storybook style" is gone). Assembly is still an act — the model chooses order and joins fragments — so it remains *authorship of the prompt* in the strict sense the paper means. But the room for a normalised phrase to quietly repair an omission is now explicitly forbidden by the contract, not merely discouraged.

**What has changed, and it strengthens the paper considerably:** both strings are recorded (§5), so the scribe tension is not merely acknowledged — it is **measured**. A held-out audit (60 unseen four-turn sequences × 3 stochastic reps, committed under `scribe_audit_v3_heldout_out/`) scores whether the child's exact words survive into the compiled prompt. On the selected configuration the result is **240/240 verbatim across all three reps and 0/720 unrequested additions** — the model carried every seeded typo through and invented nothing. That is a far stronger claim than "we concede a tension": the departure of Pip's prompt from the child's words is now *quantified and near-zero*, and it deserves a results paragraph, not a caveat. The harness and its full protocol are in the repo (`scribe_audit_v3_heldout.py`, `--rescore`; see the README's *Research artifacts*).

---

## 4. The direct drawer has been removed — the correction that matters most

There was a second, older generation path: a manual drawer with a labelled **Prompt** field, a **style menu** (Digital Art, Comic Book, Fantasy Art, Photographic, Cinematic), a **draft/final quality** toggle, and a **history strip** preserving every attempt with the exact words that produced it. Earlier revisions of this document noted it was present but hidden (`display:none`), code retained and still wired.

**It is now gone.** The `#ai-manual-ui` container, the history strip, their generator functions (`generateAiImage`, `modifyAiImage`, and the strip machinery), their bindings and their CSS were **deleted** from `workshop-plugin.html`. There is no manual path in the code at all — hidden or otherwise. Pip is the only way to make a picture.

This was the single most consequential divergence, because three separate parts of the argument lean on the drawer existing:

| Paper | What it claims | Reality |
|---|---|---|
| §3 (the scribe tension) | *"the direct prompt drawer remains the unmediated path, living inside the same product"* | There is **no unmediated path**, and no drawer to point to. Every picture goes through Pip's compilation step. |
| §4.1 (style) | The style menu is *"the studio's one explicit aesthetic control"* | It no longer exists. In Pip mode, style is expressed **conversationally** and carried forward by the system prompt — a different mechanism, worth describing as such. |
| §5 (attribution) | A child can *"re-run an unchanged description and watch what persists and what varies"* | The history strip is gone and the image bank has **no re-run**. The affordance the attribution argument depends on does not exist. |

**The decision is made; only the prose remains.** The earlier version of this section asked you to choose — un-hide the drawer to match the paper, or rewrite for a Pip-only system. That choice is settled: the drawer is removed, so §3, §4.1 and §5 must be rewritten for a Pip-only system. This is the *stronger* position — the paper no longer has to explain an escape hatch the children never had, and the scribe tension it was used to contain is now measured directly (§3).

One methodological consequence to retire with it: the two paths used to capture *different* research data. With the manual path gone, there is now a single, uniform record — every attempt is a Pip attempt, with the `childWords`/`imagePrompt` split (§5).

---

## 5. The research record — what is and is not captured

This supersedes `RESEARCH_DATA.md` entirely.

### What is captured now (schema v6, since 14 July 2026)

| Field | Holds |
|---|---|
| `pipConversation` | **The child's own words, verbatim, timestamped.** Every turn, including Pip's greeting. |
| `promptLog` | One record per generation attempt. **Never capped.** |
| `aiHistory` | The image cache. Capped at 20, newest-first. |
| `session` | `{startedAt, savedAt, totalSlides}` |

A `promptLog` record:

```json
{
  "historyId": "ai_1752...",
  "at": "2026-07-14T10:15:30.000Z",
  "source": "pip",
  "childWords":  "make the dog fluffy and put him in the snow",     // what the CHILD said
  "imagePrompt": "A fluffy white dog standing in a snowy park...",  // what the MODEL wrote
  "turnIndex": 7,
  "actions": [ { "type": "added_to_canvas", "at": "...", "slideIdx": 0 } ]
}
```

**The `childWords` / `imagePrompt` split is the heart of the dataset.** It is what lets you measure the scribe tension rather than merely concede it.

The research log is deliberately **separate from the image cache** and never capped. They were one array, limited to 20 *because each entry carries a 2–3 MB image*. Prompts are tiny. A child who makes 40 attempts now keeps all 40 — including the earliest and least refined, which are exactly what a progression study needs.

`added_to_canvas` and `removed_from_canvas` are logged with timestamp and page index, on Pip's approve button, on image-bank click and drag, and on deletion. Clearing the picture strip does **not** erase the record; only starting a new story does.

### ⚠️ What any pre-July data is missing — and it cannot be retrofitted

`RESEARCH_DATA.md` described a schema the code did not implement. In the Pip flow — the only flow a child could reach:

| The doc claimed | What actually happened |
|---|---|
| `prompt` = *"the text prompt the student wrote"* | **The model's rewritten prompt.** The child's words were never saved anywhere. |
| The conversation is available | **Never serialised.** It died on every page load. |
| `parentId` links refinement chains | **Always `null`.** |
| `settings.style_preset` / `quality` | **Always `{}`** (those came from the now-removed legacy drawer; the field is retained empty for back-compat). |
| `actions[]` records add/remove | **Never fired.** Pip-added images carried no `historyId`, and the logger is gated on it. |
| *"Number of `aiHistory` items shows total generation attempts"* | **Capped at 20.** The earliest generations were silently discarded. |

**Consequence:** `RESEARCH_DATA.md`'s analyses **§1 (prompt progression), §2 (iteration patterns), §3 (style experimentation) and §4 (selection & revision behaviour) were not supported by the data the code produced.** If any pilot session used Pip, treat those files as unusable for those analyses.

Also: `aiHistory` is stored **newest-first**. Any analysis assuming chronological array order is reversed.

**Two remaining limits:** `aiHistory` is still capped at 20 *images* (the prompts are all kept regardless), and `duplicateSelected` does not copy `historyId`, so a duplicated AI image loses its research link.

---

## 6. Where the child's work goes

*Only what bears on the paper: custody, and the privacy claims. The engineering is out of scope.*

### The custody claim — now literally true, by a mechanism the paper doesn't describe

§3.4 argues *"the record stays with the supervising adult."* That is now implemented rather than merely asserted: in class mode, a child's story is collected onto **the teacher's own computer**, as a real file, with a dated history of how it grew. The teacher can delete it, which erases every copy.

### But the "no cloud" sentences are false

The mechanism is a **relay**. A browser cannot reach into another computer — a student's browser is not a server, and the two machines are rarely online together — so an intermediary is unavoidable.

The relay is a **dead-drop, not a database**: the child's browser encrypts the story *before* it leaves the machine, using a key derived from a secret code the operator never holds. Cloudflare stores bytes it cannot read, and they expire.

That is a strong story. But these sentences, which appear in the **Abstract, §3.4, §4.4, §5 and §7**, are no longer true:

- *"no server-side storage of children's work"*
- *"retains no server-side project copy"*
- *"No accounts, no cloud, no telemetry"*

**The defensible claim is "no *readable* server-side storage."** Children still have no accounts — the teacher signs in with Google, and a team identifies *a computer, not a person*. The spirit of the argument survives intact. The sentences do not.

**One thing to say out loud:** the secret codes are the only keys that exist. They live in plaintext in a file on the teacher's computer. If that file is lost, every child's work becomes permanently unreadable — by the teacher, by us, by Cloudflare. That is the exact price of the zero-knowledge property, and a paper that claims the privacy benefit should state the cost.

**And a second:** the codes are deliberately short — six digits, ~20 bits — because a seven-year-old has to type one off a sticker. That is protection against a curious classmate, not against a determined adversary who pulls the ciphertext and grinds the keyspace (PBKDF2's 600k iterations raise the price of each guess; they do not change the arithmetic of a million-code space). The threat model here is honest: the encryption exists so that *the infrastructure* — us, Cloudflare — cannot read children's work, not to survive a targeted attack. If the paper cites the encryption, it should state the trade in the same breath.

---

## 7. Corrections to the paper

**Work from this table.**

| § | The paper says | The code does |
|---|---|---|
| Abstract, §3.4, §4.4, §5, §7 | *"no accounts and no server-side storage of children's work"*, *"no cloud"* | **False.** Work is stored (encrypted) on Cloudflare R2; the teacher has a Google account. Correct claim: **"no readable server-side storage"** — a zero-knowledge relay. Children still have no accounts. |
| §3, §4.1, §5 | *"the direct prompt drawer remains the unmediated path"* | **Removed** from the code. Pip is the only path. **The escape hatch containing your central tension does not exist.** |
| §4.1 | The style menu is *"the studio's one explicit aesthetic control"* | Removed with the drawer. In Pip mode style is conversational, carried forward by the system prompt. |
| §4.1, §5 | *"a visible history strip"*; a child can *"re-run an unchanged description"* | Removed; the image bank offers **no re-run**. §5's attribution argument describes an affordance that isn't there. |
| §4.1 | *"the platform appends only that chosen style, a fixed landscape-composition hint, and the safety constraint"* | True of the **removed legacy** path only. Pip sends **no style suffix and no landscape hint** — only the safety clause. (Landscape happens because the API default is 1536×1024.) |
| §3, §4.3 | The chat model (implied `gpt-4o-mini`) | Now **`gpt-5.4-mini`** (a reasoning model): `reasoning_effort: low`, `max_completion_tokens`, default temperature. The model was chosen by a committed audit (§3, README *Research artifacts*). The public demo may still run the prior model until the worker is redeployed. |
| §4.3 | *"three routes"*; *"stores nothing beyond ephemeral in-memory rate-limit counters"* | Three AI routes **plus ten sync routes**. The worker writes to R2. |
| §4.3 | *"rate-limits per client IP"* | True for AI routes. Sync is limited **per team** — a classroom shares one NAT IP. |
| §4.4 | The project file contains *"prompts … settings … revision links, and a log of additions and removals"* | **Aspirational until 14 July 2026.** See §5. Now true — but **only going forward.** |
| §4.1, §6, Acks | Voice input, framed around fidelity | Until 14 July 2026 the microphone **streamed children's voice audio to Google**. Now on-device, failing closed. Voice is explicitly personal information under the amended COPPA Rule. **Your Ethics statement needs this.** |
| §7 | *"no telemetry"* | Was **false** — every page load fetched Google Fonts and cdnjs, leaking the child's IP to two third parties. Both now self-hosted. **Now true.** |
| §5 | *"gpt-image-2 at the time of writing"* | ✅ Correct. |
| §4.2 | The JSON schema and the three rules | ✅ Correct. The greeting and four reflection questions in `PIP_SCOPE.md` are still verbatim — but nothing else in that file is current; cite `PIP_SYSTEM` for the rest. |

### Documents to disregard

- **`HANDOFF.md`** — **removed from the repo.** It described a Stability AI system that no longer exists: wrong provider, wrong worker URL, wrong secret, wrong routes, no mention of Pip.
- **`STYLE_CONSISTENCY.md`** — **removed from the repo.** It was stale at the premise (Stability seeds, negative prompts, `style_preset`). Its *goal* is met by a different mechanism: **Pip's most recent image is fed back as the base for the next one**, which is what actually keeps characters and style consistent across a book.
- **`RESEARCH_DATA.md`** — still present but superseded by §5. Its privacy note (*"not sent to any server"*) is false twice over.

---

## 8. Safety, and what leaves the machine

### Content safety is layered (§4.3 of the paper is right about this)

1. **Pip's system prompt** scopes the conversation to illustration, refuses age-inappropriate requests in-fiction with an offered alternative, and never asks for or repeats personal information.
2. **A server-side safety clause** is appended to *every* image request, after truncation, so the client cannot strip it: *"The image must be wholesome and appropriate for young children: no weapons of any kind (no guns, rifles, rocket launchers, grenades, bombs, or other firearms or military hardware — not even toy or cartoon versions), no violence, gore, blood, scary or frightening imagery, and no adult content."* A regex weapon-block on the image routes is a second backstop, in case a cute-sounding scene slips a weapon past the chat model.
3. **It is deliberately silent about aesthetics.** A child asking for watercolour gets watercolour. The guardrail constrains *what may be depicted*, never *how it looks* — the same allocation as §3, made from the other side.
4. **OpenAI's moderation refusals** are caught and translated into a soft redirect: *"Hmm, I can't draw that one. Let's try a different picture."*
5. **A safety notice** blocks Pip's chat box the first time it is opened each session: *don't tell Pip your real name, your school, or where you live* — and it **redirects** rather than only prohibiting (*"want a person in your picture? just say what they look like — 'a girl with red boots'"*). It is a **notice, not a control**.
6. **A pre-transmission filter** — which *is* a control. See below.

### The pre-transmission filter, and why it does not block names

A message containing personal information is **blocked in the browser, before the request is made** — so it never leaves the child's computer at all. That is strictly stronger than filtering at the worker, where the text has already left the machine. The worker redacts as well, on both the chat and image routes, as a backstop against a stale client.

**What it blocks:** email addresses, phone numbers, URLs, street addresses, and self-identifying constructions — *"my name is…"*, *"I'm called…"*, *"my school is…"*, *"I live at 12 Oak Street"*, *"my address…"*, *"my phone…"*.

**What it deliberately does not touch: names.** This is the design decision, and it is the one worth defending in the paper:

> *"Emma the brave knight rides a dragon"* is **textually identical** to a child naming a real friend. There is no feature that separates them, and a name filter would either break every story or catch nothing. Storybooks are made of names — filtering them would destroy the thing the system exists for.
>
> But a child **telling the model who they are** has a *grammar*: `my name is …`, `I live at …`, `my school is …`. A name merely *appearing* does not. **We filter the grammar, not the noun.**

`pii-filter-test.html` guards both directions, and the false-positive direction is the one that matters more: *"a princess called Aurora"*, *"my dog is called Rex"*, *"I live in a castle made of candy"* and *"my school bus is yellow"* all pass untouched, while *"my name is Jamie"* and *"I live at 12 Oak Street"* are caught.

**Blocked text is never stored** — not in the story file, not synced to the teacher. The system records that a block occurred and *what category*, never the words. Retaining a child's personal information in order to note that it refused to transmit it would rather defeat the exercise.

**For the paper:** this is what turns "reasonable steps" from a claim into a mechanism. It is also the third thing the model is not permitted to do — it may not originate the story, may not judge the result, and may not learn who it is working for (§ below). The filter and the proxy enforce that last one from opposite ends: the proxy strips every identifier the *system* would attach; the filter strips the ones a *child* might volunteer.

### Speech is now on-device, and fails closed

The Web Speech API is **server-based by default** — Chrome streams the microphone audio to Google. That is what this app did until 14 July 2026.

It now sets `processLocally = true`, so neither audio nor transcript leaves the machine. The critical property is the **failure mode**: if on-device recognition is unavailable the microphone **refuses to work** rather than falling back — a silent fallback is precisely what would ship a child's voice to Google while everyone believed it was local.

Recognised text lands in the input box for the child to read, edit and send. It is never submitted automatically — so §4.1's claim that *"the child's own words, not the recognizer's guess"* reach the renderer holds.

### What actually leaves the child's machine

| Data | Destination |
|---|---|
| Conversation + image prompts | **OpenAI** (via our worker), **after the pre-transmission filter**. This is the product; the channel is unavoidable, the personal information in it is not. |
| Encrypted story + images | **Cloudflare R2** — class mode only, zero-knowledge, expires. |
| Client IP | Our worker, in memory, 60 s, no durable log. |
| Microphone audio | **Nowhere.** On-device. |
| Imported images (incl. any photo a child adds) | Story file → encrypted to the teacher. **Never sent to OpenAI.** |
| ~~Google Fonts, cdnjs~~ | **Removed** — self-hosted. |
| ~~A persistent device ID~~ | **Removed** — nothing ever read it. |
| ~~The teacher's email on R2~~ | **Removed** — the relay now holds no identifying data at all. |

**Never collected:** a child's name, age, school, or any account of any kind.

### What the proxy achieves — and the paper undersells it

§4.4 currently says only that *"prompts pass through the stateless proxy to the model provider … under the provider's API terms."* That is honest, but it describes the proxy as a **key-hiding** measure and stops there. It does considerably more, and the stronger claim is available:

> **The proxy makes the child unidentifiable to the model provider.**

All three OpenAI calls are made **server-side, from the worker**. The child's browser never contacts `api.openai.com` at all. The worker builds a fresh request and sends only the API key, a content type, and a JSON body it constructs itself — it does not forward the child's IP address, user-agent, cookies, or any other client header.

So what actually crosses that boundary is **a scene description and nothing else.** OpenAI cannot correlate a request to a child, a device, or a session, because no identifier ever reaches it. There is no identity there to attribute anything to. Combined with a zero-retention configuration on the provider side, the provider retains nothing — and could not attribute it if it did.

**Why this belongs in an agency paper, not just a privacy footnote.** It is the same instinct as the rest of the design: *give the model exactly what it needs to do its one job, and nothing else.* The model is allowed to render. It is not allowed to originate the story, judge the result — or know who it is working for. The proxy is where that last restriction is enforced, and it is a design contribution rather than a compliance measure.

It also sharpens what the residual disclosure actually is. A scene description — *"a fluffy white dog in a snowy park"* — carries no personal information. The channel is not the exposure; **the content is**, and only when a child volunteers something about themselves. Which is precisely what the two risks below are about, and precisely what Pip's prompt and the safety notice are aimed at.

### Two residual risks the paper should name

Both belong in the Ethics statement:

- **The filter catches self-identification, not every possible disclosure.** It blocks a child *telling the model who they are*, and it cannot block a child who works around it — writing their own name as a character name, for instance, which is by construction indistinguishable from creative work. The filter is a real control and a substantial one; it is not a guarantee, and the paper should not claim it as one.
- **A child can import any local image onto the canvas** — including a photograph of themselves. That image stays in the story file and syncs encrypted to the teacher. It is **never** sent to OpenAI.

### On the paper's legal framing

The manuscript's posture — *"local custody is a data-minimization measure, not a claim of exemption or compliance"* — is **correct, and should be kept verbatim.** The engineering above strengthens the *minimisation* claim considerably; it does not, and should not be read to, convert it into a compliance claim.

Two facts that bear directly on the **Ethics statement** as currently written:

- **Voice is now explicitly personal information** under the amended COPPA Rule (in force since June 2025), which expanded the definition to cover voice data. The manuscript describes voice input as a designed feature and its Ethics statement does not mention that, until 14 July 2026, the audio left the device. It now does not.
- **"No telemetry" is now true, and was not before.** Every page load previously fetched Google Fonts and Fabric.js from third-party CDNs, disclosing the child's IP address to Google and Cloudflare before the child had done anything. Both are self-hosted.

Everything else — consent instruments, provider agreements, retention and security documentation — is operational and outside this document's scope.

---

## Appendix A — things a reviewer might catch

- Teacher Mode requires **Chrome or Edge** (File System Access API). Firefox and Safari cannot do it.
- `S.imgMap` and `S.dirHandle` are **dead** — always `{}` / `null`. Vestiges of a removed scheme.
- `duplicateSelected` does not copy `historyId`, so a duplicated AI image loses its research link.
- A **50 MB story syncs in about 1.5 KB**, because images are content-addressed and uploaded once. Worth a sentence if the paper discusses feasibility on school wifi.
- `workshop.html` (the original Stability AI app) and `cloudflare-worker/worker.js` have been **removed from the repo** — along with the hidden manual generator inside `workshop-plugin.html` (§4). The Stability AI path is gone in its entirety.
