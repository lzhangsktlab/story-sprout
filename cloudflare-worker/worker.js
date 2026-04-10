// Cloudflare Worker — Stability AI Proxy
// Keeps the API key server-side, never exposed to the browser.
//
// Routes:
//   POST /      — text-to-image (generate/core)
//   POST /edit  — image-to-image (edit/inpaint)
//
// Environment secret required:
//   STABILITY_API_KEY — your Stability AI API key
//
// Deploy: Cloudflare Dashboard → Workers & Pages → Edit code → Paste → Deploy

const GENERATE_URL = 'https://api.stability.ai/v2beta/stable-image/generate/core';
const INPAINT_URL  = 'https://api.stability.ai/v2beta/stable-image/edit/inpaint';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}

// Convert ArrayBuffer to base64 data URL (chunked to avoid stack overflow)
function toDataUrl(buffer, mime) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
  }
  return `data:${mime};base64,${btoa(binary)}`;
}

// Convert base64 data URL to Blob
function dataUrlToBlob(dataUrl) {
  const [header, b64] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)[1];
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }
    if (request.method !== 'POST') {
      return jsonResponse({ error: 'POST required' }, 405);
    }

    const url = new URL(request.url);

    try {
      const body = await request.json();
      const { prompt } = body;
      if (!prompt) return jsonResponse({ error: 'prompt is required' }, 400);

      let formData, targetUrl;

      if (url.pathname === '/edit' && body.image) {
        // ── Image-to-image (inpaint) ──
        targetUrl = INPAINT_URL;
        formData = new FormData();
        formData.append('image', dataUrlToBlob(body.image), 'image.png');
        formData.append('prompt', prompt);
        formData.append('output_format', body.output_format || 'png');
        if (body.style_preset) formData.append('style_preset', body.style_preset);
      } else {
        // ── Text-to-image (generate) ──
        targetUrl = GENERATE_URL;
        formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('output_format', body.output_format || 'png');
        if (body.aspect_ratio) formData.append('aspect_ratio', body.aspect_ratio);
        if (body.style_preset) formData.append('style_preset', body.style_preset);
        if (body.cfg_scale) formData.append('cfg_scale', String(body.cfg_scale));
        if (body.steps) formData.append('steps', String(body.steps));
      }

      const res = await fetch(targetUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.STABILITY_API_KEY}`,
          'Accept': 'image/*',
        },
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text();
        return jsonResponse({ error: `Stability AI error: ${res.status} ${errText.slice(0, 300)}` }, res.status);
      }

      const imageBuffer = await res.arrayBuffer();
      const mime = res.headers.get('Content-Type') || 'image/png';
      return jsonResponse({ image: toDataUrl(imageBuffer, mime) });

    } catch (err) {
      return jsonResponse({ error: err.message }, 500);
    }
  },
};
