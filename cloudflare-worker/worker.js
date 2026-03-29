// Cloudflare Worker — Stability AI Proxy
// Keeps the API key server-side, never exposed to the browser.
//
// Environment secret required:
//   STABILITY_API_KEY — your Stability AI API key
//
// Deploy: Cloudflare Dashboard → Workers & Pages → Create Worker
// Then add STABILITY_API_KEY as a secret in Settings → Variables

const STABILITY_URL = 'https://api.stability.ai/v2beta/stable-image/generate/core';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'POST required' }), {
        status: 405,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      });
    }

    try {
      const body = await request.json();
      const { prompt, style_preset, cfg_scale, steps, output_format, aspect_ratio } = body;

      if (!prompt) {
        return new Response(JSON.stringify({ error: 'prompt is required' }), {
          status: 400,
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        });
      }

      // Build multipart/form-data for Stability AI
      const formData = new FormData();
      formData.append('prompt', prompt);
      formData.append('output_format', output_format || 'png');
      if (aspect_ratio) formData.append('aspect_ratio', aspect_ratio);
      if (style_preset) formData.append('style_preset', style_preset);
      if (cfg_scale) formData.append('cfg_scale', String(cfg_scale));
      if (steps) formData.append('steps', String(steps));

      const res = await fetch(STABILITY_URL, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.STABILITY_API_KEY}`,
          'Accept': 'image/*',
        },
        body: formData,
      });

      if (!res.ok) {
        const errText = await res.text();
        return new Response(JSON.stringify({ error: `Stability AI error: ${res.status} ${errText.slice(0, 300)}` }), {
          status: res.status,
          headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
        });
      }

      // Convert image to base64 data URL (chunk to avoid call stack overflow)
      const imageBuffer = await res.arrayBuffer();
      const bytes = new Uint8Array(imageBuffer);
      let binary = '';
      for (let i = 0; i < bytes.length; i += 8192) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
      }
      const base64 = btoa(binary);
      const mime = res.headers.get('Content-Type') || 'image/png';
      const dataUrl = `data:${mime};base64,${base64}`;

      return new Response(JSON.stringify({ image: dataUrl }), {
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
      });
    }
  },
};
