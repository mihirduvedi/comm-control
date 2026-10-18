# Comm Control v5.1: white glass and fixed speaker voices

## Continuation brief

The user asked for a working app link after removing the full-width dispatch divider, lightening the overly blue background and adding blue panel borders, assigning one voice per person instead of a voice picker, and removing colored vertical strips from the incident queue. They then asked to modernize everything with rounded glass panels and glass blobs, referencing Apple and their Dickman Mini Analyzer.

This revision is implemented in the existing app. It preserves the complete v5 capture/review/map/response/case-closeout story and all existing runtime reports. Current UI: mostly white translucent surfaces, blue outlines, soft fixed background light shapes, a rounded floating glass navigation bar, rounded controls/panels, no status divider or queue stripes. Each caller has one persisted voice; operator playback always uses one server-controlled voice. The picker is gone.

Current source root:
`/path/to/comm-control`

Current deliverables:
`/path/to/local-artifact`

This handoff supersedes v5 for design/voice/access behavior. The full v5 handoff remains in docs/IMPLEMENTATION_HANDOFF_V5.md as architectural/test history, including the case lifecycle details. Its voice picker and blue-canvas descriptions are historical.

## What to do next

1. Open the working private launch link supplied in chat. It can be redeemed once within 30 minutes and establishes the normal eight-hour local browser session. After that, use http://127.0.0.1:8765/control in the same browser. The launcher is the durable fallback on this Mac.
2. Inspect the main workspace. The status bar blends into the canvas, with no full-width line; incident rows have no left strips. Panel boundaries are blue outlines around white glass, and the background shapes are stationary.
3. Open a caller's field view. There is no voice menu. Listen uses the operator's assigned voice for operator messages; it never assigns the recipient's voice to the sender's message. Caller sample recordings use each caller's assigned voice.
4. Continue only with specific feedback or pitch/submission finishing work. No new major feature is required for the demonstrated local app. Do not reset actual data, silently add dispatch integrations, deploy, commit, push or submit without user instruction.

## Architecture and preserved behavior

FastAPI/SQLite WAL serves React/TypeScript/Vite, Leaflet and the bundled Downtown LA OSM road graph. Captured source → interpreted draft → human review → authenticated simulated link → received report → response plan remains intact. The case layer records owner/handover, monitoring, guarded closeout, resource release, reopen and download. Closing preserves sources, road reports, unanswered questions and actual delivery state. Actual and test stores remain separate.

The actual service uses port 8765 and `.data`; current logs are `work/v5-1-runtime.log`. Browser tests use 8766 and `.data-browser-tests`. Verify PIDs with lsof before stopping anything. The in-app browser was reopened to the actual authorized workspace; it still contained eight reports after the revision. No reports were reset to improve screenshots.

This is not a Git repository. No new packages, model weights, account tier or public deployment was introduced. Existing Groq Free-tier confirmation and the application's shared 60-request/hour cap remain. Keys and durable capabilities stay in private runtime files.

## Design contract

`web/src/glass.css` loads after daylight.css. Canvas #f7f9fc; white panel fills are translucent enough to reveal fixed low-contrast blue/cyan light shapes, but retain readable contrast. Three principal panes use 18px corners and blue outlines; the header uses a floating capsule; controls use 10–12px rounding. The map and source text remain crisp. Blur is for background depth, not foreground content. Reduced-transparency and unsupported-filter fallbacks use white surfaces. No moving blobs, particles, scrolling decorations or additional dashboard tiles.

The dispatch status bar has zero border/box shadow and transparent background. Queue ::before strips are disabled and the selected row's old colored inset shadow is removed; selection uses a pale fill, category icon and text. Category/urgency/warning colors remain meaningful.

The Dickman source theme was inspected directly at `/path/to/local-artifact`. Its neutral colors and practical hierarchy informed this direction. No claim was made of cloning an uninspected running analyzer; the new rounded/glass geometry comes from the user's explicit request. Memory reinforced the user's low-clutter preference, but current source/render/test evidence supports implementation claims.

Humanize was applied to the small new copy surface. Literal source quotes, original recordings, old audit entries, approved instructions and proper names remain unchanged. `docs/V5_1_UI_COPY.md` contains the changed product text.

## Speaker contract

`server/speakers.py` defines OPERATOR_VOICE='hannah' and stable caller assignments:
- Alex Rivera: Autumn
- Jamie Chen: Troy
- Jordan Chen: Diana
- Sam Okafor: Austin
- Taylor Brooks: Daniel

Unknown names use a deterministic normalized-name hash into the caller voice pool; their assignment is then saved in the session's demo_voice field. Multiple sessions with the same demo name get a consistent assignment. This is a prototype identity rule, not real-person identity matching or voice cloning.

`Domain.create_session()` saves demo_voice. Initialization adds it once to old sessions without changing their IDs, private token or display name. Reopening the server therefore keeps the assignment. `visible_session()` exposes the assignment as normal metadata. Field inbox projections add speaker_name='Operator' and speaker_voice='hannah'. There is no public mutation control for the voice.

`POST /api/inbox/{id}/listen` always derives the natural voice from the operator speaker constant. A client-supplied voice query parameter cannot change it. Existing recipient permission, expiry/replacement, exact text, chunking, cache and provider-budget guards remain. The legacy `mode=local` backend route remains for native compatibility testing; there is no user-facing voice picker or offline voice menu. UI errors keep the written instruction available for reading/retry. Original call audio is never synthesized into a different voice.

The fictional fixtures now match their stated speaker: city/warehouse reports and answer use Alex's Autumn voice; both operator instruction fixtures use Hannah. The refresh script records speaker, model, exact text and audio hash in `fixtures/voice-provenance.json`. Existing fixture originals remain privately under work/; actual runtime source recordings were not changed.

## Exact files changed or added

- `server/speakers.py` (new): fixed operator identity, canonical caller mapping, normalized deterministic fallback.
- `server/domain.py`: create/migrate persisted caller voice assignment; projected operator identity on field inbox.
- `server/main.py`: removes client-selected natural voice from recipient playback; uses server operator voice.
- `server/speech.py`: error text no longer suggests the removed voice menu.
- `web/src/Field.tsx`: removes voice state/select; always requests the speaker's normal playback; small generated-audio disclosure.
- `web/src/types.ts`: demo_voice and projected speaker metadata.
- `web/src/Admin.tsx`: fixed-speaker setup explanation.
- `web/src/glass.css` (new): final white-glass, blobs, rounded panel/control, outline, divider/stripe removal and accessibility fallback styling.
- `web/src/main.tsx`: imports glass.css last.
- `scripts/refresh_demo_voices.py`: canonical speaker fixture voices and provenance speaker labels; regenerated three affected AIFFs/capture WAVs (unchanged clips reuse cache).
- `scripts/open_app.py`: defaults to workspace; --live explicitly opens live capture; one-use link access is unchanged.
- `tests/test_speech.py`: voice override prevention, saved identity/new-session/restart/old-session migration coverage.
- `web/tests/polish.spec.ts` (new): white canvas, no divider/stripes/inset shadow, rounded panes, caller identity, responsive/axe/entry-point checks and screenshots.
- `web/tests/speech-live.spec.ts`: no voice selector, actual fixed operator playback/cache/stop.
- `web/tests/audio.spec.ts`: explicit test-only local-readout routing for the retained native API; no picker.
- `web/tests/live.spec.ts`: no removed selector; normal generated playback if opt-in legacy flow is run.
- Built `web/dist`, README and v5.1 design/plan/copy/handoff documents.

## Verification and repaired findings

The baseline was the completed v5 release. Final Python suite: 147 passed in 24.26 seconds, with the existing upstream Starlette/httpx deprecation warning. Focused speech suite passed, including authorization/expiry, preventing client voice changes, exact text/cache/failures and persistence/migration.

The complete browser suite passed 22 scenarios in 48.2 seconds (`evidence/v5-1-browser.txt`). A final root flow-layout fix prevents the floating header’s outer margin from adding page height, and the focused desktop/tablet/mobile polish scenario was rerun with an exact desktop viewport-height assertion. It includes existing auth, dispatch, source review, case lifecycle, recording denial/recovery, native compatibility, fixed natural voice playback and the new glass/responsive scenario. Tests use the actual built frontend and dedicated server/store. Natural playback makes a real Groq call, then verifies Chrome playback time, Stop and byte-identical private cached replay. It does not merely mock the provider result.

A first pass exposed routine queue text at 4.3:1 contrast on the whiter surface. The text was darkened and affected checks rerun. The generic static checker warns about repeated backdrop blur; this is an intentional, explicitly requested glass design, reviewed across its semantic work surfaces with contrast and reduced-transparency fallbacks. No functional/static error is hidden by that aesthetic warning.

Built TypeScript/Vite succeeds, with map/react chunks retaining the previous performance split. Static heuristic: 25 files, zero errors; one intentional glass-style warning. Exact desktop/tablet/mobile and recipient screenshots were visually inspected. No real mobile-device/VoiceOver/human-listening certification is claimed. The earlier hosted city/microphone verification remains history; this refinement did not rewrite intake/extraction/routing.

Run from the source root:
```sh
.venv/bin/pytest -q
npm --prefix web run build
cd web
COMM_NATURAL_VERIFY=1 npx playwright test polish.spec.ts speech-live.spec.ts audio.spec.ts dispatch.spec.ts cases.spec.ts intake.spec.ts ui.spec.ts browser-access.spec.ts
```
Do not run tests against actual .data or repeatedly spend live model quota without a verification reason.

## Access, deliverables and source package

The user explicitly requested a working link. The final chat supplies a fresh one-use local launch URL, separate from the provider key and durable operator token. It is intentionally not saved in artifacts/source/archive. A second unused launch ticket was not required for normal current-browser navigation; browser auth behavior is covered by existing tests. A fresh browser can use the one-use link; the existing authorized browser can use /control directly.

`Open_Comm_Control.command` reuses/starts the actual local service and calls the helper. The helper now opens the workspace by default. `scripts/open_app.py --live` opens capture. Browser authorization lasts eight hours; unused launch links last thirty minutes. The server stays loopback-only. Do not make /control unauthenticated merely to produce a friendly URL.

Latest source ZIP and handoff are versioned v5_1 in outputs. A clean extracted-style boot, required OSM data/attribution, built assets, ZIP integrity, per-file hashes and exact-known-secret scan are verified during packaging. Private env/runtime/dependencies/work caches are excluded. The ZIP contains current editable code, tests, fixtures, docs and evidence.

No required blocker or user approval remains. All requested work is local and reversible. No deployment, commit, push, external message or real dispatch was performed. Next actions are user visual/voice preference feedback and submission rehearsal/pitch finishing.
