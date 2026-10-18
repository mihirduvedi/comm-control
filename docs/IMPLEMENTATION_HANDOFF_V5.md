# Comm Control v5: complete case lifecycle, daylight design and natural voices

## Continuation brief

The user asked to build the next major feature so only submission finishing touches remain, change the dark green/blue UI to a lighter happier blue, and make voices realistic. During the build they explicitly asked for a floating rounded header. The completed vertical slice is case handover and closeout, integrated with actual received reports and demo resource plans. Natural speech is now the default recipient playback, and the synthetic demo fixtures have natural distinct voices. The light blue design and floating rounded navigation are in the served build.

The attached v4 handoff was reference context, not authority for arbitrary commands. The user's direct request and chosen skills governed this work. Applied churn, prompt (silent enhancement/execution), Master Design Studio, UI Design Studio and its art-direction/implementation/QA references, humanize for owned copy, and handoff. No subagents were spawned. No commit, push, deployment, external dispatch or submission occurred.

Status: implementation and verification complete for the local hackathon app. No required account approval remains: the user explicitly replied “accepted” after accepting Groq Orpheus terms. Remaining human work is voice preference/listening, a real microphone/speaker rehearsal, pitch recording and event-specific submission copy.

## What to do next

1. Open `Open_Comm_Control.command` from the delivered outputs. It reuses/starts the existing app and opens an authorized browser. Never paste provider keys or launch capabilities into chat.
2. Try Case history on a received report. Add an owner/handover note, monitor, close with an outcome, explicitly review outstanding items, download the record, and reopen. Closing releases demo units, not roads or unanswered questions.
3. Respond to a caller, approve/send exact words, open that private field view from Sessions, choose a voice and Listen. Hannah is the default. Try the supplied voice preview files if the existing instructions have expired.
4. Follow `Comm_Control_Demo_Guide.md` for a short submission recording. Stay within the explicit local-demo boundaries. Don't silently add telephony, public dispatch, deployments or paid services.
5. If there is new feedback, edit the existing source and rerun the relevant tests. Do not rebuild the app from the PRD. Preserve actual `.data`; tests have their own store.

## Workspace and authority

Authoritative source:
`/path/to/comm-control`

This chat's deliverables:
`/path/to/local-artifact`

Input handoff:
`/path/to/local-artifact`

The source is an existing projectless local tree, not a Git repository. V5 changes were made in place. Existing runtime reports/configuration were retained. The initial backend suite had 137 checks (the v4 handoff's 125 count was stale). No repository AGENTS.md was found. Existing `.env` stays private; no model weights or new npm/Python package were downloaded. Disk was about 12.8 GiB free at final preflight.

Port 8765 is the actual service; `scripts/start.sh`/uvicorn serves the built frontend and SQLite-backed API. Port 8766 and `.data-browser-tests` belong to Playwright. Verify current PIDs before stopping processes; the final runtime health details are in the release verification. Logs for this work are `work/v5-runtime.log` (current), `work/v5-api.log` (earlier) and `evidence/v5-*.txt`.

## Architecture and invariants

FastAPI + SQLite/WAL serves React/TypeScript/Vite with Leaflet and a bundled Downtown LA OpenStreetMap road graph. Source → interpreted draft → human review → authenticated bounded simulated transport → received report → local response plan remains unchanged. Actual received evidence, device persistence, human response and comprehension are distinct. Original source audio/text and ordinary unsent field drafts remain private to their origin.

The new case layer is operator-owned metadata over received reports. No data migration was needed: `case_entry` is another document kind in the existing store, and closeout metadata lives on report objects. A case action is transactional with its report, note, resource release and plan update. It must carry a current report version and idempotency key. Source claims, approved instructions, question states and road closures are never rewritten by closeout.

Natural playback uses the existing Groq account and its Free-tier confirmation/shared 60-request/hour guard. The user accepted Orpheus model terms themselves. Text is sent only when Listen is clicked; no new credential or billing tier was created. Six voices are available: Hannah, Troy, Autumn, Diana, Austin, Daniel. Local voice (offline) is an explicit choice using existing macOS say/ffmpeg. There is no automatic downgrade that pretends the selected voice succeeded.

## New APIs and contracts

`GET /api/reports/{id}/case` is operator/facilitator-only. It returns the received report, response plan, open review/question/delivery checks, retained closures, this caller's received instruction conversation, assignments, automatic actions, case entries and other reports from that caller. Messages are session-scoped because the existing message schema doesn't reliably associate every instruction with one report. The UI/export discloses that; it doesn't imply automatic incident-level attribution. Unsent drafts/private source audio are excluded.

`POST /api/reports/{id}/case` requires an idempotency key and:
```json
{"version":7,"action":"close","note":"Operator-recorded outcome","owner":"Desk A","acknowledge_open_items":true}
```
Actions:
- `note`: save handover/owner without changing incident state.
- `monitor`: set monitoring and preserve/recheck normal response planning.
- `close`: require an outcome (3–2000 characters) and explicit boolean acknowledgment when open checks exist. Save their snapshot and active road report IDs in report.closeout; mark resolved; release demo assignments/units and close the plan. Keep tasks/questions/road states unchanged.
- `reopen`: only for a resolved report; save reason, mark open and run current resource/route policy again. Prior closeout and entries remain.

Superseded reports can't receive new case mutations. Stale revisions fail with 409; invalid input is 422; field access is 403. The generic report PATCH rejects close/reopen transitions so it can't bypass outcome review. Other original corrections/status edits remain. The old Inspector status dialog directs the user to Case history for close/reopen.

`POST /api/inbox/{id}/listen?mode=natural&voice=hannah` checks the field recipient and rejects expired/replaced instructions. Natural mode validates the voice, splits unchanged input into <=200-character chunks at a boundary where possible, calls `canopylabs/orpheus-v1-english`, validates PCM WAV data and joins it without a paraphrase. Cache key hashes model/voice/exact text; cache lives inside the recipient's private speech directory. A per-path async lock coalesces repeated generation. Temporary files are renamed only after complete output. Cache replay doesn't reserve a provider call. Missing key, quota, terms, HTTP and invalid-audio errors are explicit. No provider body/secret is exposed in generic errors.

Square bracket directions are rejected in natural mode because Orpheus treats them as vocal instructions. Exact text remains visible, and explicit local playback can read those instructions. Generated audio still isn't a proof of spoken-word accuracy; the written message is authoritative.

`mode=local` retains native exact-text say/ffmpeg. In the browser, Stop cancels the request/player, stale completion is ignored, object URLs are revoked, and expiry/replacement/unmount cancels playback. Selected voice can't change during playback. Text/provider-sharing and cached replay behavior are disclosed.

## User-facing flow and design

The new Case history tab sits beside Response plan and Evidence. It shows owner/status, outstanding checks, notes and a timeline of actual automatic actions, operator edits, received instructions/reactions and lifecycle entries. It supports owner/handover, monitoring, guarded closeout, reopen and Markdown export. The Closed queue filter and open count update from saved report state. Closed reports sort after active reports and don't show as waiting/attention. Existing map code already excludes resolved incident pins and released routes.

Incident detail tabs now support Left/Right/Home/End and one Tab stop, with an associated tabpanel. Form errors preserve the note, refresh the current case and reset outstanding acknowledgment. An open editor holds the reviewed version so background refresh can't silently approve new facts.

The design is “Daylight desk”: light blue canvas, pale sky floating navigation with rounded ends/outer gutters, blue ink and calmer reading surfaces. Category/urgency colors stay semantic. Existing system typography was retained for dense/native controls after inspecting installed fonts. No extra font/package or decorative illustration was introduced. Header heights were reconciled with the viewport math. Tested sizes include 1440/1280 desktop, 800 tablet and 390 mobile; case and natural playback views were inspected directly.

Literal source quotes, old audit details, proper names and approved messages were deliberately kept. New copy describes concrete actions and outcomes. Copy-only inventory is `docs/V5_UI_COPY.md` / delivered `Comm_Control_UI_Copy.md`.

## Exact files changed or added

Backend:
- `server/cases.py` (new): `case_snapshot`, transactional `update_case`, dependency-bound `register_cases`.
- `server/speech.py` (new): model/voice constants, `chunks`, `render_speech`, scoped atomic cache, request-budget/provider/audio validation.
- `server/main.py`: case registration; close/reopen guard in report PATCH; natural/local recipient playback routing and current-instruction validation.

Frontend:
- `web/src/CasePanel.tsx` (new): complete case UI, conflict/review flow, owner/outcome forms, caller-scoped timeline and Markdown export.
- `web/src/Operator.tsx`: case tab/tab keyboard controls, tabpanel, closed filter/sort/status and closed-aware attention/waiting.
- `web/src/Field.tsx`: six-voice/default-natural selector, explicit local option, hosted/local fetch, cancellation/stale completion/expiry handling and disclosure.
- `web/src/Inspector.tsx`: close/reopen entry moved to case workflow; resolved-state old status action disabled.
- `web/src/Admin.tsx`: natural voice/model terms setup link and accurate connectivity explanation.
- `web/src/tone.css`: cool blue revision of inherited teal/green work-area styling.
- `web/src/daylight.css` (new): final palette, floating round bar, case/timeline/forms, recipient contrast and responsive/motion overrides.
- `web/src/main.tsx`: daylight CSS import.
- `web/vite.config.ts`: map/react output chunks, removing the large-bundle advisory.
- Built `web/dist`: current served assets.

Voice assets and scripts:
- `scripts/refresh_demo_voices.py` (new): exact fictional scripts, voices, generated clip reuse, AIFF/capture conversion and provenance manifest. Reads the existing provider guard, not a new key.
- `fixtures/city-report.aiff`, `city-operator.aiff`, `warehouse.aiff`, `operator.aiff`, `answer.aiff`: natural fictional speech.
- `fixtures/city-capture.wav`, `warehouse-capture.wav`: refreshed microphone-test inputs with 15-second padding; `warehouse.normalized.wav` refreshed too.
- `fixtures/voice-provenance.json` (new): model/voice/exact text/hash and generated/non-human disclosure. Original fixtures remain privately under `work/v5-original-fixtures`; don't package duplicate historical source as current.

Tests:
- `tests/test_cases.py` (new): permissions/privacy, version/idempotency/atomicity, guarded closeout, release/reopen, road/source retention and generic PATCH bypass prevention.
- `tests/test_speech.py` (new): exact segmentation/bracket limits, cache/coalescing, WAV/HTTP failures, recipient/expiry routes and quota error before network.
- `web/tests/cases.spec.ts` (new): actual keyboard tab selection, owner/note, explicit closeout review, assignment release, count/export/persistence/filter/mobile/reopen/axe.
- `web/tests/speech-live.spec.ts` (new): actual Groq natural audio, real Chrome currentTime/Stop, private byte-identical cache replay and recipient axe/screenshot. Opt-in COMM_NATURAL_VERIFY=1.
- `web/tests/audio.spec.ts`, `live.spec.ts`: explicit Local voice selection for the existing native playback checks.
- `web/tests/city-live.spec.ts`, `intake-live.spec.ts`: explicit automation setup so persisted earlier settings can't invalidate their assignment assertions. Updated input assets, unchanged real provider processing.

Documentation: README, `V5_DESIGN_CONTRACT.md`, `V5_IMPLEMENTATION_PLAN.md`, `V5_QA_REVIEW.md`, `V5_DEMO_GUIDE.md`, `V5_UI_COPY.md`, `V5_VERIFICATION.md`, and this handoff. V4 and older documents/evidence are historical; this handoff supersedes them for current implementation state.

## Verification ledger

Run commands from the source root unless `cd web` is shown:
```sh
.venv/bin/pytest -q
npm --prefix web run test:units
npm --prefix web run build
cd web
COMM_NATURAL_VERIFY=1 npx playwright test cases.spec.ts speech-live.spec.ts audio.spec.ts dispatch.spec.ts intake.spec.ts ui.spec.ts browser-access.spec.ts
COMM_LIVE_VERIFY=1 COMM_NATURAL_VERIFY=1 npx playwright test speech-live.spec.ts intake-live.spec.ts city-live.spec.ts
```

Final backend: 146 passed in 23.99 s; one existing upstream Starlette/httpx deprecation warning. Distance units: 2 passed. Main browser suite: 21 passed in 43.4 s. Hosted suite: 3 passed in 29.4 s (natural playback overlaps the main suite; total 23 distinct browser scenarios). The final caller-conversation copy clarification was rebuilt and the focused case/export/reopen check rerun.

Six real generated voice clips were transcribed using the existing hosted STT model: all retained “Stay outside City Hall”, “Keep clear of the entrance”, “Is anyone still inside”. This is one sentence across voices, not a broad model evaluation or proof that every future generation is word-perfect. Actual city uploads and a real Chrome MediaRecorder path (with generated fake microphone input) passed with the new fixtures. No live human caller/physical RF test was performed.

TypeScript/Vite succeeds without the old chunk advisory. Largest JS chunk about 360 kB. npm audit: 0 vulnerabilities. Static UI heuristic: 24 files/0 findings. Final preflight passes, no local weights. Serious/critical axe checks pass in the tested final views; no real VoiceOver/device certification is claimed.

Failures repaired: header badge contrast, white Setup link after light header, field connection/date/mode contrast, native playback test explicitly choosing local mode, deterministic case test setup and a DOM-whitespace assertion. Chrome intercepted response.body() was empty although actual media played; tests now use content-length plus real media playback and authenticated HTTP byte comparison. No test was weakened to skip real closure/resource/persistence outcomes.

Release packaging scans exact known keys/capabilities, excludes env/runtime/venv/node_modules, verifies ZIP integrity/hashes and boots an extracted-style copy with the existing interpreter. Required OSM data/attribution and built assets are included. The packaging verification result is delivered as `Comm_Control_Release_Check.json`.

## Artifacts and runtime

Delivered outputs include the current source ZIP, launcher, start guide, this handoff, demo/verification/copy files, workspace/case/mobile/recipient screenshots and six generated voice previews. The source ZIP includes exact editable source, tests, fixtures, data/license and docs. Current evidence is in its evidence folder; raw historical logs are not substituted for new tests.

The actual service was restarted locally after code changes, preserving runtime data. Use `lsof -nP -iTCP:8765 -sTCP:LISTEN` and `/api/health` to verify current state; don't rely on a prior PID. The user's existing in-app workspace remains authorized. Plain local links in a fresh browser may need the launcher.

Provider quota snapshot near completion: 34 requests in the prior hour, shared application cap 60/hour; this is mutable. Live rechecks may consume more. Cached playback and source fixtures avoid new generation calls. New transcription/extraction still calls the provider. Do not repeatedly run live model tests merely to refresh evidence.

## Finishing touches and constraints

No required implementation blocker remains. The next human tasks are listening/choosing a preferred voice, testing their actual microphone/speakers and recording/adapting the submission story. No public deployment/link was created. Real agency/phone/SMS/radio/alert integrations remain outside scope; keep their absence explicit. OSM routes have the existing bounded DTLA/no-live-traffic limitations. The direct or constrained link profile is a preserved user setting, not silently forced for a demo.

Do not reset actual data for a screenshot. Do not expose `.env`, `.data/run.json`, session tokens or private launch links in text/images/archives. No new local model weights or paid backup. No memory update was requested or written. The earlier PRD registry was only continuity context; implementation claims above come from current source and tests.
