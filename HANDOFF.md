# Storybook Workshop — Developer Handoff Guide

A guide for developers taking over this codebase. Focuses on structure, where things live, and how pieces connect.

---

## Project at a Glance

A single-file, client-side web app for creating illustrated picture books with AI image generation. No build step, no framework, no server. Runs by opening the HTML file in a browser or hosting it on any static server.

**Live site:** https://lzhangsktlab.github.io/story-sprout/workshop-plugin.html
**Repo:** https://github.com/lzhangsktlab/story-sprout
**Hosted via:** GitHub Pages (auto-deploys on push to `main`)

---

## File Map

```
platform/
├── workshop.html              ← Original standalone app (not actively maintained)
├── workshop-plugin.html       ← Main app (this is the one deployed and used)
├── cloudflare-worker/
│   └── worker.js              ← API proxy on Cloudflare (holds the AI key)
├── scripts/
│   └── images-to-json.py      ← Utility: convert image folders to workshop JSON
├── CLAUDE.md                  ← Architecture reference for Claude Code
├── RESEARCH_DATA.md           ← Schema for research data collected in saved files
├── STYLE_CONSISTENCY.md       ← Future feature ideas (not implemented)
└── HANDOFF.md                 ← This file
```

### Which file is "the app"?

**`workshop-plugin.html`** — this is everything: CSS, HTML, and JavaScript in one file (~2,400 lines). It's the version deployed to GitHub Pages and embedded in the Bubble.io app.

`workshop.html` is the earlier standalone version. It still works but lacks the plugin features (Story Text panel, Save As, IndexedDB persistence, image-to-image, research data tracking). Don't modify it unless you need the standalone version.

---

## How the Pieces Connect

```
┌─────────────────────────────────────────────────────┐
│  Bubble.io App (somethingbeautiful322.bubbleapps.io)│
│  ┌───────────────┐                                  │
│  │ Story Library  │──── "Use this Story" button ───►│
│  └───────────────┘     opens new tab with           │
│                        ?story=...&title=...          │
└─────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│  GitHub Pages                                       │
│  workshop-plugin.html                               │
│  (reads story text from URL params)                 │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │ Fabric.js│  │ AI Drawer │  │ Story Text Panel│   │
│  │ Canvas   │  │ (generate │  │ (copy/paste     │   │
│  │ Editor   │  │  images)  │  │  to slides)     │   │
│  └──────────┘  └─────┬─────┘  └─────────────────┘   │
└──────────────────────┼──────────────────────────────┘
                       │ fetch()
                       ▼
┌─────────────────────────────────────────────────────┐
│  Cloudflare Worker (stability-proxy.lzhang688)      │
│  worker.js                                          │
│                                                     │
│  POST /      → Stability AI generate/core           │
│  POST /edit  → Stability AI control/structure       │
│                                                     │
│  Holds STABILITY_API_KEY as env secret              │
└─────────────────────────────────────────────────────┘
```

---

## Inside workshop-plugin.html

### Layout (top to bottom)

```
┌────────────────────────────────────────────────────────────┐
│ TOP BAR: Back | Brand | Title | Story Text | Save Status  │
│          | New | Open | Save | Save As | Export PNG        │
├────────────────────────────────────────────────────────────┤
│ RIBBON: Insert | Edit | Arrange | Align | Zoom            │
├──────┬───────────────────────────────┬─────────┬──────────┤
│ SLIDE│                               │PROPERTIES│ STORY   │
│ PANEL│      CANVAS (Fabric.js)       │  PANEL   │ TEXT    │
│      │      800 × 540               │          │ PANEL   │
│ Page │                               │          │         │
│ thumbs                               │          │         │
├──────┴───────────────────────────────┴─────────┴──────────┤
│ AI DRAWER (collapsible, overlays canvas area)             │
│ ┌─ History strip (thumbnails with ×delete) ─── Clear All ┐│
│ │                 Image Preview                          ││
│ │ Prompt: [...] Style:[▼] Quality:[▼] Strength:[═══]    ││
│ │              Generate | Regenerate | Add to Canvas     ││
│ └────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────┤
│ STATUS BAR: zoom | page | position | messages            │
└──────────────────────────────────────────────────────────┘
```

### Global State — the `S` object

All runtime state lives in one object:

| Property | What it holds |
|----------|---------------|
| `S.slides[]` | Array of `{json, thumb, imgMap}` per slide |
| `S.cur` | Current slide index |
| `S.history[]` / `S.redo[]` | Per-slide undo/redo stacks (max 50) |
| `S.canvas` | The Fabric.js canvas instance |
| `S.zoom` | Current zoom level |
| `S.fileHandle` | File System Access API handle (Chrome — for auto-save) |
| `S.dirHandle` | Directory handle (legacy, mostly unused in plugin) |
| `S.imgMap` | Maps image element IDs to filenames |
| `S.dirty` | Whether there are unsaved changes |
| `S.aiImgSrc` | Currently previewed AI image (base64) |

Other key globals:
- `storyTextLines[]` — the story text lines for the side panel
- `aiHistory[]` — AI generation history with full research metadata
- `aiSelectedIdx` — currently selected history thumbnail
- `SESSION_START` — ISO timestamp when the page loaded

### Major Function Groups

| Area | Key functions | What they do |
|------|--------------|--------------|
| **Canvas** | `initCanvas()`, `fitCanvas()`, `bindCanvas()` | Set up Fabric.js, handle resize, wire mouse/keyboard events |
| **Slides** | `saveCurrentSlide()`, `loadSlide()`, `addSlide()`, `deleteSlide()`, `renderSlideThumbs()` | Multi-page management, serialize/deserialize canvas per slide |
| **History** | `pushHistory()`, `undo()`, `redo()` | Per-slide undo/redo via JSON snapshots |
| **Elements** | `addTextBox()`, `addShape()`, `addImageSrc()`, `deleteSelected()`, `duplicateSelected()` | Add/remove canvas objects |
| **Properties** | `showPropsPanel(obj)`, `clearPropsPanel()` | Dynamic property editor (position, color, font, etc.) |
| **AI Generate** | `generateAiImage()` | Text-to-image via Cloudflare Worker proxy |
| **AI Modify** | `modifyAiImage()` | Image-to-image via Worker `/edit` route |
| **AI History** | `addToHistory()`, `renderHistoryStrip()`, `selectHistoryItem()`, `deleteHistoryItem()`, `clearAiHistory()` | Manage generated image gallery |
| **Story Text** | `setStoryText()`, `renderStoryText()`, `toggleStoryTextPanel()` | Side panel for story text from Bubble |
| **Save/Load** | `saveStory()`, `saveStoryAs()`, `openStory()`, `loadStoryData()`, `buildStoryJson()` | File persistence (Chrome: File System API, Firefox: IndexedDB + download) |
| **Auto-save** | `scheduleAutoSave()`, `markDirty()` | 5-second debounced save (to file or IndexedDB) |
| **Boot** | `DOMContentLoaded` handler | URL param parsing, auto-resume, canvas init |

### How Save/Load Works

**Chrome/Edge:**
- Save → `showSaveFilePicker` → writes to file → stores `fileHandle` in IndexedDB
- Auto-save → writes to same file every 5 seconds
- Open → `showOpenFilePicker` → reads file → stores handle
- Auto-resume → reads `fileHandle` from IndexedDB on boot

**Firefox/Safari:**
- Save → saves to IndexedDB (silent)
- Save As → prompts for filename → downloads as `.json`
- Auto-save → saves to IndexedDB every 5 seconds
- Open → `<input type="file">` → reads selected file
- Auto-resume → reads from IndexedDB on boot

### How the AI Drawer Works

1. User clicks "AI Image" → drawer opens
2. User types prompt, picks style/quality
3. **Generate New** → `generateAiImage()` → POST to `PROXY_URL` (Worker `/`) → Stability AI `generate/core` → returns base64 image
4. **Regenerate** → `modifyAiImage()` → POST to `PROXY_URL + '/edit'` → Worker forwards image + prompt to Stability AI `control/structure` → returns modified image
5. Image appears in preview + added to `aiHistory[]` with timestamp, settings, parentId
6. **Add to Canvas** → places image on current slide, logs `added_to_canvas` action
7. Delete from canvas → logs `removed_from_canvas` action

### Research Data (captured automatically)

Every AI generation is tracked in `aiHistory[]` with:
- `prompt`, `timestamp`, `settings` (style, quality, type)
- `parentId` — links refinement chains (which image was being modified)
- `actions[]` — add/remove from canvas with timestamps and slide index

See `RESEARCH_DATA.md` for the full schema.

---

## Cloudflare Worker (`cloudflare-worker/worker.js`)

**Deployed at:** `https://stability-proxy.lzhang688.workers.dev`
**Purpose:** Proxy that holds the Stability AI API key server-side

### Routes

| Route | Stability AI Endpoint | Purpose |
|-------|----------------------|---------|
| `POST /` | `generate/core` | Text-to-image (new image from prompt) |
| `POST /edit` | `control/structure` | Image-to-image (modify existing image) |

### Request format (from browser)
```json
// Text-to-image
POST /
{ "prompt": "a cat", "style_preset": "digital-art", "output_format": "png", "aspect_ratio": "16:9", "cfg_scale": 5, "steps": 15 }

// Image-to-image
POST /edit
{ "image": "data:image/png;base64,...", "prompt": "make it orange", "style_preset": "digital-art", "control_strength": 0.5 }
```

### Response format
```json
{ "image": "data:image/png;base64,..." }
```

### How to update the Worker
1. Go to https://dash.cloudflare.com → Workers & Pages → stability-proxy
2. Click "Edit code"
3. Select all → delete → paste new `worker.js`
4. Click Deploy
5. API key is stored as environment secret `STABILITY_API_KEY` in Settings → Variables

---

## Utility Script (`scripts/images-to-json.py`)

Converts a folder of images into a workshop-compatible JSON file with the images as AI history candidates.

```bash
python3 scripts/images-to-json.py "/path/to/image/folder"
# Output: /path/to/image/folder_name.json
```

The user can then Open this JSON in the workshop — images appear in the AI history strip.

---

## Bubble.io Integration

The workshop plugin is embedded in a Bubble.io app. When a user clicks "Use this Story", Bubble opens a new tab:

```
https://lzhangsktlab.github.io/story-sprout/workshop-plugin.html?title=Cat%20Story&story=Line1%0ALine2%0ALine3
```

The plugin reads `title` and `story` URL params on boot, populates the title and Story Text panel. The user copies lines from the panel into text boxes on their slides.

Story text can also be sent via `postMessage` (for iframe embedding):
```javascript
iframe.contentWindow.postMessage({ type: 'storyText', text: '...', title: '...' }, '*');
```

---

## Key Technical Decisions

| Decision | Why |
|----------|-----|
| Single HTML file | No build step, easy to host anywhere, easy to maintain |
| Fabric.js 5.3.1 | Mature canvas library with serialization, object management |
| Cloudflare Worker for API proxy | Free, no cold start, unlimited bandwidth, hides API key |
| IndexedDB for Firefox persistence | localStorage too small for base64 images, IndexedDB handles GBs |
| File System Access API for Chrome | Native save/open dialogs, auto-save to same file |
| Images inline as base64 | Self-contained JSON files, no separate image files to manage |
| Research data in same JSON | No external data collection, privacy-preserving |

---

## Deployment

### GitHub Pages (the HTML app)
- Push to `main` → Pages auto-builds
- Or manually trigger: `gh api repos/lzhangsktlab/story-sprout/pages/builds -X POST`
- URL: `https://lzhangsktlab.github.io/story-sprout/workshop-plugin.html`

### Cloudflare Worker (the API proxy)
- Manual deploy via Cloudflare dashboard
- See "How to update the Worker" section above

### Bubble.io (the parent app)
- Separate Bubble project at `somethingbeautiful322.bubbleapps.io`
- Links to the GitHub Pages URL with URL parameters
- Deploy via Bubble's Deploy button

---

## Quick Reference

| What | Where |
|------|-------|
| The app | `workshop-plugin.html` |
| API proxy | `cloudflare-worker/worker.js` |
| API proxy URL | `https://stability-proxy.lzhang688.workers.dev` |
| API key location | Cloudflare Worker env secret `STABILITY_API_KEY` |
| GitHub repo | `https://github.com/lzhangsktlab/story-sprout` |
| Live URL | `https://lzhangsktlab.github.io/story-sprout/workshop-plugin.html` |
| Bubble app | `https://somethingbeautiful322.bubbleapps.io` |
| Data schema docs | `RESEARCH_DATA.md` |
| Architecture docs | `CLAUDE.md` |
| CDN dependencies | Fabric.js 5.3.1, Google Fonts (Nunito) |
