/* ═══════════════════════════════════════════════════════════════════════════
   sprout-sync.js — shared crypto + transform + relay client for Teacher Mode.

   Loaded by BOTH workshop-plugin.html (student) and teacher.html (teacher).
   The two MUST agree byte-for-byte on every constant in here: if the HKDF
   `info` strings or the salt recipe ever drift between the two pages, the
   teacher silently cannot decrypt student work, and you find out only after a
   classroom of stories is unrecoverable. That is why this is one shared file
   and not copy-pasted into both.

   Deliberately a CLASSIC script (IIFE → window.SproutSync), NOT an ES module:
   ES modules are blocked over file://, and the student app must keep working
   when opened straight off disk.

   ── The security model, stated plainly ──────────────────────────────────────
   Work is encrypted in the child's browser before it ever leaves the machine.
   The relay stores bytes it cannot read. The only readable copy lives on the
   teacher's disk.

     masterKey = PBKDF2(secretCode, salt=SHA256("storysprout-v1|"+team), 600k)
     encKey    = HKDF(masterKey, "storysprout-enc-v1")   AES-GCM. Never leaves.
     authToken = HKDF(masterKey, "storysprout-auth-v1")  Sent to relay as proof.
     blobKey   = HKDF(masterKey, "storysprout-blob-v1")  HMAC key for blob ids.

   The relay sees authToken but cannot derive encKey from it (one-way HKDF with
   a different `info`). Blob ids are HMAC'd rather than raw content hashes, so
   whoever can list the bucket cannot test "does team X have this exact image?"
   nor correlate the same image across two teams.

   HONEST LIMIT: the secret code is the whole security model. A generated
   10-char code is fine against a curious classmate. It is NOT fine against a
   determined attacker holding the ciphertext — no iteration count fixes a
   small search space. Codes must be GENERATED, never chosen by a child.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
'use strict';

/* ── VERSIONING — read this before you edit anything below ───────────────────
   Both pages assert SproutSync.VERSION === their own REQUIRE_SYNC_VERSION and
   refuse to sync if it differs. That guard exists because the alternative is
   silent data loss: a browser holding a stale cached copy of this file would
   derive keys by a different recipe, the upload would still succeed, the teacher
   would still collect it, and the story would simply never open again.

   So if you change ANY crypto constant below, you must bump, together:
     1. VERSION here
     2. REQUIRE_SYNC_VERSION in workshop-plugin.html
     3. REQUIRE_SYNC_VERSION in teacher.html
     4. ?v=N on the <script src="sprout-sync.js?v=N"> tag in BOTH pages

   And note that changing the derivation constants makes every story already on
   the relay undecryptable. If that ever has to happen, add a new branch and
   migrate — do not edit these in place.
   ─────────────────────────────────────────────────────────────────────────── */
const VERSION = 1;
const PBKDF2_ITERS = 600000;             // OWASP floor for PBKDF2-HMAC-SHA256
const SALT_PREFIX  = 'storysprout-v1|';
const INFO_ENC     = 'storysprout-enc-v1';
const INFO_AUTH    = 'storysprout-auth-v1';
const INFO_BLOB    = 'storysprout-blob-v1';

const REF_PREFIX = 'sprout:';            // replaces a data: URL inside the manifest

// Envelope on the wire: [0]=fmt  [1]=flags  [2..13]=IV(12)  [14..]=AES-GCM ct‖tag
const FMT       = 1;
const FLAG_GZIP = 0x01;
const IV_LEN    = 12;
const HDR_LEN   = 2 + IV_LEN;

const enc = (s) => new TextEncoder().encode(s);
const dec = (b) => new TextDecoder().decode(b);

/* ── small helpers ───────────────────────────────────────────────────────── */

function toHex(buf) {
  const u8 = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = '';
  for (let i = 0; i < u8.length; i++) s += u8[i].toString(16).padStart(2, '0');
  return s;
}

async function sha256Hex(bytes) {
  return toHex(await crypto.subtle.digest('SHA-256', bytes));
}

// "Table 3" and "table 3 " must derive the SAME keys, or a trailing space
// silently makes a child's work unrecoverable. This is not paranoia; kids and
// teachers type team names by hand.
function normalizeTeamName(name) {
  return String(name || '').trim().replace(/\s+/g, ' ').toLowerCase();
}

function dataUrlToBytes(dataUrl) {
  const comma = dataUrl.indexOf(',');
  const mime = (dataUrl.slice(0, comma).match(/:(.*?);/) || [, 'image/png'])[1];
  const bin = atob(dataUrl.slice(comma + 1));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return { bytes, mime };
}

function bytesToDataUrl(bytes, mime) {
  let bin = '';
  const CHUNK = 0x8000;                  // avoid blowing the arg limit on big images
  for (let i = 0; i < bytes.length; i += CHUNK) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  }
  return 'data:' + (mime || 'image/png') + ';base64,' + btoa(bin);
}

async function gzip(bytes) {
  if (typeof CompressionStream === 'undefined') return null;
  const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function gunzip(bytes) {
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/* ── key derivation ──────────────────────────────────────────────────────── */

// ~0.4–1.2s on a low-end Chromebook, and WebCrypto's PBKDF2 does NOT yield —
// it blocks the main thread for the whole duration. Callers must paint a
// spinner and hand the browser a frame before calling this.
//
// (No Web Worker: blob-URL workers are blocked on file://, which would break
// the student app's open-straight-off-disk workflow.)
async function deriveKeys(teamNameRaw, secretCode) {
  const teamName = normalizeTeamName(teamNameRaw);
  if (!teamName) throw new Error('Team name is required');
  if (!secretCode) throw new Error('Secret code is required');

  const salt = new Uint8Array(
    await crypto.subtle.digest('SHA-256', enc(SALT_PREFIX + teamName))
  );

  const pbkdf2Key = await crypto.subtle.importKey(
    'raw', enc(String(secretCode).trim()), 'PBKDF2', false, ['deriveBits']
  );
  const masterBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERS, hash: 'SHA-256' },
    pbkdf2Key, 256
  );

  const hkdf = await crypto.subtle.importKey(
    'raw', masterBits, 'HKDF', false, ['deriveBits', 'deriveKey']
  );
  const hkdfParams = (info) => ({
    name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc(info),
  });

  // Non-extractable: XSS can *use* this key but cannot exfiltrate its bytes.
  const encKey = await crypto.subtle.deriveKey(
    hkdfParams(INFO_ENC), hkdf, { name: 'AES-GCM', length: 256 }, false,
    ['encrypt', 'decrypt']
  );
  const blobKey = await crypto.subtle.deriveKey(
    hkdfParams(INFO_BLOB), hkdf, { name: 'HMAC', hash: 'SHA-256', length: 256 },
    false, ['sign']
  );
  const authBits = await crypto.subtle.deriveBits(hkdfParams(INFO_AUTH), hkdf, 256);

  return { teamName, encKey, blobKey, authToken: toHex(authBits) };
}

// The id an image is stored under on the relay. HMAC — NOT the raw content
// hash — so listing the bucket reveals neither "team X holds this exact image"
// nor "teams X and Y hold the same image".
async function blobIdFor(blobKey, plainHash) {
  return toHex(await crypto.subtle.sign('HMAC', blobKey, enc(plainHash)));
}

/* ── encryption ──────────────────────────────────────────────────────────── */

// A FRESH random IV every single time. Reusing a nonce under AES-GCM leaks the
// authentication key itself, not merely the plaintext — it is catastrophic, not
// merely bad. Never derive the IV deterministically.
async function encrypt(key, bytes, { compress = false } = {}) {
  let flags = 0;
  let body = bytes;

  if (compress) {
    const gz = await gzip(bytes);
    if (gz && gz.length < bytes.length) { body = gz; flags |= FLAG_GZIP; }
  }

  const iv = crypto.getRandomValues(new Uint8Array(IV_LEN));
  const ct = new Uint8Array(
    await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, body)
  );

  const out = new Uint8Array(HDR_LEN + ct.length);
  out[0] = FMT;
  out[1] = flags;
  out.set(iv, 2);
  out.set(ct, HDR_LEN);
  return out;
}

async function decrypt(key, envelope) {
  const u8 = envelope instanceof Uint8Array ? envelope : new Uint8Array(envelope);
  if (u8.length < HDR_LEN) throw new Error('Envelope is truncated');
  if (u8[0] !== FMT) throw new Error('Unsupported envelope format: ' + u8[0]);

  const flags = u8[1];
  const iv = u8.subarray(2, HDR_LEN);
  const ct = u8.subarray(HDR_LEN);

  let plain;
  try {
    plain = new Uint8Array(
      await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, ct)
    );
  } catch (e) {
    // AES-GCM authentication failure. Overwhelmingly the wrong secret code —
    // callers should say that, not surface a raw OperationError.
    const err = new Error('Could not decrypt — wrong secret code, or the data is corrupt.');
    err.code = 'DECRYPT_FAILED';
    throw err;
  }

  return (flags & FLAG_GZIP) ? gunzip(plain) : plain;
}

/* ── content-addressing: shred / rehydrate ───────────────────────────────────
   A 6-page illustrated story is 20–30MB, because every AI image is base64'd
   inline into each slide's Fabric JSON *and* duplicated again in aiHistory.
   Re-uploading that every few minutes, per device, over school wifi, is a
   non-starter — so images are pulled out, hashed, and uploaded once each.
   The recurring payload drops to ~50–300KB.

   Fabric happens to store the SAME data-URL string for aiHistory[].dataUrl and
   the canvas object's src, so hashing the decoded bytes collapses that 2×
   duplication into a single blob for free.

   Thumbnails are deliberately NOT content-addressed: slides[].thumb is
   regenerated on every save, so its hash churns constantly — it would never
   dedup, and would just litter the store with orphans. They're 3–8KB; leaving
   them inline also lets the teacher's grid render with zero extra fetches.
   ─────────────────────────────────────────────────────────────────────────── */

async function stripNode(node, blobs) {
  if (!node || typeof node !== 'object') return;

  if (Array.isArray(node)) {
    for (const child of node) await stripNode(child, blobs);
    return;
  }

  // Only inline data: URLs are ours to take. An http(s) src (addImageFromUrl)
  // is someone else's URL and must be left exactly as it is.
  if (typeof node.src === 'string' && node.src.startsWith('data:')) {
    const { bytes, mime } = dataUrlToBytes(node.src);
    const hash = await sha256Hex(bytes);
    if (!blobs.has(hash)) blobs.set(hash, { bytes, mime });
    node.src = REF_PREFIX + hash;
  }

  // Today every image is a top-level object in objects[] — no groups, no
  // clipPaths, no background images anywhere in the app. Recurse anyway: the
  // cost is nothing and the failure mode of missing one is a corrupt story.
  for (const key of ['objects', 'clipPath', 'backgroundImage', 'overlayImage']) {
    if (node[key]) await stripNode(node[key], blobs);
  }
}

async function rehydrateNode(node, blobs) {
  if (!node || typeof node !== 'object') return;

  if (Array.isArray(node)) {
    for (const child of node) await rehydrateNode(child, blobs);
    return;
  }

  if (typeof node.src === 'string' && node.src.startsWith(REF_PREFIX)) {
    const hash = node.src.slice(REF_PREFIX.length);
    const blob = blobs.get(hash);
    if (!blob) {
      const err = new Error('Missing image blob ' + hash.slice(0, 12));
      err.code = 'MISSING_BLOB';
      err.hash = hash;
      throw err;
    }
    node.src = bytesToDataUrl(blob.bytes, blob.mime);
  }

  for (const key of ['objects', 'clipPath', 'backgroundImage', 'overlayImage']) {
    if (node[key]) await rehydrateNode(node[key], blobs);
  }
}

// story  → { manifestStory, blobs: Map<plainHash, {bytes, mime}> }
// `story` is exactly what buildStoryJson() produces; it is not mutated.
async function stripImages(story) {
  const out = JSON.parse(JSON.stringify(story));
  const blobs = new Map();

  for (const slide of (out.slides || [])) {
    if (!slide.json) continue;
    const canvas = JSON.parse(slide.json);   // slides[].json is a JSON *string*
    await stripNode(canvas, blobs);
    slide.json = JSON.stringify(canvas);
    // slide.thumb: left inline on purpose (see note above)
  }

  for (const item of (out.aiHistory || [])) {
    if (typeof item.dataUrl === 'string' && item.dataUrl.startsWith('data:')) {
      const { bytes, mime } = dataUrlToBytes(item.dataUrl);
      const hash = await sha256Hex(bytes);
      if (!blobs.has(hash)) blobs.set(hash, { bytes, mime });
      item.dataUrl = REF_PREFIX + hash;
    }
  }

  return { manifestStory: out, blobs };
}

// The exact inverse. MUST run before loadStoryData() ever sees the object:
// Fabric will happily try to fetch "sprout:<hash>" as a URL and hand back a
// broken image, and there is no clean hook to intercept it after the fact.
async function rehydrate(manifestStory, blobs) {
  const out = JSON.parse(JSON.stringify(manifestStory));

  for (const slide of (out.slides || [])) {
    if (!slide.json) continue;
    const canvas = JSON.parse(slide.json);
    await rehydrateNode(canvas, blobs);
    slide.json = JSON.stringify(canvas);
  }

  for (const item of (out.aiHistory || [])) {
    if (typeof item.dataUrl === 'string' && item.dataUrl.startsWith(REF_PREFIX)) {
      const hash = item.dataUrl.slice(REF_PREFIX.length);
      const blob = blobs.get(hash);
      if (!blob) {
        const err = new Error('Missing image blob ' + hash.slice(0, 12));
        err.code = 'MISSING_BLOB';
        err.hash = hash;
        throw err;
      }
      item.dataUrl = bytesToDataUrl(blob.bytes, blob.mime);
    }
  }

  return out;
}

/* ── key cache (IndexedDB) ───────────────────────────────────────────────────
   We cache the DERIVED KEYS, never the secret code. IndexedDB structured-clones
   CryptoKey, and encKey is non-extractable — so this is both nicer (later visits
   ask the child for nothing at all) and safer (the raw code is never sitting on
   disk) than persisting the code in localStorage.
   ─────────────────────────────────────────────────────────────────────────── */

const DB_NAME = 'storysketch_db';   // reuse the app's existing database
const STORE   = 'kv';
const KEY_REC = 'sprout_keys';

function idb() {
  return new Promise((res, rej) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
    };
    req.onsuccess = (e) => res(e.target.result);
    req.onerror = (e) => rej(e);
  });
}

async function idbPut(key, val) {
  const db = await idb();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, 'readwrite');
    tx.objectStore(STORE).put(val, key);
    tx.oncomplete = () => res();
    tx.onerror = (e) => rej(e);
  });
}

async function idbFetch(key) {
  const db = await idb();
  return new Promise((res, rej) => {
    const tx = db.transaction(STORE, 'readonly');
    const r = tx.objectStore(STORE).get(key);
    r.onsuccess = () => res(r.result);
    r.onerror = (e) => rej(e);
  });
}

async function cacheKeys(keys) {
  await idbPut(KEY_REC, {
    v: VERSION,
    teamName: keys.teamName,
    encKey: keys.encKey,       // CryptoKey — structured-cloneable, non-extractable
    blobKey: keys.blobKey,
    authToken: keys.authToken,
  });
}

async function loadCachedKeys() {
  const rec = await idbFetch(KEY_REC);
  if (!rec || rec.v !== VERSION || !rec.encKey) return null;
  return rec;
}

async function clearCachedKeys() {
  await idbPut(KEY_REC, null);
}

/* ── exports ─────────────────────────────────────────────────────────────── */

window.SproutSync = {
  VERSION,
  PBKDF2_ITERS,
  REF_PREFIX,

  // crypto
  deriveKeys,
  blobIdFor,
  encrypt,
  decrypt,

  // transform
  stripImages,
  rehydrate,

  // key cache
  cacheKeys,
  loadCachedKeys,
  clearCachedKeys,

  // utils (shared so the two pages cannot disagree about them)
  normalizeTeamName,
  sha256Hex,
  toHex,
  dataUrlToBytes,
  bytesToDataUrl,
};

})();
