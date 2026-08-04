/*
 * Derive a team's authToken from (team name, secret code) using the SAME
 * sprout-sync.js the two pages use, then ask the relay what content level that
 * team is actually on.
 *
 * This is the `tier_enforced` check from PROTOCOL.md §4, run as a pre-flight.
 * The level is resolved server-side, so a team that is silently on the wrong
 * one would void an entire arm of the audit without anything looking wrong.
 * Cheap to check, expensive to discover later.
 *
 * usage: node team_token.js "<team-name>" "<code>" [expected-level]
 */
const fs = require('fs');
const path = require('path');

globalThis.window = globalThis;
const syncPath = path.join(__dirname, '..', 'sprout-sync.js');
(0, eval)(fs.readFileSync(syncPath, 'utf8'));

const WORKER = 'https://storysprout-pip.jackwangxyw.workers.dev';
// Cloudflare 1010-blocks a default Node/curl UA before the Worker ever sees it.
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
         + '(KHTML, like Gecko) Chrome/126.0 Safari/537.36';

(async () => {
  const [name, code, expected] = process.argv.slice(2);
  if (!name || !code) {
    console.error('usage: node team_token.js "<team-name>" "<code>" [expected-level]');
    process.exit(2);
  }

  const keys = await window.SproutSync.deriveKeys(name, code);
  console.log(`team      : ${name}`);
  console.log(`normalized: ${window.SproutSync.normalizeTeamName(name)}`);
  console.log(`authToken : ${keys.authToken.slice(0, 16)}… (${keys.authToken.length} hex chars)`);

  const res = await fetch(WORKER + '/sync/state', {
    headers: { 'X-Team-Auth': keys.authToken, 'User-Agent': UA },
  });
  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    console.log(`state     : HTTP ${res.status} — ${body.error || 'unknown'}`);
    if (res.status === 403) {
      console.log('            (that team does not exist on the relay — check the name and code)');
    }
    process.exitCode = 1;
    return;
  }

  console.log(`exists    : ${body.exists}`);
  console.log(`level     : ${body.contentTier}`);
  console.log(`rev       : ${body.rev}   blobs: ${body.blobCount ?? 0}   bytes: ${body.bytes ?? 0}`);

  if (expected) {
    const ok = body.contentTier === expected;
    console.log(`\n${ok ? 'PASS' : 'FAIL'}  expected "${expected}", relay reports "${body.contentTier}"`);
    process.exitCode = ok ? 0 : 1;
  }
})().catch((e) => { console.error('ERROR', e); process.exitCode = 1; });
