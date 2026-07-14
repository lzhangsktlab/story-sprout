# vendor/

Third-party assets, served from our own origin **on purpose**.

## Why these are not on a CDN

This app is used by children aged roughly 7–9. Every external `<script src>` or
`<link href>` in a page causes the child's browser to contact that third party and
hand over its **IP address and user-agent**, on every page load, before the child
has done anything at all.

Previously the student app loaded:

| From | What | What it leaked |
|---|---|---|
| `fonts.googleapis.com` | the Nunito webfont | the child's IP → Google |
| `cdnjs.cloudflare.com` | Fabric.js | the child's IP → Cloudflare |

An IP address is a *persistent identifier* — one of the categories of personal
information named in the COPPA Rule (16 C.F.R. § 312.2). Rate-limiting has at least
a plausible internal-operations justification for touching one. **A webfont does
not.** It can simply be hosted here, and now is.

With these files local, the child's browser contacts exactly one origin it did not
choose — our own Cloudflare Worker — and only when a picture is actually generated.
That makes the project's "no telemetry" claim true rather than aspirational.

## Contents

| File | Version | Licence |
|---|---|---|
| `fabric.min.js` | Fabric.js 5.3.1 | MIT |
| `nunito/nunito-latin.woff2` | Nunito v32, latin subset, variable 200–1000 | SIL Open Font License 1.1 |
| `fonts.css` | local `@font-face` for the above | — |

## Updating

Re-download and commit the file; do **not** point a `<link>` or `<script>` back at a
CDN to get a newer version. The whole point is that these bytes are served from the
same origin as the page.
