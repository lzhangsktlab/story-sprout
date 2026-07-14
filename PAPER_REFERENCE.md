# Storybook Workshop — Paper Reference

**Status:** current as of commit `a7e7e61` (14 July 2026).

**What this is.** A verified account of what the system actually does, written for the paper — whose subject is the **allocation of agency between child and model**. It exists because the manuscript describes a system that has since changed underneath it, and because `HANDOFF.md`, `RESEARCH_DATA.md` and `STYLE_CONSISTENCY.md` are all materially out of date.

Every factual claim here was checked against source rather than recalled. Where the manuscript and the code disagree, this document says so plainly.

**Read §7 first if you are revising.** It is a claim-by-claim map of where the paper and the code diverge. Two of those divergences go to the argument, not the details.

**Scope.** This is organised around agency, not around engineering. Teacher Mode — teams, encryption, the sync protocol — appears only in §6, and only where it bears on the paper: **custody** (who ends up holding the child's work) and the **privacy claims** the manuscript makes. Its internals are deliberately out of scope; they live in `CLAUDE.md`.

A naming note: the repo is `story-sprout`, the product is **Storybook Workshop**, and the paper says **Story Sprout**. The two live pages say "Storybook Workshop". Pick one before submission.

---

## 1. The agency allocation, as actually enforced

The paper's §5 table, checked against the code. This is the section the argument rests on.

| The agency | Paper says | What the code actually enforces |
|---|---|---|
| **Origination** — the story, and every scene description | Child | ✅ **Holds.** There is no text-generation path anywhere. No continue, no title suggester, no rewrite. Pip's system prompt forbids contributing story content and redirects any non-illustration request. |
| **Rendering** | Model | ✅ **Holds.** There are no drawing tools for illustrations. The only way to get a picture is to describe one. |
| **Compiling the render prompt** | *Contested* — mitigated by "the direct drawer remains the unmediated path" | ⚠️ **The mitigation does not exist.** The direct drawer is `display:none`. Pip is the **only** reachable path, so the compilation step is unavoidable, not optional. See §4. |
| **Judgment / acceptance** | Child | ✅ **Holds.** No score, no praise, no auto-accept. A generated picture lands in Pip's *preview* — not on the canvas — and stays there until the child presses **Add to book**. |
| **Removal** | Child, on request, logged | ✅ **Holds.** A revision is placed *beside* the old picture. Pip may offer removal; it never performs it unprompted. Both add and remove are now logged (§5). |
| **Re-run / attribution** | Child, via the history strip | ❌ **The affordance is gone.** The history strip is `display:none`. The image bank shows past pictures but offers **no re-run**. §5's argument — *"a child can re-run an unchanged description and watch what persists and what varies"* — describes UI a child cannot use. |

**The honest summary:** four of the six allocations are enforced exactly as the paper claims. The two that aren't are both consequences of the same fact — **the direct drawer is hidden** — and they happen to be the two the paper uses to *contain* its central tension. That is the thing to fix, in code or in prose, before submission.

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

A chat model (`gpt-4o-mini`) behind the worker, governed by a written system prompt and constrained **structurally** by a JSON reply schema. Every turn the model must return exactly:

```json
{ "reply": "...", "ready": true|false, "image_prompt": "...", "remove_old": true|false }
```

The front end acts on those four fields and nothing else. Parameters: `temperature 0.5`, `max_tokens 400`, `response_format: json_object`, `store: false`. History is capped at the last **24 turns**, each truncated to 2,000 characters.

The server can **overrule the model**: `ready` is only true if the model said `true` *and* produced a non-empty `image_prompt`. A malformed reply degrades to a friendly fallback rather than an error.

**`PIP_SCOPE.md` is accurate.** It is the one document in this repo still in sync with the code — the greeting and the four rotating reflection questions are used verbatim. §4.2 of the paper is correct as written.

### The three rules that do the pedagogical work

- **Draw by default; ask at most one question.** A subject plus *any* concrete detail — colour, place, action, mood, or art style — must be drawn immediately. One clarifying question is permitted only for a bare subject ("a dog") or a pure judgment word ("make it better") with nothing concrete to act on.
- **Complete-scene prompts.** Each render is fresh, so the compiled prompt must restate every detail agreed so far. A requested style is carried forward until the child changes it.
- **Compare, then remove only on request.**

### The tension, stated exactly

The paper's §3 is right that Pip is a scribe, and right to be uneasy about it. Here is precisely what happens, because the wording matters for a paper about agency:

> **The child never writes the image prompt.** They converse with Pip in their own words. `gpt-4o-mini` decides when it has enough, and *authors* an `image_prompt` — a complete scene description — which is what actually reaches the image model. The child's words and the model's words are different strings.

The system prompt forbids Pip from inventing plot or scene content; it may only aggregate what the child supplied, plus a default storybook style. But **aggregation is still authorship of the prompt**, and a normalised phrase can quietly repair an omission before the child ever sees it rendered — exactly the worry §3 names.

**What has changed, and it strengthens the paper:** both strings are now recorded (§5). The scribe tension is no longer merely acknowledged — it is **measurable**. You can quantify how far Pip's compiled prompt departs from the child's own words, across a session and across children. That is a stronger position than the manuscript currently claims, and it deserves a paragraph rather than a caveat.

---

## 4. The direct drawer is hidden — the correction that matters most

There is a second, older generation path: a manual drawer with a labelled **Prompt** field, a **style menu** (Digital Art, Comic Book, Fantasy Art, Photographic, Cinematic), a **draft/final quality** toggle, and a **history strip** preserving every attempt with the exact words that produced it.

**A child cannot reach it.** The container is `<div id="ai-manual-ui" style="display:none">`. The history strip is `display:none` too. The code is retained and still wired; the UI is invisible.

This is the single most consequential divergence, because three separate parts of the argument lean on it:

| Paper | What it claims | Reality |
|---|---|---|
| §3 (the scribe tension) | *"the direct prompt drawer remains the unmediated path, living inside the same product"* | There is **no unmediated path**. Every picture goes through Pip's compilation step. |
| §4.1 (style) | The style menu is *"the studio's one explicit aesthetic control"* | A child cannot see it. In Pip mode, style is expressed **conversationally** and carried forward by the system prompt — a different mechanism, worth describing as such. |
| §5 (attribution) | A child can *"re-run an unchanged description and watch what persists and what varies"* | The history strip is hidden and the image bank has **no re-run**. The affordance the attribution argument depends on does not exist. |

**Decide before you revise.** Either un-hide the drawer so the deployed system matches the paper, or rewrite §3, §4.1 and §5 for a Pip-only system. Both are defensible. What is not defensible is a paper describing an escape hatch the children never had.

Note the two paths also capture *different* research data (§5) — so this choice has methodological consequences, not just rhetorical ones.

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
| `settings.style_preset` / `quality` | **Always `{}`** (those come from the hidden legacy drawer). |
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

---

## 7. Corrections to the paper

**Work from this table.**

| § | The paper says | The code does |
|---|---|---|
| Abstract, §3.4, §4.4, §5, §7 | *"no accounts and no server-side storage of children's work"*, *"no cloud"* | **False.** Work is stored (encrypted) on Cloudflare R2; the teacher has a Google account. Correct claim: **"no readable server-side storage"** — a zero-knowledge relay. Children still have no accounts. |
| §3, §4.1, §5 | *"the direct prompt drawer remains the unmediated path"* | **Hidden** (`display:none`). Pip is the only path. **The escape hatch containing your central tension does not exist.** |
| §4.1 | The style menu is *"the studio's one explicit aesthetic control"* | Hidden with the drawer. In Pip mode style is conversational, carried forward by the system prompt. |
| §4.1, §5 | *"a visible history strip"*; a child can *"re-run an unchanged description"* | Hidden; the image bank offers **no re-run**. §5's attribution argument describes an affordance that isn't there. |
| §4.1 | *"the platform appends only that chosen style, a fixed landscape-composition hint, and the safety constraint"* | True of the **legacy** path only. Pip sends **no style suffix and no landscape hint** — only the safety clause. (Landscape happens because the API default is 1536×1024.) |
| §4.3 | *"three routes"*; *"stores nothing beyond ephemeral in-memory rate-limit counters"* | Three AI routes **plus ten sync routes**. The worker writes to R2. |
| §4.3 | *"rate-limits per client IP"* | True for AI routes. Sync is limited **per team** — a classroom shares one NAT IP. |
| §4.4 | The project file contains *"prompts … settings … revision links, and a log of additions and removals"* | **Aspirational until 14 July 2026.** See §5. Now true — but **only going forward.** |
| §4.1, §6, Acks | Voice input, framed around fidelity | Until 14 July 2026 the microphone **streamed children's voice audio to Google**. Now on-device, failing closed. Voice is explicitly personal information under the amended COPPA Rule. **Your Ethics statement needs this.** |
| §7 | *"no telemetry"* | Was **false** — every page load fetched Google Fonts and cdnjs, leaking the child's IP to two third parties. Both now self-hosted. **Now true.** |
| §5 | *"gpt-image-2 at the time of writing"* | ✅ Correct. |
| §4.2 | The JSON schema and the three rules | ✅ Correct. `PIP_SCOPE.md` is in sync. |

### Documents to disregard

- **`HANDOFF.md`** — describes a Stability AI system that no longer exists: wrong provider, wrong worker URL, wrong secret, wrong routes. No mention of Pip.
- **`STYLE_CONSISTENCY.md`** — stale at the premise (Stability seeds, negative prompts, `style_preset`). Its *goal* is now solved by a different mechanism: **Pip's most recent image is fed back as the base for the next one**, which is what actually keeps characters and style consistent across a book.
- **`RESEARCH_DATA.md`** — superseded by §5. Its privacy note (*"not sent to any server"*) is false twice over.

---

## 8. Safety, and what leaves the machine

### Content safety is layered (§4.3 of the paper is right about this)

1. **Pip's system prompt** scopes the conversation to illustration, refuses age-inappropriate requests in-fiction with an offered alternative, and never asks for or repeats personal information.
2. **A server-side safety clause** is appended to *every* image request, after truncation, so the client cannot strip it: *"The image must be wholesome and appropriate for young children: no violence, gore, weapons, blood, scary or frightening imagery, and no adult content."*
3. **It is deliberately silent about aesthetics.** A child asking for watercolour gets watercolour. The guardrail constrains *what may be depicted*, never *how it looks* — the same allocation as §3, made from the other side.
4. **OpenAI's moderation refusals** are caught and translated into a soft redirect: *"Hmm, I can't draw that one. Let's try a different picture."*
5. **A safety notice** now blocks Pip's chat box the first time it is opened each session: *don't tell Pip your real name, your school, or where you live* — and it **redirects** rather than only prohibiting (*"want a person in your picture? just say what they look like — 'a girl with red boots'"*). It is a **notice, not a control**: it cannot stop a determined child, and is not a substitute for supervision or consent.

### Speech is now on-device, and fails closed

The Web Speech API is **server-based by default** — Chrome streams the microphone audio to Google. That is what this app did until 14 July 2026.

It now sets `processLocally = true`, so neither audio nor transcript leaves the machine. The critical property is the **failure mode**: if on-device recognition is unavailable the microphone **refuses to work** rather than falling back — a silent fallback is precisely what would ship a child's voice to Google while everyone believed it was local.

Recognised text lands in the input box for the child to read, edit and send. It is never submitted automatically — so §4.1's claim that *"the child's own words, not the recognizer's guess"* reach the renderer holds.

### What actually leaves the child's machine

| Data | Destination |
|---|---|
| Conversation + image prompts | **OpenAI** (via our worker). This is the product; unavoidable. |
| Encrypted story + images | **Cloudflare R2** — class mode only, zero-knowledge, expires. |
| Client IP | Our worker, in memory, 60 s, no durable log. |
| Microphone audio | **Nowhere.** On-device. |
| Imported images (incl. any photo a child adds) | Story file → encrypted to the teacher. **Never sent to OpenAI.** |
| ~~Google Fonts, cdnjs~~ | **Removed** — self-hosted. |
| ~~A persistent device ID~~ | **Removed** — nothing ever read it. |
| ~~The teacher's email on R2~~ | **Removed** — the relay now holds no identifying data at all. |

**Never collected:** a child's name, age, school, or any account of any kind.

### Two residual risks the paper should name

Neither is fixable in code, and both belong in the Ethics statement:

- **A child can volunteer personal information in free text.** Pip's system prompt forbids it from *asking for or repeating* personal information, but nothing can stop a child typing their own name into a prompt. The safety notice (above) is the mitigation, and it is a notice, not a control.
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
- `workshop.html` (the original Stability AI app) and `cloudflare-worker/worker.js` are **dead code** retained in-repo. Neither runs; the former's API key has been removed.
