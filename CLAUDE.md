# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StorySketch Workshop** — a single-file, client-side web app for creating multi-slide illustrated stories with an integrated AI image generator (Gemini API). No build step, no server, no framework.

## Running

Open `workshop.html` directly in a modern browser (Chrome/Edge 86+ recommended for File System Access API). No build tools or dependencies to install.

## Architecture

Everything lives in `workshop.html` (~2000 lines): inline CSS, HTML, and JavaScript.

### Key Dependencies (loaded via CDN)
- **Fabric.js 5.3.1** — canvas manipulation, object management, serialization
- **Nunito** (Google Fonts) — UI typeface

### Global State

All app state is in the `S` object:
- `S.slides[]` — array of `{json, thumb}` per slide (Fabric.js serialized JSON)
- `S.cur` — current slide index
- `S.history[]` / `S.redo[]` — per-slide undo/redo stacks (max 50 entries)
- `S.canvas` — the Fabric.js canvas instance
- `S.zoom` — current zoom level
- `S.dirHandle` — File System Access API directory handle
- `S.imgMap` — maps image IDs to filenames for on-disk storage

### Major Subsystems

| Area | Key functions |
|---|---|
| Canvas | `initCanvas()`, `fitCanvas()`, `bindCanvas()` |
| Slides | `saveCurrentSlide()`, `loadSlide()`, `addSlide()`, `deleteSlide()`, `renderSlideThumbs()` |
| History | `pushHistory()`, `undo()`, `redo()` |
| Elements | `addTextBox()`, `addShape()`, `addImageFromUrl()`, `addImageSrc()`, `deleteSelected()`, `duplicateSelected()` |
| Properties | `showPropsPanel(obj)`, `clearPropsPanel()` — dynamically renders editors based on object type |
| AI Image | `generateAiImage()` — calls Gemini API; `openAiDrawer()` / `closeAiDrawer()` toggle the drawer |
| Persistence | `saveStory()` / `openStory()` — read/write `story.json` + image files via File System Access API; auto-save debounced at 3s |
| File I/O | `ensureFolder()`, `writeFile()`, `readFile()`, `saveImageToFolder()` — wrappers around File System Access API |
| IndexedDB | `idbOpen()`, `idbGet()`, `idbSet()` — persists directory handle across sessions |

### Storage Format
- `story.json` — full project (slides as Fabric.js JSON, thumbnails, title, image map)
- `image_*.jpg` — extracted image files saved alongside the JSON
- IndexedDB stores the directory handle; localStorage remembers the folder name

### CSS Theming
All colors/spacing defined as CSS custom properties on `:root` (e.g., `--purple`, `--cream`, `--radius`).

### Keyboard Shortcuts
- Ctrl/Cmd+Z — Undo
- Ctrl/Cmd+Y or Ctrl/Cmd+Shift+Z — Redo
- Ctrl/Cmd+S — Save
- Ctrl/Cmd+D — Duplicate
- Delete/Backspace — Delete selected
