# Style Consistency Options for Stability AI

Future enhancements to keep AI-generated image styles consistent across a story.

---

## 1. Seed Storage & Reuse
**Effort:** ~20 lines of code

- Store the `seed` returned from each generation alongside the image
- Display seed value in the AI drawer UI
- Add a "Lock seed" toggle so subsequent generations reuse the same seed
- **Same seed + same prompt + same settings = identical image**
- Seed range: 0–4,294,967,295

## 2. Image-to-Image Reference
**Effort:** ~50 lines of code (new API endpoint)

- **Endpoint:** `POST https://api.stability.ai/v2beta/stable-image/generate/sd3`
- Add a "Use as style reference" button on generated/canvas images
- Sends the reference image + new prompt to the img2img endpoint
- Key parameter: `image_denoise` (0.0–1.0) — lower values stay closer to reference
- **Recommended range:** 0.2–0.4 for style consistency
- Enables consistent characters, color palettes, and visual style across slides

## 3. Negative Prompt Field
**Effort:** ~10 lines of code

- Add a text input for negative prompts in the AI drawer
- API parameter: `negative_prompt` (max 10,000 chars)
- Common values: `blurry, ugly, distorted, extra limbs, watermark`
- Helps maintain quality consistency by excluding unwanted artifacts

## 4. Available Style Presets (already implemented)

| Preset | Use case |
|---|---|
| `digital-art` | Default, versatile |
| `comic-book` | Bold outlines, flat colors |
| `fantasy-art` | Rich, detailed fantasy scenes |
| `photographic` | Realistic photos |
| `cinematic` | Film-like dramatic lighting |
| `anime` | Japanese animation style |
| `3d-model` | 3D rendered look |
| `pixel-art` | Retro pixel style |
| `line-art` | Clean line drawings |
| `low-poly` | Geometric 3D style |
| `isometric` | Isometric perspective |
| `neon-punk` | Cyberpunk neon aesthetic |
| `origami` | Paper fold style |
| `analog-film` | Vintage film grain |
| `enhance` | General quality boost |
| `modeling-compound` | Clay/plasticine look |
| `tile-texture` | Seamless texture tiles |
