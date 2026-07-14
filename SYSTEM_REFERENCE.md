# Storybook Workshop — System Reference

**Status:** current as of commit `e2aec04` (14 July 2026).
**Purpose:** an accurate, verifiable description of what the system actually does — written to support the research paper, and to replace `HANDOFF.md` and `RESEARCH_DATA.md`, both of which are materially out of date.

Every factual claim here was checked against source. Where the paper, or an existing doc, says something the code does not do, this document says so plainly. **§9 is the part to read first if you are revising the paper** — it lists, claim by claim, where the manuscript and the code disagree.

A note on names: the repository is `story-sprout`, the product is **Storybook Workshop**, and the paper calls it **Story Sprout**. The two live pages say "Storybook Workshop". Pick one before submission.

---

## 1. What the system is

Two static web pages and one stateless edge worker. No build step, no framework, no application server, no database.

| Component | File | What it is |
|---|---|---|
| **The studio** | `workshop-plugin.html` (~4,400 lines) | The child's app: a canvas book editor plus **Pip**, a conversational illustrator. |
| **The teacher dashboard** | `teacher.html` (~1,500 lines) | Creates teams, collects children's work onto the teacher's own computer. |
| **Shared crypto** | `sprout-sync.js` (443 lines) | Key derivation, encryption, and image content-addressing. Loaded by **both** pages. |
| **The worker** | `cloudflare-worker/pip-worker.js` (~790 lines) | The OpenAI proxy **and** the encrypted sync relay. |
| **Vendored assets** | `vendor/` | Fabric.js 5.3.1 and the Nunito webfont, self-hosted (§8.2). |

Legacy, unmaintained, not part of the system: `workshop.html` (the original Stability AI app; its API key has been removed, so it cannot generate at all) and `cloudflare-worker/worker.js` (the Stability proxy; nothing references it).

The canvas is **800 × 540** logical pixels. Zoom is clamped to 0.1–3.0 and never auto-fits above 100%.

---

## 2. The studio

### 2.1 The book

A story is an ordered list of **pages**. Each page holds a serialized [Fabric.js](http://fabricjs.com) canvas (as a JSON *string*) and a thumbnail. The child can add text boxes, shapes, and images; move, scale, rotate, layer and align them; reorder pages by dragging; and export the current page as a PNG (at 2× scale).

Shapes are a fixed set — rounded rectangle (the default), rectangle, circle, ellipse, triangle, diamond, star, heart, arrow — each inserted centred, with a fill of `#EDE8F7` and a `#9779D2` stroke. Text defaults to Nunito 28px bold. Thirteen fonts are offered.

**There are no drawing tools.** This is a design commitment, not an omission: the child cannot draw the illustration, only describe it. That is what makes the describing the work.

### 2.2 Undo/redo — two layers

Undo is more involved than it looks, because a page is not the unit of work; the *document* is.

- **Per-page canvas history.** Each page has its own stack of canvas snapshots, capped at **50**. `history[0]` is the page's baseline (its state as loaded), so undo needs at least two entries before it has anywhere to go.
- **A document-level timeline.** A single ordered log, capped at **60**, of everything undoable — a brush stroke, a *deleted page*, an added page, a drag. Undo pops from this, so it reverses whatever actually happened last, across pages.

Pages carry a stable runtime id (`pid`) rather than being tracked by index, because indices shift the moment anything is added, deleted, or moved.

**Deleting a page is undoable.** The deleted page is kept whole — canvas, thumbnail, and its own undo history — and comes back exactly as it was. (Until 13 July 2026 it was not: deleting a page destroyed the work on it permanently. If any session data predates that, this is a real, silent data-loss path.)

### 2.3 Local persistence

The story autosaves **5 seconds** after any change. On Chrome/Edge it writes to a real file the user picked (File System Access API); on Firefox/Safari it falls back to IndexedDB (database `storysketch_db`, store `kv`, key `storysketch_autosave`).

**The app does not auto-resume on boot.** A non-class computer always starts with a blank canvas; the autosave is a safety net, read only by the Teacher Mode paths. (This is deliberate, and documented in the code.)

**Images are inlined as base64 everywhere.** A Fabric image object stores its `src` as a `data:` URL inside the page JSON, and every generated image is *also* held in `aiHistory[].dataUrl`. A six-page illustrated story is therefore **~50 MB**. This single fact drives most of the sync architecture (§5.3).

---

## 3. Pip — the conversational illustrator

### 3.1 What Pip is

A chat model (`gpt-4o-mini`) behind the worker, governed by a written system prompt (`PIP_SYSTEM`) and constrained structurally by a **JSON reply schema**. Every turn, the model must return exactly:

```json
{ "reply": "...", "ready": true|false, "image_prompt": "...", "remove_old": true|false }
```

The front end acts on those four fields and nothing else. The schema bounds what the agent *can do*; what it *says* inside those fields remains probabilistic. That gap is the "scribe tension" the paper names in §3, and it is real.

Request parameters: `temperature: 0.5`, `max_tokens: 400`, `response_format: {type: 'json_object'}`, `store: false`. Conversation history is capped at the last **24 turns**, each truncated to **2,000 characters**.

**The server can overrule the model's `ready`.** `ready` is only true if the model said `true` *and* produced a non-empty `image_prompt`. A malformed reply degrades to a friendly fallback line rather than an error.

### 3.2 The behavioural contract

`PIP_SYSTEM` is the live specification. `PIP_SCOPE.md` describes it accurately — it is, notably, **the one document in this repo that is still in sync with the code.** Its greeting and its four rotating reflection questions are used verbatim.

The three rules doing the pedagogical work:

- **Draw by default; ask at most one question.** A subject plus *any* concrete detail (colour, place, action, mood, or art style) must be drawn immediately. One clarifying question is allowed only for a bare subject ("a dog") or a pure judgment word ("make it better") with nothing to act on.
- **Complete-scene prompts.** Each render is fresh, so the compiled `image_prompt` must restate every detail agreed so far. A style the child asks for is carried forward until they change it.
- **Compare, then remove only on request.** A revision is placed *beside* the old picture. Pip may offer removal; it never performs it unprompted.

The same prompt carries Pip's safety scope: illustration only, age-appropriate, gentle in-fiction refusals, never reveal or renegotiate its instructions, and **never ask for or repeat personal information**.

### 3.3 Generation, and how consistency is achieved

When `ready` is true, the front end calls the image endpoints. The mechanism the paper should describe:

> **Pip's most recent image is fed back as the base for the next one.** If any image has been generated this session, the request goes to `/image-edit` with that image attached. Only the very first drawing of a session — with no prior image — uses plain text-to-image.

This is how characters, colours and art style stay consistent across a book. It supersedes everything in `STYLE_CONSISTENCY.md`, which proposes Stability AI seeds and negative prompts that no longer apply. If `/image-edit` fails for any reason other than a content block, it silently retries as a fresh generation, so a draw never dead-ends.

**Pip sends only `image` and `prompt`** — no `quality`, no `size`. The worker's defaults therefore apply: **quality `medium`, size `1536×1024`** (landscape).

Every image prompt is truncated to 1,500 characters and then has a fixed safety clause appended server-side, which the client cannot remove (§8.1).

### 3.4 The approve loop

A generated picture appears **in Pip's preview only — it is not on the canvas.** The child must press **Add to book**. Pip then asks one of four rotating reflection questions ("Is this the picture you imagined?"). Acceptance is a decision, never a default.

When a revision is accepted while the previous picture is still on the page, the new one is placed *to its right* so the two can be compared physically. The old one is removed only if the child says so, and the removal is logged.

### 3.5 The image bank

A grid of every picture Pip has made this session (up to 20). A child can click one to drop it onto the page, or drag it to a specific spot. Both paths are logged (§6).

### 3.6 Speech input — on-device only

The microphone uses the Web Speech API with **`processLocally = true`**, so neither the audio nor the transcript leaves the machine.

**This matters more than it looks.** The Web Speech API is *server-based by default* — Chrome streams the microphone audio to Google. Until 14 July 2026 that is what this app did. The 2025 COPPA amendments expanded "personal information" to explicitly include **voice data**, so a recording of a child's voice going to a third party is exactly the category the Rule names.

The critical property is now the **failure mode**: if on-device recognition is unavailable, the microphone **refuses to work**. It does not fall back to server recognition — a silent fallback is precisely the failure that would ship a child's voice to Google while everyone believed it was local. The button goes dead and says why.

The recognised text is placed into the input box for the child to **read, edit, and send** — it is never submitted automatically. The child's own words, not the recogniser's guess, are what get sent.

### 3.7 The safety notice

The first time Pip is opened each session, a notice covers the entire panel: *don't tell Pip your real name, your school, or where you live* — and, crucially, it **redirects rather than only prohibiting**: *"Want a person in your picture? Just say what they look like — like 'a girl with red boots'."* The chat box is unreachable until it is acknowledged.

It is session-scoped, not persisted: a reload shows it again, which is the safe direction on a shared classroom computer.

**It is a notice, not a control.** It does not stop a determined child typing their name, and it is not a substitute for supervision or consent. It is the "reasonable steps" that OpenAI's developer terms ask for, and it should be described as exactly that.

---

## 4. The legacy direct drawer — **hidden, and this matters for the paper**

There is a second, older generation path: a manual drawer with a labelled **Prompt** field, a **style menu** (Digital Art, Comic Book, Fantasy Art, Photographic, Cinematic), a **draft/final quality** toggle, and a **history strip** where every attempt is preserved with the exact words that produced it.

**It is not reachable.** The container is `<div id="ai-manual-ui" style="display:none">`. The history strip is likewise `display:none`. The code is retained and still wired; the UI is invisible.

This is the single most consequential divergence between the paper and the system, because the paper's argument leans on it:

- §3 resolves the scribe tension by saying *"the direct prompt drawer remains the unmediated path, living inside the same product."* **In the shipped build there is no unmediated path.** Pip is the only way to get a picture.
- §4.1 describes the style menu as *"the studio's one explicit aesthetic control."* A child cannot see it. In Pip mode, style is expressed conversationally and carried forward by the system prompt — which is a *different* mechanism and worth describing as such.
- §5's attribution argument — *"a child can re-run an unchanged description and watch what persists and what varies"* — describes UI a child cannot use. The image bank shows past pictures but offers no re-run.

**Decide before you revise:** either un-hide the drawer so the deployed system matches the paper, or rewrite §3, §4.1 and §5 to describe a Pip-only system. Both are defensible; the current state is that the paper describes a system the children cannot reach.

(Note that the two paths capture *different* research data — see §6.)

---

## 5. Teacher Mode

### 5.1 The problem it solves, and the constraint

A teacher needs each child's work on their own computer. A browser cannot reach into another computer — a student's browser is not a server, nothing can connect *to* it, and the two machines are rarely online simultaneously. Some intermediary is unavoidable.

The design makes that intermediary a **dead-drop, not a database**: the child's browser encrypts the story *before* it leaves the machine, and the relay stores bytes it holds no key to open.

### 5.2 Teams, and the key derivation

A **team is one computer**, not one child. Children are anonymous; the team *is* the identity. The teacher creates a team and gets back a name and a secret code to tape to that machine.

- **Team name:** `adjective-animal` (e.g. `brave-otter`), from lists of 20 and 20 → 400 combinations (~8.6 bits). It is a label, not a secret.
- **Secret code:** `WORD-WORD-WORD-DDDD` from a 30-word list plus four digits → 30³ × 10⁴ = 2.7 × 10⁸ combinations ≈ **28.0 bits**. Generated with `crypto.getRandomValues`, never chosen by a child.

> ⚠ **A code comment in `teacher.html` claims "~35 bits of entropy." That is wrong; the true figure is ≈28.0 bits.** Do not repeat the 35-bit figure in the paper. To reach 35 bits with this format you would need roughly a 150-word list.

Both the teacher and the student derive everything from `(team name, secret code)` alone — **no key is ever exchanged**:

```
masterKey = PBKDF2-HMAC-SHA256(secretCode, salt = SHA-256("storysprout-v1|" + normalisedTeamName),
                               600,000 iterations) → 256 bits
encKey    = HKDF(masterKey, info="storysprout-enc-v1")   → AES-GCM-256, NON-EXTRACTABLE, never leaves the browser
authToken = HKDF(masterKey, info="storysprout-auth-v1")  → 64 hex chars, sent to the relay
blobKey   = HKDF(masterKey, info="storysprout-blob-v1")  → HMAC-SHA-256 key for image ids
objectKey = SHA-256(authToken)                            → computed BY THE WORKER; the storage prefix
```

The worker sees `authToken` and nothing else. It cannot derive `encKey` from it (different HKDF branch, one-way). It computes the storage prefix itself, so a client never chooses where its data lands and a bucket listing yields no usable tokens.

Team names are normalised (trim → collapse whitespace → lowercase) before derivation, so `"Table 3"` and `"table 3 "` produce the same keys. Without that, a trailing space silently makes a child's work unrecoverable.

**Honest limit, and it belongs in the paper:** the secret code *is* the security model. 28 bits is solid against a curious classmate; it is *not* solid against a determined attacker who already holds the ciphertext, because no iteration count fixes a small search space. Guessing a code still cannot let you *read* a story without breaking the KDF — but it would let you *overwrite* one, which is why the relay keeps the last 30 revisions.

### 5.3 Content-addressing: why 50 MB syncs in ~1.5 KB

Because images are base64-inlined in every page *and* duplicated in `aiHistory`, a story is ~50 MB. Re-uploading that every few minutes, per device, over school wifi is a non-starter.

So each image is **hashed (SHA-256 over the decoded bytes), uploaded exactly once, and referenced by hash** (`sprout:<hash>`) inside the story. The recurring payload is the story skeleton — gzipped and encrypted — measured at **~1.5 KB**, roughly **4,000× smaller**. Because Fabric stores the *same* data-URL string in the canvas and in `aiHistory`, hashing the decoded bytes collapses that duplication into one blob for free.

On the wire, an image's id is **`HMAC(blobKey, hash)`**, not the raw content hash. This matters: a raw hash would let anyone who can list the bucket test whether a given team holds a specific image, and correlate the same image across two teams. The HMAC makes ids team-specific and meaningless without the code.

**Thumbnails are deliberately left inline** (JPEG, quality 0.25, 0.18× scale — 3–8 KB each). They are regenerated on every save, so their hashes churn and would never dedupe; keeping them inline also lets the teacher's dashboard render with zero extra fetches.

The round-trip is verified byte-identical by `sprout-sync-test.html` — open it and click *Run tests*.

### 5.4 The sync protocol

**Blobs upload first; the manifest is published last.** The manifest is the single atomic commit point, so a teacher pulling mid-write sees either the old story or the new one, never a torn one referencing images that don't exist.

Concurrency is handled by a **server-assigned revision counter** with compare-and-set: the client sends the revision it is based on, and a mismatch returns **409 Conflict**. Client clocks are never trusted for ordering — a Chromebook with the wrong date would otherwise poison a team's history permanently.

| Timing | Value |
|---|---|
| Local autosave | 5 s after a change |
| Sync push debounce | 12 s |
| Push on tab blur / hide / close | immediate |
| Teacher check interval | 30 s (paused while the tab is hidden) |

A push whose content hash matches the last successful one **sends nothing at all** — so a child leaning on the Send button costs zero requests.

**Closing the tab:** the manifest goes out with `keepalive` (capped at 60,000 bytes) so a last text edit survives the page being torn down. But a closing page **cannot** reliably upload megabytes of *new images* — the browser kills those requests — and publishing a manifest whose images never arrived would leave the teacher permanently unable to open the story. So in that case it sends nothing and marks the work unsent; the next sign-in pushes it before the child touches anything. Nothing is lost either way, because the work is already saved locally.

### 5.5 Identity on a shared computer

Classroom computers get passed between groups, so **a class computer asks for the team name and secret code on every load.** The team is never remembered.

The corresponding data-protection rule: the local autosave is tagged with the team that made it. If a *different* team signs in, the local copy is **wiped, not offered** — otherwise Team B would be shown Team A's story, which is a straightforward leak of one group's work to another. A brand-new team gets a blank page.

Derived keys are deliberately **not cached** on a class computer.

### 5.6 What lands on the teacher's disk

```
<class folder>/
├── teacher.json          ← teams + secret codes, in PLAINTEXT. This is the master key.
├── class.json            ← per-team collection state
├── images/<sha256>.<ext> ← decrypted images, content-addressed, shared across all teams
└── teams/<team-name>/
    ├── latest.json       ← the full story, images inlined — opens directly in the workshop
    └── snapshots/<ISO timestamp>.json   ← the ref-form manifest, a few KB each
```

The asymmetry is deliberate. `latest.json` is fat and self-contained so a teacher can just open it. Snapshots are thin and share the `images/` folder — writing the full 50 MB story every few minutes would be gigabytes a day.

> ⚠ **`teacher.json` holds every team's secret code in plaintext, and those codes are the only keys that exist.** If that file is lost, every team's encrypted work becomes permanently unreadable — by the teacher, by the developers, by Cloudflare. That is the exact price of the zero-knowledge property. **It must be backed up, and it must be described honestly in the paper.**

### 5.7 Teacher authentication and deletion

Two independent paths, so a broken OAuth config cannot lock a teacher out mid-lesson:
- **Google sign-in** (GIS), verified in the worker against Google's JWKS with native WebCrypto — signature, `exp`, `iat` (±300 s skew), `aud`, `iss`, `email_verified` — then checked against an email allowlist.
- **A shared passphrase**, compared in constant time.

Only two routes require teacher credentials: **creating** a team and **deleting** one. Everything else authenticates with the team token alone; the relay cannot tell a teacher from a student, and does not need to.

**Deletion** is teacher-only on purpose — a child knows their own team's code, and "delete everything we made" must not be one mistyped click away for a seven-year-old. It requires typing the team name, erases the relay first (so a failure changes nothing locally), then the disk, then prunes images no surviving team references. **This is the mechanism that makes a parental deletion request satisfiable.**

---

## 6. The research record — read this carefully

This section supersedes `RESEARCH_DATA.md` entirely.

### 6.1 What is captured now (schema **v6**)

| Field | What it holds |
|---|---|
| `pipConversation` | **The child's own words, verbatim, with timestamps.** Every turn, including Pip's greeting. |
| `promptLog` | One record per generation attempt. **Never capped.** |
| `aiHistory` | The image cache. **Capped at 20.** Newest-first. |
| `storyText` | The story panel's lines (from Bubble, or typed). |
| `session` | `{startedAt, savedAt, totalSlides}` |
| `slides[]` | Page canvases + thumbnails |

A `promptLog` record:

```json
{
  "historyId": "ai_1752...",
  "at": "2026-07-14T10:15:30.000Z",
  "source": "pip" | "manual",
  "childWords": "make the dog fluffy and put him in the snow",   // what the CHILD said
  "imagePrompt": "A fluffy white dog standing in a snowy park...", // what the MODEL wrote
  "turnIndex": 7,          // index into pipConversation
  "settings": {},
  "parentId": null,
  "actions": [ { "type": "added_to_canvas", "at": "...", "slideIdx": 0 } ]
}
```

**The distinction between `childWords` and `imagePrompt` is the heart of the research data.** In the Pip flow the child never writes the image prompt: they converse, and `gpt-4o-mini` authors the prompt that actually reaches the image model. Both are now recorded, so they can be **compared rather than conflated** — which is arguably a more interesting dataset than either alone.

The research log is deliberately **separate from the image cache**, and never capped. They were one array, limited to 20 *because each entry carries a 2–3 MB image*. Prompts are tiny. A child who makes 40 attempts now keeps all 40 prompts — including the earliest and least refined, which are exactly what a progression study needs.

Two actions are logged, both with a timestamp and page index: `added_to_canvas` and `removed_from_canvas`. They fire on Pip's approve button, on image-bank click, on image-bank drag, and on deletion.

Clearing the picture strip does **not** erase the research record. Only starting a genuinely new story resets it.

### 6.2 What was captured before 14 July 2026 — and why any existing data is compromised

Everything in §6.1 is **new**. If you have data from before commit `c168415`, it has these gaps, and they cannot be retrofitted:

| `RESEARCH_DATA.md` claimed | What the code actually did |
|---|---|
| `prompt` = *"the text prompt the student wrote"* | **The model's rewritten prompt.** The child's words were never saved anywhere. |
| The conversation is available | **`pipMessages` was never serialised.** It died on every page load. |
| `parentId` links refinement chains | **Always `null`** in the Pip flow. |
| `settings.style_preset` / `quality` | **Always `{}`** in the Pip flow (those come from the hidden legacy drawer). |
| `actions[]` records add/remove | **Never fired.** Pip-added images carried no `historyId`, and the logger is gated on it. |
| *"Number of `aiHistory` items shows total generation attempts"* | **Capped at 20.** The earliest generations were silently discarded. |

The doc's analyses **§1 (prompt progression), §2 (iteration patterns), §3 (style experimentation) and §4 (selection & revision behaviour) were not supported by the data the code produced.** If any of your pilot sessions used Pip, treat those files as unusable for those analyses.

`aiHistory` is stored **newest-first** (`unshift`). Any analysis assuming chronological array order is reversed.

### 6.3 Two remaining honest limits

- **`aiHistory` is still capped at 20 images.** That is the *picture* cache, not the record. If you want every image preserved for analysis, the story file will grow to hundreds of megabytes; the prompts are all kept regardless.
- **`duplicateSelected` does not copy `historyId`.** A duplicated AI image loses its link to the research record.

---

## 7. The worker

One Cloudflare Worker serves both roles. Deployed by **pasting the file into the dashboard** — no wrangler, no bundler, so it must stay a single dependency-free file. **The repo copy and the deployed copy drift easily; the repo is the source of truth.**

| Route | Purpose |
|---|---|
| `POST /chat` | Pip's turn. `gpt-4o-mini`. |
| `POST /image` | Text-to-image. `gpt-image-2`. |
| `POST /image-edit` | Image-conditioned revision. `gpt-image-2`. |
| `POST /sync/register` | **Teacher only.** Creates a team. The one gate stopping the relay being open storage. |
| `POST /sync/delete` | **Teacher only.** Erases a team and everything in it. |
| `GET /sync/state` | Cheap poll: revision + timestamp. |
| `GET · PUT /sync/manifest` | The encrypted story. `PUT` is compare-and-set; 409 on conflict. |
| `POST /sync/blobs/check` | Which images are missing — keeps a routine sync to two requests. |
| `GET · PUT /sync/blob/<id>` | An encrypted image. Immutable. |
| `GET · PUT /sync/assign` | The teacher's assignment. |

An unknown path **404s**. (It used to fall through to `/chat`, which meant a typo'd path silently called OpenAI and burned credit.)

Rate limits, all in-memory sliding windows:

| Limiter | Key | Budget |
|---|---|---|
| AI routes | client IP | 40 / 60 s |
| Sync routes | **the team**, not the IP | 240 / 60 s |
| Register + delete | client IP | 10 / 60 s |

Sync is keyed on the team deliberately: an entire classroom shares one school NAT address, and a per-IP budget would have throttled the whole class on day one.

Storage limits: image ≤ 8 MB, manifest ≤ 4 MB, 500 images per team, last **30** revisions retained.

**Environment:** `OPENAI_API_KEY` (secret), `SPROUT_BUCKET` (R2 binding), and for teacher sign-in either `GOOGLE_CLIENT_ID` + `ALLOWED_TEACHER_EMAILS`, or `TEACHER_PASSPHRASE` (secret), or both.

---

## 8. Safety and privacy

### 8.1 Content safety is layered

1. **Pip's system prompt** scopes the conversation to illustration, refuses age-inappropriate requests in-fiction with an offered alternative, and never asks for or repeats personal information.
2. **A server-side safety clause** is appended to *every* image request, after truncation, so the client cannot remove it: *"The image must be wholesome and appropriate for young children: no violence, gore, weapons, blood, scary or frightening imagery, and no adult content."*
3. **It is deliberately silent about aesthetics.** A child asking for watercolour or comic-book style gets exactly that. The guardrail constrains *what may be depicted*, never *how it looks*. This is the same allocation as §3 of the paper, made from the other side.
4. **OpenAI's own moderation refusals** are caught (an HTTP 400 matching `/safety|moderation|content[_ ]?policy|not allowed|rejected/i`) and translated into a soft, child-readable redirect: *"Hmm, I can't draw that one. Let's try a different picture."*
5. **All use is facilitated and in-person.**

### 8.2 What leaves the child's machine

**Nothing, to anyone but us — and only when a picture is made.**

The child's browser used to fetch the Nunito webfont from `fonts.googleapis.com` and Fabric.js from `cdnjs.cloudflare.com` on *every page load*, handing the child's **IP address and user-agent to Google and to Cloudflare** before the child had done anything. Both are now self-hosted in `vendor/`. This is what makes the paper's "no telemetry" claim true rather than aspirational.

| Data | Destination | Why |
|---|---|---|
| Conversation text + image prompts | **OpenAI** (via our worker) | This is the product. Unavoidable. |
| Encrypted story + images | **Cloudflare R2** | Only in class mode. Zero-knowledge — we hold no key. |
| Client IP | Our worker, in memory, 60 s | Rate limiting. No durable log. |
| Microphone audio | **Nowhere.** On-device only. | §3.6 |
| — | ~~Google Fonts~~ | Removed |
| — | ~~cdnjs~~ | Removed |
| — | ~~`sprout_device_id`~~ | Removed — a persistent identifier that nothing ever read |
| — | ~~teacher's email on R2~~ | Removed — the relay now holds no identifying data at all |

### 8.3 COPPA posture — what is done, and what is not

**This is not legal advice.** It is an accurate inventory so counsel can assess it. The paper's existing framing — *"a data-minimization measure, not a claim of exemption or compliance"* — is correct and should be kept verbatim.

The amended COPPA Rule has been in force since **23 June 2025**, with full compliance required from **22 April 2026**. It expanded "personal information" to explicitly include **voice data**, and now requires **separate parental consent for third-party disclosure**, a **written data retention policy**, and a **written information security program**.

**Done (engineering):**
- No child accounts. No child sign-in of any kind.
- No third-party requests from the child's browser.
- No persistent identifiers stored on the child's device.
- Voice recognition on-device, failing closed rather than falling back.
- Zero-knowledge relay — the operator cannot read stored work even if compelled.
- `store: false` on chat completions.
- A safety notice before a child can reach Pip.
- Deletion actually implemented (team deletion wipes relay *and* disk).

**Outstanding (contractual and procedural — not engineering):**

1. **Zero Data Retention from OpenAI.** Their developer terms say you should *not* process under-13 personal data without it. It is **not self-serve** — OpenAI grants it at the organisation level via sales/support. **Get it in writing whether it covers `/v1/images/generations` and `/v1/images/edits`, not just chat** — image endpoints can have different retention rules, and the images are the product.
2. **Consent that actually covers this system.** Any consent obtained before the Pip integration was for a different system. The amended Rule requires *separate* consent for the OpenAI disclosure.
3. **Threshold question:** does COPPA even apply? It is enforced under the FTC Act, which generally reaches entities organised for profit. A nonprofit/academic operator may fall outside it — but that is fact-specific, it evaporates on commercialisation, and IRB obligations are independent regardless.
4. **The school-consent route may not be available.** FTC guidance lets *schools* consent on parents' behalf. A community after-school programme is likely not a school — which would mean parental consent per family.
5. **Written retention policy and security program.** Now mandatory.

Two residual risks no code change removes: children can type their own name into free text (Pip is forbidden to *solicit* it, but cannot prevent it being volunteered), and children can import **any local image** — including a photo of themselves — onto the canvas. That image stays local and syncs encrypted to the teacher; it is **never** sent to OpenAI.

---

## 9. Corrections to the paper

Claim by claim. **This is the section to work from when revising.**

| § | The paper says | The code does |
|---|---|---|
| Abstract, §3.4, §4.4, §7 | *"no accounts and no server-side storage of children's work"*, *"no cloud"* | **False.** Teacher Mode stores every story on Cloudflare R2, and the teacher signs in with Google. The defensible claim is **"no *readable* server-side storage"** — a zero-knowledge relay. The spirit survives; the sentences do not. |
| §3, §4.1, §5 | *"the direct prompt drawer remains the unmediated path"* | **The direct drawer is hidden** (`display:none`). Pip is the only reachable path. Your resolution of the scribe tension currently points at UI a child cannot use. |
| §4.1 | The style menu is *"the studio's one explicit aesthetic control"* | It lives in the hidden drawer. In Pip mode, style is conversational and carried forward by the system prompt — a different mechanism. |
| §4.1, §5 | *"Every result lands in a visible history strip"*; a child can *"re-run an unchanged description"* | The history strip is `display:none`. The image bank shows past pictures but offers **no re-run**. §5's attribution argument describes an affordance that does not exist. |
| §4.1 | *"the platform appends only that chosen style, a fixed landscape-composition hint, and the safety constraint"* | True of the **legacy** path only. Pip sends **no style suffix and no landscape hint** — only the safety clause. (Landscape happens because the API default is 1536×1024.) |
| §4.3 | *"three routes"*; *"stores nothing beyond ephemeral in-memory rate-limit counters"* | **Three AI routes plus ten `/sync/*` routes.** The worker writes to R2. |
| §4.3 | *"rate-limits per client IP"* | True for AI routes. **Sync is rate-limited per team**, because a classroom shares one NAT IP. |
| §4.4 | The project file contains *"prompts … settings … revision links, and a log of additions and removals"* | **Aspirational until 14 July 2026.** `parentId` was always null, `settings` always `{}`, the action log never fired, and the recorded "prompt" was the *model's* rewrite. Now true (v6) — but **only going forward.** |
| §4.1, §6, Acknowledgments | Voice input, framed around fidelity | Until 14 July 2026 the microphone **streamed children's voice audio to Google.** Now on-device and failing closed. Voice is explicitly personal information under the amended Rule. Your Ethics statement needs this. |
| §7 | *"no telemetry"* | Was **false** — the child's page fetched Google Fonts and cdnjs on every load, leaking IP to two third parties. Now true. |
| §5 | *"gpt-image-2 at the time of writing"* | ✅ **Correct.** |
| §4.2 | The `{reply, ready, image_prompt, remove_old}` schema and the three rules | ✅ **Correct.** `PIP_SCOPE.md` is in sync with the code — the one document that is. |
| — | (code comment) *"~35 bits of entropy"* | **≈28.0 bits.** Do not repeat the 35-bit figure. |

### Documents to disregard

- **`HANDOFF.md`** — describes a Stability AI system that no longer exists: wrong provider, wrong worker URL, wrong secret name, wrong routes, wrong parameters. No mention of Pip, Teacher Mode, or the crypto.
- **`STYLE_CONSISTENCY.md`** — stale at the premise: Stability seeds, negative prompts, and `style_preset` values that OpenAI does not have. Its *goal* (style consistency across a book) is now solved by a different mechanism (§3.3).
- **`RESEARCH_DATA.md`** — superseded by §6. Its privacy note (*"not sent to any server"*) is false twice over.

---

## 10. Data map

For counsel. Every field, every destination.

| Data | Origin | Where it goes | Retention |
|---|---|---|---|
| Chat turns (`pipConversation`) | Child types or dictates | → OpenAI (as context) · → story file · → relay (encrypted) · → teacher's disk | Teacher's disk: indefinite. Relay: until lifecycle expiry. |
| `image_prompt` | **Authored by `gpt-4o-mini`** | → OpenAI image endpoint · → story file | As above |
| Generated images | OpenAI | → canvas · → story file · → relay (encrypted) · → teacher's disk | As above |
| Imported images | Child's own files | → canvas · → story file · → relay (encrypted) · → teacher's disk. **Never sent to OpenAI.** | As above |
| Story text, page content | Child | Same as above | As above |
| Microphone audio | Child's voice | **Nowhere — on-device only** | Not retained |
| Client IP | Network | Worker memory only | 60 seconds |
| Team name + secret code | Generated by teacher | `teacher.json` on the teacher's disk, **plaintext** | Until the teacher deletes the team |
| Teacher's email | Google sign-in | Verified in the worker, **then discarded** | Not stored |
| Child's name, age, school | **Never collected** | — | — |

---

## Appendix A — draft data retention policy

*Starting point for counsel to redline. Not legal advice.*

1. **Children's work** (stories, prompts, conversations, images) is retained **on the supervising adult's computer** for the duration of the programme and for no longer than is necessary for the educational and research purposes for which it was collected. At the end of each programme cycle, the supervising adult deletes the class folder unless a family has consented to retention for research.
2. **The relay (Cloudflare R2)** retains only encrypted objects the operator cannot read. A bucket lifecycle rule expires all objects after **30 days**. The relay is a transport buffer, not a store of record.
3. **The relay retains no identifying data** — no names, no emails, no device identifiers. Only ciphertext, a revision counter, and creation timestamps.
4. **OpenAI** retains API content per its own terms. **Zero Data Retention must be obtained before the system is used with children.**
5. **Deletion on request.** A parent may request deletion of their child's work. The teacher deletes the team, which erases the relay copy and the local copy, and prunes the images no other team references. This is implemented and tested.
6. **Microphone audio is never retained**, by us or by any third party — recognition is on-device.

## Appendix B — draft information security program

*Starting point for counsel to redline. Not legal advice.*

- **Encryption in transit:** all traffic is HTTPS.
- **Encryption at rest:** children's work is encrypted in the child's browser (AES-GCM-256) with a key derived by PBKDF2 (600,000 iterations) → HKDF from a generated secret code. **The operator never holds the key.**
- **Key custody:** the only copies of the keys are the secret codes in `teacher.json` on the supervising adult's computer. Loss of that file makes the work permanently unreadable — this is an accepted and documented consequence of the zero-knowledge design.
- **Access control:** creating and deleting teams requires a verified Google account on an allowlist, or a shared passphrase. Reading a team's work requires the team's secret code.
- **API keys:** the OpenAI key exists only as an encrypted secret in the Cloudflare Worker and never reaches any browser.
- **Abuse controls:** per-IP rate limiting on AI routes, per-team on sync, tight per-IP limits on team creation and deletion.
- **Data minimisation:** no child accounts, no persistent identifiers, no third-party assets, no telemetry.
- **Integrity:** revision history (last 30) allows recovery from a malicious or accidental overwrite.
- **Known residual risks:** a 28-bit team code is not proof against a determined attacker holding the ciphertext; children can volunteer personal information in free text; `teacher.json` is unencrypted key escrow on the teacher's disk.

---

## Appendix C — known limitations and dead code

- `S.imgMap` and `S.dirHandle` are **dead** — always `{}` / `null`. Vestiges of a removed folder-based scheme.
- `SAVE_KEY`, `STORY_FILE`, `addImageFromUrl()` are declared and never used.
- The IndexedDB key `storysketch_fileHandle` is written and **never read** — the file handle does not survive a reload.
- `duplicateSelected` does not copy `historyId`, so a duplicated AI image loses its research link.
- The manifest compare-and-set is a read-then-write against R2 with no conditional put, so two simultaneous pushes at the same revision could in principle both succeed. In practice a team is one device and pushes are single-flighted.
- `PUT /sync/assign` requires only the team token, despite a comment claiming it is teacher-only. Any holder of the team code can write the assignment.
- Teacher Mode requires **Chrome or Edge** — Firefox and Safari do not implement the File System Access API.
- `sprout-sync.js` is shared byte-for-byte by both pages. Changing any crypto constant requires bumping `VERSION`, both pages' `REQUIRE_SYNC_VERSION`, **and** the `?v=` on both script tags — together. A stale cached copy would derive different keys and fail **silently**. Both pages assert the version on boot to turn that into a loud error.
