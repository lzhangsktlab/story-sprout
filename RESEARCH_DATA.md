# Project-File Schema — a codebook for the local story file

**This is a codebook, not a data-collection notice.** It describes the fields inside the JSON
**story file** that StorySprout Studio writes, so that a file can be read correctly. It does not
describe anything the platform gathers.

**Nothing here is collected by the platform.** The story file is written to and lives on the
**local device** — the child's own machine, or, in class mode, the **supervising teacher's
computer** (see [`PAPER_REFERENCE.md`](PAPER_REFERENCE.md) §5–§6). The platform transmits none of
it to a research server and retains no copy. Consistent with the paper's §5, **no child data is
collected through the platform, by design.**

Research analysis, when it happens at all, is performed **only on files that consenting families
voluntarily contribute after ethics review**, per the paper's §7. This codebook exists so that such
a contributed file can be interpreted — including the field that tells a current record apart from a
pre-Pip one.

**A framing point the schema makes concrete: children do not write the image prompt.** They
*describe* a scene in their own words; **Pip** (the model) *composes* the prompt that reaches the
image model. The file stores both, as **separate strings** — the child's words (`childWords`, and
the full `pipConversation` transcript) and the model's composed prompt (`imagePrompt`). That split
is the point of the record.

---

## File structure (v6)

`v6` is the current schema; **`v5` is the legacy, pre-Pip schema** and still loads (see the bottom
of this document).

```json
{
  "v": 6,
  "title": "My Cat Story",
  "saved": 1712400000000,
  "session": { "startedAt": "2026-07-14T10:00:00.000Z", "savedAt": "…", "totalSlides": 3 },
  "storyText": ["Line 1", "Line 2", "…"],

  "pipConversation": [ /* the child ↔ Pip transcript, verbatim */ ],
  "promptLog":       [ /* the research record — one entry per attempt; uncapped */ ],
  "aiHistory":       [ /* the image cache — capped at 20, newest-first */ ],

  "slides": [ /* { json, thumb, imgMap } per page */ ],
  "imgMap": {}   // dead vestige — always {}; ignore
}
```

Three arrays carry the research signal, and they are deliberately different things:

| Array | What it is | Capped? | Use it for |
|---|---|---|---|
| `pipConversation` | The child's own words, in context, timestamped | No | What the child actually said |
| `promptLog` | One record per generation attempt (+ safety-block events) | **No** | Counting/analyzing attempts |
| `aiHistory` | The image cache (carries the base64 images) | **Yes — 20, newest-first** | Displaying pictures, **not** counting attempts |

> ⚠️ `aiHistory` is capped at 20 and stored **newest-first**. It is **not** the attempt counter — a
> child who makes 40 attempts keeps all 40 in `promptLog` but only the last 20 images here. Any
> analysis that counts or orders attempts must read `promptLog`, not `aiHistory`.

---

## `promptLog` — the research record

Uncapped, because each entry is small (no image). Two kinds of record share the array.

### 1. A generation attempt

```json
{
  "historyId": "ai_1752480000_x3k9",
  "at": "2026-07-14T10:15:30.000Z",
  "source": "pip",
  "childWords":  "make the dog fluffy and put him in the snow",     // what the CHILD said
  "imagePrompt": "A fluffy white dog standing in a snowy park…",    // what the MODEL composed
  "turnIndex": 7,
  "settings": {},
  "parentId": null,
  "actions": [ { "type": "added_to_canvas", "at": "…", "slideIdx": 0 } ]
}
```

| Field | Type | Meaning |
|---|---|---|
| `historyId` | string | Links this attempt to its `aiHistory` image (if still cached) |
| `at` | ISO 8601 | When the attempt was made |
| `source` | `"pip"` \| `"manual"` | **Era discriminator.** `pip` = the current conversational flow. `manual` = a pre-Pip record from the removed manual drawer — **current code never writes it** (the producer was deleted); it appears only in older contributed files. |
| `childWords` | string \| **null** | The child's own words, verbatim. **`null` on `manual`/pre-Pip records**, where the child *did* type the prompt directly and `imagePrompt` already holds their words. |
| `imagePrompt` | string | The composed scene description actually sent to the image model — **the model's words**, in the Pip flow. |
| `turnIndex` | int \| null | Index into `pipConversation`, so a whole exchange can be replayed around the attempt. |
| `settings` | object | **Legacy-era.** `{}` from current code; older files may carry `{style_preset, quality}` (see legacy section). |
| `parentId` | string \| null | `historyId` of the image being refined; `null` for a first attempt. |
| `actions` | array | Add/remove events for the resulting image (mirror of `aiHistory[].actions`). |

**The `childWords` ↔ `imagePrompt` split is the heart of the record.** It is what lets a reader
verify, per attempt, that the child's words and the composed prompt are saved as *separate strings*
— the trace the paper's Table 1 depends on — and measure how far one departs from the other. (The
held-out audit under `scribe_audit_v3_heldout_out/` is exactly that measurement, run adversarially.)

### 2. A safety-block event

When the pre-transmission filter blocks a message that self-identifies the child, the record notes
**that** it happened and **what category** — **never the words themselves**:

```json
{ "at": "…", "type": "blocked_personal_info", "category": "an address", "source": "pip" }
```

Retaining the personal information in order to note that it was refused would defeat the purpose.

---

## `pipConversation` — the child's transcript

```json
{ "role": "user", "content": "a fluffy dog in the snow", "at": "2026-07-14T10:15:12.000Z" }
```

`role` is `user` (the child) or `assistant` (Pip), `content` is the message verbatim, `at` is the
timestamp. This is the child's own language, in order, including Pip's greeting — the primary
artifact for studying how a child learns to **describe and refine a scene**. Before v6 it was never
serialized and died on every page load.

## `aiHistory` — the image cache

```json
{
  "historyId": "ai_1752480000_x3k9",
  "prompt": "A fluffy white dog standing in a snowy park…",   // the composed prompt (model's words)
  "timestamp": "2026-07-14T10:15:30.000Z",
  "settings": {},
  "parentId": null,
  "actions": [ /* added_to_canvas / removed_from_canvas, each { type, at, slideIdx } */ ],
  "dataUrl": "data:image/png;base64,…"
}
```

Holds the rendered images (2–3 MB each), which is why it is capped at 20. `prompt` here is the
**model's** composed prompt — to recover the child's words for an attempt, join on `historyId` to
`promptLog` and read `childWords`.

**Action types:** `added_to_canvas` (the child placed the picture on a page) and
`removed_from_canvas` (removed it). Each carries `at` and `slideIdx` (0-indexed). Clearing the
picture strip does not erase these; only starting a new story resets the record.

---

## What this supports

Because the child's words and the model's words are stored separately, a contributed file supports:

- **Describe-and-refine progression** — how a child's *descriptions* (`pipConversation`,
  `childWords`) grow and sharpen across a session.
- **The scribe trace** — per attempt, how the composed `imagePrompt` departs from the child's
  `childWords` (fidelity, additions, omissions).
- **Selection & revision** — via `actions`: which pictures were placed, removed, reused, or never
  used; time from attempt (`at`) to placement.
- **Attempt counts and chains** — from `promptLog` (uncapped) and `parentId` refinement links.

## Privacy

- The story file is **local**: on the child's device, or synced **encrypted** to the supervising
  teacher's computer in class mode. The platform keeps no readable copy (`PAPER_REFERENCE.md` §6).
- **No names, ages, schools, or accounts** are recorded. A child who self-identifies is **blocked
  before transmission**, and only the *category* of block is logged — never the text.
- Any research use is on **voluntarily contributed** files, under the ethics protocol (paper §7).
  Nothing is gathered by the platform for research.

---

## Legacy: the v5 schema (pre-Pip)

Older files declare `"v": 5` and predate Pip. They still open in the current app. Their records
differ:

- The single **`prompt`** field held the text the child typed *directly* into the manual drawer —
  there was no `childWords`/`imagePrompt` split, because in that flow the child *was* the author of
  the prompt.
- **`settings.style_preset`** (digital-art, comic-book, …) and **`settings.quality`** (draft/final)
  came from the drawer's controls. Current code **can read these but never writes them** — the
  drawer that produced them has been removed.
- There was **no `pipConversation`** and **no `promptLog`**; `aiHistory` was the only record, and
  its 20-item cap silently discarded a child's earliest attempts.

In a mixed set of contributed files, **`source` is the discriminator**: `"pip"` for current-era
records, `"manual"` (or a v5 file with no `source`) for pre-Pip ones. Analyses that assume the
`childWords`/`imagePrompt` split will find it only on Pip-era records.
