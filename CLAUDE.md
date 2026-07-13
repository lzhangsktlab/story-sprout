# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Storybook Workshop** — a client-side web app where children create multi-slide illustrated stories with **Pip**, a conversational AI illustrator. No build step, no server, no framework.

It also has a **Teacher Mode**: a teacher collects every child's work onto their own computer automatically, without any child ever creating an account.

## The files that matter

| File | What it is |
|---|---|
| `workshop-plugin.html` | **The app.** ~3,900 lines, single file. This is what you almost always want. |
| `teacher.html` | Teacher Mode dashboard — create teams, collect student work. |
| `sprout-sync.js` | Shared crypto + content-addressing + relay client. Loaded by **both** pages. |
| `sprout-sync-test.html` | Test harness for the above. Open it, click *Run tests*. |
| `cloudflare-worker/pip-worker.js` | The OpenAI proxy **and** the sync relay. |
| `workshop.html` | **Legacy.** An earlier standalone version (Stability AI). Not maintained — don't edit it unless asked. |

⚠️ **`workshop.html` is not the app.** Earlier versions of this file said it was. If a task mentions "the workshop", it means `workshop-plugin.html`.

## Running

Open `workshop-plugin.html` directly in Chrome or Edge. No build tools, no dependencies.

`teacher.html` will **not** work over `file://` — Google sign-in and `showDirectoryPicker()` both refuse an opaque origin. Serve it over localhost:

```bash
python -m http.server 8000     # then http://localhost:8000/teacher.html
```

The Worker's CORS allowlist already covers `localhost` and `file://`.

## Architecture

Browser app → **Cloudflare Worker** (`https://storysprout-pip.jackwangxyw.workers.dev`) → OpenAI. The API key lives only in the Worker.

- **Chat:** `gpt-4o-mini` · **Images:** `gpt-image-2`
- Worker routes: `/chat`, `/image`, `/image-edit`, and `/sync/*` for Teacher Mode.
- The Worker is deployed by **pasting it into the Cloudflare dashboard** — no wrangler, no bundler, so it must stay a single dependency-free file. The repo copy and the deployed copy drift easily; the repo is the source of truth.

### Global state (`workshop-plugin.html`)

All app state is in the `S` object:
- `S.slides[]` — `{json, thumb}` per page. `json` is a **string** of serialized Fabric JSON.
- `S.cur` — current page index
- `S.history[]` / `S.redo[]` — per-page undo/redo stacks (max 50)
- `S.canvas` — the Fabric.js canvas
- `S.dirty` — unsaved-changes flag; drives autosave

⚠️ `S.slides`, `S.history` and `S.redo` are **parallel arrays indexed by page**, and `S.cur` points into them. Anything that reorders or removes a page must move all three in step (see `movePage()`).

⚠️ `S.imgMap` and `S.dirHandle` are **dead** — always `{}` / `null`. Vestiges of a removed folder-based scheme. Don't build on them.

### Major subsystems

| Area | Key functions |
|---|---|
| Canvas | `initCanvas()`, `fitCanvas()`, `bindCanvas()` |
| Pages | `saveCurrentSlide()`, `loadSlide()`, `addSlide()`, `deleteSlide()`, `movePage()`, `renderSlideThumbs()` |
| History | `pushHistory()`, `undo()`, `redo()` |
| Elements | `addTextBox()`, `addShape()`, `addImageSrc()`, `deleteSelected()`, `duplicateSelected()` |
| Pip | `pipSend()`, `pipGenerate()` — talks to the Worker |
| Persistence | `buildStoryJson()` / `loadStoryData()` — the single choke point for the story format |
| Teacher sync | `syncPush()`, `syncRestore()`, `initTeacherMode()` |

⚠️ **`canvas.add()` fires `object:added` synchronously**, which snapshots history and regenerates the thumbnail. **Position an object BEFORE adding it**, or the recorded state will hold the pre-move position while the canvas shows the post-move one — undo then faithfully restores the wrong thing. This was a real bug in `addShape()`.

### Story format

`buildStoryJson()` produces `{v: 5, title, saved, session, imgMap, storyText, aiHistory, slides[]}`.

Images are **base64 data URLs inlined into every page's Fabric JSON, and duplicated again in `aiHistory[].dataUrl`**. A six-page story is therefore ~50MB. This matters enormously for sync — see below.

### Teacher Mode

Work is encrypted **in the child's browser** before it is sent. Cloudflare R2 stores bytes it holds no key to open. The only readable copy lives on the teacher's disk.

```
masterKey = PBKDF2(secret code, salt = SHA256("storysprout-v1|" + team), 600k)
encKey    = HKDF(master, "enc")   never leaves the browser
authToken = HKDF(master, "auth")  proves team membership; cannot be reversed into encKey
blobKey   = HKDF(master, "blob")  HMACs image ids, so a bucket listing reveals nothing
```

Because stories are ~50MB, images are **content-addressed**: hashed, uploaded once, referenced by hash. The recurring sync is a gzipped encrypted skeleton, ~1.5KB. `sprout-sync-test.html` proves the round-trip is byte-identical.

⚠️ **`sprout-sync.js` is shared byte-for-byte by both pages.** Change any crypto constant and you must bump `VERSION`, both pages' `REQUIRE_SYNC_VERSION`, **and** the `?v=` on both script tags — together. A stale cached copy on one page derives different keys and fails **silently**: uploads succeed, collection succeeds, stories never open. Both pages assert the version on boot to turn that into a loud error.

⚠️ **The `storysketch_*` IndexedDB keys keep their old name on purpose.** Renaming them would orphan every existing user's autosave and file handle.

### CSS theming
All colours/spacing are CSS custom properties on `:root` (`--purple`, `--cream`, `--radius`, …).

### Keyboard shortcuts
- Ctrl/Cmd+Z — Undo · Ctrl/Cmd+Y or Ctrl/Cmd+Shift+Z — Redo
- Ctrl/Cmd+S — Save · Ctrl/Cmd+D — Duplicate
- Delete/Backspace — Delete selected

## Related docs
- `PIP_SCOPE.md` — Pip's behavioural spec. Mirrored into `PIP_SYSTEM` in the Worker; keep them in sync.
- `RESEARCH_DATA.md` — schema for the prompt-writing research data captured in the story file.
