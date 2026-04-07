# Research Data Schema

Data collected by Storybook Workshop for studying children's AI prompt-writing progression. All data is saved in the story JSON file — no external data collection.

## File Structure (v5)

```json
{
  "v": 5,
  "title": "My Cat Story",
  "saved": 1712400000000,
  "session": {
    "startedAt": "2026-04-06T10:00:00.000Z",
    "savedAt": "2026-04-06T11:30:00.000Z",
    "totalSlides": 3
  },
  "storyText": ["Line 1", "Line 2", "..."],
  "aiHistory": [ ... ],
  "slides": [ ... ]
}
```

## AI History Item Schema

Each item in `aiHistory` represents one AI image generation:

```json
{
  "historyId": "ai_1712400000_x3k9",
  "prompt": "A cat climbing a tree, cartoon style, bright colors",
  "timestamp": "2026-04-06T10:15:30.000Z",
  "settings": {
    "style_preset": "digital-art",
    "quality": "draft"
  },
  "parentId": "ai_1712399900_m2j4",
  "actions": [
    { "type": "added_to_canvas", "at": "2026-04-06T10:16:00.000Z", "slideIdx": 0 },
    { "type": "removed_from_canvas", "at": "2026-04-06T10:17:00.000Z", "slideIdx": 0 },
    { "type": "added_to_canvas", "at": "2026-04-06T10:18:00.000Z", "slideIdx": 1 }
  ],
  "dataUrl": "data:image/png;base64,..."
}
```

### Fields

| Field | Type | Description |
|---|---|---|
| `historyId` | string | Unique ID for this generation |
| `prompt` | string | The text prompt the student wrote |
| `timestamp` | ISO 8601 | When the image was generated |
| `settings.style_preset` | string | Style used (digital-art, comic-book, etc.) |
| `settings.quality` | string | "draft" (512px) or "final" (1024px) |
| `parentId` | string/null | `historyId` of the image being refined (null if first attempt) |
| `actions` | array | Log of add/remove events (see below) |
| `dataUrl` | string | Base64-encoded image data |

### Action Types

| Action | Description |
|---|---|
| `added_to_canvas` | Student placed this image on a slide |
| `removed_from_canvas` | Student removed this image from a slide |

Each action includes:
- `at` — ISO 8601 timestamp
- `slideIdx` — which slide (0-indexed)

## Research Analysis Enabled

### 1. Prompt Progression
Compare consecutive prompts (ordered by `timestamp`) to see how students refine their descriptions over a session. Prompts linked by `parentId` form **refinement chains**.

### 2. Iteration Patterns
- How many images are generated before one is added to the book?
- How long between generation (`timestamp`) and adding to canvas (`actions[0].at`)?
- How many drafts are generated per slide?

### 3. Style Experimentation
Track `settings.style_preset` across generations to see which styles students prefer and whether they experiment.

### 4. Selection & Revision Behavior
- Images with `actions` containing both `added_to_canvas` and `removed_from_canvas` show revision behavior
- Images with no `added_to_canvas` action were generated but rejected
- Multiple `added_to_canvas` actions on the same image show reuse across slides

### 5. Session Engagement
- `session.startedAt` / `session.savedAt` gives session duration
- `session.totalSlides` shows scope of the picture book
- Number of `aiHistory` items shows total generation attempts

### 6. Prompt Complexity Over Time
Analyze prompt length, vocabulary, and descriptiveness across the `timestamp` sequence to measure learning progression within a single session.

## Privacy Notes

- No student names or identifying information is collected
- No accounts or logins — all data is local to the student's device
- Data is only in the saved JSON file — not sent to any server
- Researchers receive anonymized JSON files for analysis
