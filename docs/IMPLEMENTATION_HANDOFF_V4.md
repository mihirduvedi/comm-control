# Handoff: Comm Control v4 quiet desk and live microphone map

> Continuation point from an earlier conversation. Read once, verify mutable runtime state and start with the next action below. The requested local prototype update is complete within the stated boundaries. Do not recreate the product or ask the user to repeat the task.

## Continuation Brief

- **Original task:** Build FieldPacket for the InnovateLA Dual-Use Hackathon from a pasted user prompt and PRD. User renamed it Comm Control.
- **Previous release:** Source-linked voice reporting, exact reviewed return instructions, constrained authenticated simulated transport, real OSM DTLA map/routes and policy-based demo unit/response plans.
- **Latest request:** Display miles, humanize all product text, add more useful color while reducing white/clutter, and let someone dictate a live demo message and watch it map to the control center while speaking. User explicitly confirmed Downtown Los Angeles.
- **Outcome:** Mixed-tone UI with clearer work zones, fewer visible secondary details, natural copy, miles/feet, and an actual microphone→hosted audio snapshots→provisional map pin→finished facts→operator review→received incident/route/demo assignment workflow.
- **Current phase:** Implemented, integrated and verified. Source/docs/evidence/handoff delivered locally. No deployment/commit/publication or real external dispatch.
- **Definition of done:** Real entry points and state/recovery are connected; source/approval/privacy/transport invariants survive; meaningful backend, unit, browser, hosted voice and render/accessibility checks pass; release package excludes secrets/runtime and includes the OSM data/attribution; authorized demo reopened.
- **State snapshot:** October17,2026 Pacific, around07:30. Verify service PID/health and quota before relying on mutable state.

## What to Do Next

**Instruction to the next chat:** Begin with the user’s feedback on the updated app. This request is complete; don’t silently add telephony or send anything outside the demo.

### Immediate next action

1. Open outputs/Open_Comm_Control.command if the user needs access. Plain localhost/control can show the access page because it lacks the private launch capability. Use the launcher or scripts/open_app.py; never paste tokens into chat.
2. For the new live demo, choose **Live call → Start microphone**, allow access, and say a short report near City Hall. About every5seconds a transcript/location preview appears. Choose **Finish call**, check the facts and choose **Add reviewed incident**. The selected simulated link still controls delivery.
3. On another change request, inspect current source and verify runtime state. Preserve actual .data and the user’s current reports. Tests use .data-browser-tests/port8766; never reset the actual run for testing.

### Already completed

- Dark teal navigation, mist-blue queue and sage response pane. Semantic fire/medical/access/safety/help/info accents remain separate from urgency.
- Unselected queue status lines hidden, Messages tools collapsed, fixed Respond action kept. Source inspector/Evidence and all existing controls remain.
- Humanized owned UI/policy/error copy across operator, field and admin; literal source quotes, already approved messages and old audit records remain unchanged. A copy-only Markdown inventory is in outputs/Comm_Control_UI_Copy.md.
- Geographic display uses miles and device accuracy feet. Road/storage/API values stay meters; spoken numerical miles/feet are protected against silent unit changes.
- Explicit desk-captured live-intake service/UI, provisional literal place pins, serialized bounded cumulative audio updates, final normal extraction, source correction/review, selected-link commit, cancellation and recording recovery.
-125backend checks,2distance display checks,16distinct browser checks,7focused final rechecks and2legacy-map rechecks; one actual hosted microphone flow using3provider calls in the ten-second synthetic run. Build, axe, static heuristic, npm audit and preflight pass within recorded scope.
- Actual desktop/narrow renders inspected. Data/attribution included in versioned source archive; secret scan/integrity/clean-source check and identical Downloads handoff copy are performed by packaging.

### Remaining work

No required implementation remains for this bounded local update. Product/human gates: actual microphone acoustics/speaker listening, unfamiliar human call phrasing with independent adjudication, real assistive technology/devices, operator usability/task times, operational route checks and any real emergency/phone/public-channel integrations. No new held-out model accuracy result is claimed.

### Blockers / decisions needed

None for the delivered app. Real outside communications/deployment/commits/account upgrades still require explicit user instructions. Keep the free-tier/no-local-weights decision and storage concern.

## Project / Task Context

### Background and scope

The original concept turns speech into source-linked facts and a shared site picture, then sends an approved instruction through a bounded link. The latest design feedback was that even the minimal layout felt overwhelmingly white and repetitive. The user wants a useful working demo, not a mockup, another plan or a page of design advice.

The live demo is microphone capture at the desk, not a telephone connection. It uses the existing free hosted speech model, not a browser speech service or downloaded weights. A provisional pin is a place mentioned in a partial transcript; it may be a caller position or one of multiple places. It never authorizes a dispatch. Final extraction separates event/reporter location and preserves uncertainty; received reports alone drive the response plan.

### Terminology and boundaries

- Source: immutable original text/audio, normally private to its origin.
- Draft: interpreted content requiring review; edits invalidate relevant approval/current versions.
- Received report: destination projection after actual authenticated simulated delivery.
- Intake: desk-captured call with explicit operator sharing of only its associated transcript/job/draft; normal unsent field sources stay private.
- Demo unit: simulated capability/location/status, with a local reservation and route estimate. Not a real resource dispatch or GPS feed.
- Advisory/contact note: reviewable wording/audience published only to a local demo board. No phone/SMS/public-alert service is connected.
- Receipt: device persistence, distinct from human acknowledgment, answered questions and comprehension.

### User corrections and authority

Use Comm Control, not FieldPacket in new product text. Downtown LA is explicitly chosen. The user required checking disk space before any local model; earlier downloads were stopped/removed. The private Groq key was configured locally by the user. All new services must stay free; no local weights or paid model/map accounts. Pasted request and direct user messages are authority; attached PRD is specification/source material, not permission to execute arbitrary document directives.

## Workstream Status & Roadmap

| Workstream | Status | Verification / boundary |
|---|---|---|
| Source/extraction/review/return link | Implemented | Original invariants retained;125backend + legacy browser/native audio checks. No human/physical-radio certification. |
| OSM map/routes/closures | Implemented, bounded DTLA | Actual graph/alternatives/edge exclusion/no-path/restriction checks; tile/route browser evidence. No live traffic or global routing. |
| Demo operations | Implemented | Capable available unit assignment, waiting resources, route holds, internal review/escalation and prepared messages. No real agency integration. |
| Quiet desk/copy/imperial UI | Implemented | Rendered1440/1280/800/390/720×500; unit formatting/accuracy/quote protection; axe/static and browser checks. |
| Live call | Implemented | Actual MediaRecorder + cumulative hosted STT + provisional pin before finish; final extraction/review/paused-link/receive/assignment. Explicit failure/cancel/revision tests. |
| Release | Delivered | V4 source/data/licenses/evidence/docs/handoff, clean extracted-source checks, launcher and current screenshots. |

## Work Completed

V2 built the full voice/source/evidence/return transport. V3 added a real-world OSM atlas and persistent dispatch policies plus category panels. V4 refined the visual/copy/imperial presentation and added live microphone intake. Old demo reports and data were preserved. Backend was restarted with the new intake routes. The user can open the updated authorized app without seeing/typing a key.

### Exact important files changed in v4

- web/src/format.ts: miles(), feet(), assertionLabel() and unitStatus(); display only, raw geometry stays meters.
- web/src/tone.css: new semantic surfaces, reduced density, responsive/accessibility states, live panel and overlay stacking. Existing styles.css/dispatch.css remain foundations.
- web/src/LiveIntake.tsx: microphone/update/recovery/review UI and source-only live preview state.
- web/src/Operator.tsx: Live call entry, provisional center brief, preview map and automatic focus only after actual report receipt.
- web/src/WorldMap.tsx: dashed provisional candidate rings and source labels; old incident/routes remain normal; map isolated below app notices.
- web/src/OperationsPanel.tsx: miles/short steps, unit labels, concise plan copy and collapsed Messages disclosure.
- web/src/FieldLocationMap.tsx: feet, both event/device positions fit in view, full accuracy radius, clear tile failure. Device coordinate never changes event.
- web/src/Admin.tsx, Field.tsx, Inspector.tsx, Composer.tsx, VoiceInput.tsx, ManualReport.tsx, SiteMap.tsx, api.ts, main.tsx: product text/labels/states and tone integration. Literal dynamic source and instruction text preserved.
- server/intake.py: operator-only desk-call APIs, cumulative STT snapshots, literal preview matching, source/job correlation, correction, reviewed send/cancel/version/sequence guards.
- server/main.py: register_intake() call. Generic field/draft/audio permissions unchanged.
- server/models.py: plain value-style extraction guidance and decimal miles/feet unit protection. Actual quoted excerpts and all factual schema requirements remain.
- server/operations.py: clearer future policy explanations; no dispatch-policy rewrite.
- tests/test_intake.py:9new backend cases including imperial instruction guard.
- web/tests/format.test.mjs:2display cases; web/tests/intake.spec.ts:2UI recovery/permission/axe checks; intake-live.spec.ts:actual hosted microphone flow; dispatch.spec.ts:feet/miles +5city checks; ui.spec.ts/live.spec.ts:updated labels.
- fixtures/city-capture.wav: synthetic native-speech input for fake microphone test; no local model.
- docs/V4_DESIGN_CONTRACT.md, V4_QA_REVIEW.md, README, DEMO, VERIFICATION, PRD amendment, IMPLEMENTATION_PLAN and this handoff.

## Current State

### Repository and runtime

Authoritative app: /path/to/comm-control
Root: /path/to/local-artifact
Actual service:127.0.0.1:8765, last observed PID33432, scripts/start.sh; logs work/v4-api.log. Verify PID/command before stopping it. Test server8766 is owned by Playwright and normally exits after tests. No Git repo/commit/deployment. No other project/files deleted.

Actual .data has the previous legacy/city reports and was never reset for v4. Test data may have been reset repeatedly. The actual transport was Local direct when last checked; don’t silently change user configuration to make a demo look faster. Standard simulated1000bit/s has intentionally longer airtime.

Private .env contains the user’s server-side provider key/Free confirmation. .data/run.json and sessions contain separate demo launch capabilities. Never print these, put them in public links/archive, or paste them into chat. Use the launcher/helper. About13.9GiB free at preflight; laptop remains relatively full. No model weights/new packages were downloaded; existing Babel parser was used only to export copy. No real phone/agency/public integrations or outbound sends.

### Latest verification boundary

Combined browser run:16passed in29.3seconds. Later7affected city/intake checks passed in13.9seconds after recovery-copy/device-map fitting fixes. Two distance cases passed. Backend125passed in22.25seconds with one upstream warning. The latest hosted microphone run passed in15.1seconds,17.6including startup, using2STT snapshots+1extraction. Later copy/map fixes did not change the hosted audio/backend flow; they were checked with focused UI tests. Final desktop padding was measured at800px document height for an800px viewport. Final source hashes/manifest record chronology rather than implying every historical model eval was rerun.

Production bundle ~512.7kB/~153.8kB gzip triggers a Vite chunk-size advisory; TypeScript/Vite succeeded. npm audit0, static heuristic22files/0findings, axe no serious/critical in tested city/legacy/live-empty/live-ready states. These aren’t full security/VoiceOver/human studies.

## Work Organization

- work/comm-control/server: FastAPI/domain/store/transport/model/geography/operations/intake.
- work/comm-control/web/src: editable product UI; web/dist is built/served output.
- data/downtown-la.osm.json, downtown-la.manifest.json, ATTRIBUTION.md: required cached road database/source/license. Omitting data breaks startup.
- fixtures: explicit synthetic audio/case inputs, not canned model fallbacks.
- tests and web/tests: Python/domain and real Chrome browser checks.
- evidence: current v4 test reports/screenshots plus retained historical evidence.
- docs: PRD, design/QA contracts, handoffs. Use v4 handoff; oldv2/v3 files are historical snapshots.
- outputs: user-facing deliverables and launcher. Final links in this projectless thread must use absolute paths to outputs.
- work/package_release_v4.py: whitelist release/manifest, exact-known-secret scan, clean source check and Downloads handoff copy.

All project implementation came from this build. Still inspect current changes before editing; never overwrite new user work. Don’t package .env/.data/node_modules/.venv or blindly delete recordings. No memory update was requested or written; older PRD-only memory wasn’t used as current implementation authority.

## System Design & Interfaces

### Existing data/control flow

FastAPI + SQLite WAL serves React/TS/Vite. Field capture normalizes audio with ffmpeg, calls Groq STT/extraction, and creates immutable source + job + reviewed draft. Sent canonical bounded CBOR goes through the shared simulated transport. The receiver applies report only after authenticated delivery; then Operations.on_report builds brief, closures, route/resource assignments, internal review tasks and prepared messages. Outgoing approval binds exact text, recipients, expiry, source revision and replacement. Browser IndexedDB completes before the field receipt; acknowledgment doesn’t answer questions.

Atlas uses actual OSM road/landmark elements, vehicle/access filtering, directed one-way edges and simple via-node turn restrictions. Snapping uses the largest weakly-connected road component but path search still follows directions. Closed segment IDs exclude either direction. Alternatives penalize the first path. No supported path produces a hold/review, never a straight-line driving route. Dotted endpoint gaps remain disclosed. Local place/catalog matching doesn’t send call text to a public geocoder.

### Live audio/control flow

LiveIntake starts only on a microphone button gesture. MediaRecorder collects500ms chunks; about every5seconds it posts the entire recording prefix, including the media header, so ffmpeg can decode it. Only one snapshot is in flight; backpressure skips redundant intermediate work. Browser capture stops at30seconds. A final snapshot waits for earlier work, then STT is reused for the normal extraction job so final audio isn’t transcribed twice. A10second verified call had2audio updates+1extraction. Server accepts at most8audio updates, with <=10MiB and normal decoder duration checks. No browser SpeechRecognition/extra provider, no installed ASR weights.

The intake has a reusable dedicated reporting session, actual immutable source IDs and explicit shared_with_operator metadata. Partial transcript/place previews live in the operator-scoped intake record. They don’t become facts/reports/units. Final STT creates a normal source/job at the dedicated session origin; only the intake’s correlated job/draft is returned by its operator-only snapshot. Generic /api/jobs,/api/drafts,/api/source audio rules remain private. The explicit capture UI doesn’t expose any ordinary unsent field source.

Finished facts are reviewed in the panel. A transcript edit creates another immutable source and normal job, invalidating old unsent drafts and binding the intake to the new one. Add reviewed incident requires exact current intake/draft IDs/versions and reviewed=true. It uses Domain.send_report with the real session origin, so all existing receiver route checks and the bounded link remain. On actual receive, the parent selects the new incident and normal policy assignments run. No direct report-insertion shortcut.

Recording failure keeps the full clip in operator-scoped IndexedDB for Retry/Discard. Cancel marks the intake canceled, stops browser tracks, and ignores a late STT result; no later draft/pin is created. Successful partial server audio/normalized files are removed after use; final source audio remains under ignored runtime data. Restart/refresh can leave an interrupted call; the UI explains how to edit/retry/discard before another capture. No invisible success/fallback transcript.

### APIs

Existing v3 routes unchanged: /api/geo,/api/geo/search,/api/geo/route; report geo confirmation; operations config/replan; units/assignment route; closures; plan tasks; announcements prepare/approve/publish-demo; city scenarios. Versions/Idempotency-Key apply as before.

New operator-only routes:
- GET /api/demo/intake/current: last uncommitted intake or null.
- POST /api/demo/intake: create a desk capture; reject another active listening call; reuse one dedicated session; create uses Idempotency-Key.
- GET /api/demo/intake/{id}: its transcript/place candidates, current correlated job and draft only.
- POST /api/demo/intake/{id}/audio: multipart sequence1..8, final boolean, cumulative audio. Sequence/hash replay guard,3second minimum for intermediate updates, serialized lock. Errors are explicit failed states with retained audio, not fake model results.
- POST /api/demo/intake/{id}/revise: current version/text/reason; source retained, old drafts invalidated and new extraction job created.
- POST /api/demo/intake/{id}/send: current intake version/draft_id/draft_version/reviewed=true, idempotent; normal report send, then queued state/message ID.
- POST /api/demo/intake/{id}/cancel: stop pending intake; already queued report can’t be unsent by cancel.

### Invariants

- Literal source text/excerpts/offsets, numbers, units, uncertainty and original approvals aren’t cosmetically rewritten. Display conversion never mutates graph/storage values or quoted units.
- Ordinary unsent field sources remain private. Operator snapshots contain received evidence; explicit desk-intake endpoints share only their correlated call, never arbitrary source/job IDs.
- Interim places are unreviewed mentions, not event certainty or dispatch decisions. Reporter position remains separate in final extraction.
- No unit double reservation; unavailable/no-route resources produce reviews/holding; no-route unit can’t be marked en route. Released capable units can serve waiting cases.
- Stale road blockage stays excluded until explicitly reopened. No live traffic/full conditional/via-way restrictions claimed.
- Exact advisory approval binds wording/audience/source signature. Local public/contact board does not send outside.
- CBOR<=1024bytes, <=8chunks128bytes, frame<=176bytes, CRC+HMAC16; shared half-duplex airtime/loss/receipt/retries/expiry. No raw audio crosses simulated radio. Receipt != human response/comprehension/resolution.
- Loopback host/origin allowlist and scoped demo capabilities remain. This isn’t production identity management.

## Decisions & Rationale

Mixed-tone work zones preserve the learned queue/map/plan structure and use color for grouping. Fully dark UI would increase contrast against street imagery; a full-map overlay would hide unresolved work. Detail is disclosed instead of repeated in equal-weight cards. Review stays amber and editable/source content has quieter white surfaces. Native fonts/icons and no new imagery/dependencies keep the laptop load modest.

Use cumulative hosted audio snapshots instead of a new paid realtime provider, browser-dependent speech service or local model. It’s near-live at roughly5second intervals, honest about provisional status. Native MediaRecorder and the real configured Groq endpoints were verified with synthetic microphone input. Partial revisions don’t become confirmed source facts until final review/delivery.

OSM/Leaflet/local catalog stays free without Google billing/API key. Basemap is worldwide but search/routing is bounded DTLA. No public Nominatim service is used. Tiles expose viewport/IP metadata; no confidential incident use. Source content goes to Groq only for requested processing. Data is under ODbL and ordinary tile usage respects policy/attribution, with no bulk/offline tile pack.

### Repaired approaches that matter

Initial intake wrappers nested domain-owned SQLite transactions; moved boundaries around existing atomic operations without rewriting global store transaction behavior. Leaflet attribution could intercept a notification button; isolated map stacking and raised the app notice layer. Tint changes exposed low contrast in inactive filters/map buttons/roster/elevated labels; darkened and reran axe. Exact text selectors were migrated after copy changes; source-quote meaning/assertions weren’t weakened. Device-location fit now includes both positions and uses the full accuracy radius, with clear tile failure. Recovery now explains why an interrupted live call needs edit/retry/discard. Direct live links with old fictional-site reports now stay on the city map;2legacy-only intake cases passed (v4-intake-final-legacy-results.json).

## Implementation Details & Commands

Mac Python3.14, existing pinned FastAPI/httpx/SQLite requirements. Node/Vite7.3.7/React19/TypeScript, Leaflet1.9.4, Playwright using installed Chrome at /Applications/Google Chrome.app/Contents/MacOS/Google Chrome. ffmpeg installed; macOS say supports exact local Listen. No browser or model download. Existing Babel parser exports static UI copy, and TypeScript transpileModule supports the Node distance test without another dependency.

```zsh
cd /path/to/comm-control
scripts/start.sh
# another terminal; opens without printing capability
.venv/bin/python scripts/open_app.py
.venv/bin/python scripts/preflight.py
.venv/bin/python -m pytest tests -q --tb=short
npm --prefix web run build
npm --prefix web run test:units
(cd web && npm exec -- playwright test tests/dispatch.spec.ts tests/ui.spec.ts tests/audio.spec.ts tests/intake.spec.ts)
# explicit real hosted calls, synthetic microphone input; separate test database
(cd web && COMM_LIVE_VERIFY=1 npm exec -- playwright test tests/intake-live.spec.ts)
```

Use absolute paths for file writes. A recurring harmless mistake was prefixing work/comm-control or web/ when already running from app/web; do not repeat. Batch independent reads/checks, but run mutations and test suites sharing .data-browser-tests sequentially. Don’t print full failing fixture reprs (they may include test capabilities); redirect results and prefer --tb=short. Never interpolate private keys into shell/tool arguments. Use helpers for authenticated browser opening.

## Verification Ledger

- evidence/v4-backend-results.txt:125passed,22.25seconds,1upstream TestClient/httpx deprecation warning.9new intake cases cover literal preview/intersection, operator-only sharing/no other sources, single-session reuse, partial/final no early dispatch, sequence/replay/rate/size guards, provider failure, cancel race, source revision/stale review and imperial instruction fidelity.
- evidence/v4-units-results.txt:2cases for mile totals/short nonzero precision/invalid values and outward feet accuracy.
- evidence/v4-browser-results.json:16passed,29.3seconds (8legacy,5city/unit,2intake,1native audio).
- evidence/v4-focused-final-results.json:7affected cases passed after final recovery-copy and field map fitting/tile changes. evidence/v4-intake-recovery-results.json is an earlier2-case focused pass.
- evidence/v4-live-browser-results.json and v4-live-intake.json:1actual hosted synthetic microphone flow,3provider calls. Latest raw run report is saved after the final recording check. Map pin before finish, zero interim reports/assignments, full unknown-occupancy draft, review, paused-link hold, received incident and real route/demo unit. No human call/ASR benchmark or RF proof.
- evidence/v4-accessibility.json, accessibility.json, v4-intake-empty-axe.json, v4-intake-ready-axe.json: no serious/critical findings in tested states. Static heuristic0, npm audit0, preflight no weights/key+Free confirmation.
- New screenshots: v4-operator1440/1280, mobile map, live provisional/received/mobile, field feet and actual main/field captures. Original v4-before screenshots preserve baseline. Fresh actual captures wait for map tiles to avoid resize/compositor artifacts in immediate test screenshots.
- Historical v3 hosted city upload flow4calls, v2 MediaRecorder/voice-answer/native playback remain separate. Historical40synthetic text cases initial37/40, tuned rechecks39/40 with one provider400. Not fresh heldout accuracy; prompt/value-style/location changes occurred later and40cases weren’t rerun.
- Source archive integrity/known-secret scan, OSM hash, clean extracted-source API/UI/route/intake startup without bundled key are recorded in v4-release-check.json and release-manifest.json.

### Not run

Real human microphone/speakers, VoiceOver/device scaling, independent unseen complete-fact adjudication, live traffic/emergency navigation, full conditional/via-way/vehicle constraints, phone/SMS/CAD/public alert delivery, physical radio/clock skew/multi-host disconnected operation, Spanish translation, production security, teammate task times, customer/business validation, demo video and hackathon submission.

## Constraints, Risks & Gotchas

Use the authorized launcher; plain localhost links lack access tokens in a new browser/tab context. Don’t remove capability checks just to make a URL clickable. Don’t expose private links publicly.

Loaded atlas bounds34.035,-118.265,34.073,-118.215, timestamp2026-10-17T06:05:57Z,3498190bytes/29040elements. Basemap panning doesn’t add automatic routing coverage. Include the database, manifest and attribution. No live traffic/agency policies; positions/ETAs/resources are demo/static. Stale reports remain excluded until review. Dotted endpoint gaps aren’t driving directions.

The local60requests/hour cap covers all app/eval/snapshot requests and can stop a long demo. Keep Groq Free tier. No paid fallback/account change. A separately upgraded account is outside the local cap’s billing protection. New AI and tiles require internet; cached routing/manual flows/approvals/transport are local. Cumulative snapshots can revise early words; never hide provisional labels.

API tests and browser tests use separate data from actual .data. UI suites are stateful and serial; one test reset can break another suite if run concurrently. Test server8766 can be stale when reuseExistingServer=true; verify its owned PID before restarting. Real default Chrome/speech permissions are separate from isolated automated fake-mic contexts. Automated tests don’t listen to speakers as a person.

## Documents & Artifacts Produced

Current outputs: Comm_Control_v4_Source.zip, Comm_Control_Start_Here.md, Comm_Control_Demo.md, Comm_Control_Verification.md, Comm_Control_PRD.md (original plus amendments), Comm_Control_UI_Copy.md, Comm_Control_Workspace.png, Comm_Control_Field.png, Comm_Control_Mobile_Map.png, Comm_Control_Live_Call.png, Open_Comm_Control.command, SHA256SUMS.txt and this Comm_Control_v4_Handoff_2026-10-17.md. V2/V3 archives/handoffs remain historical. An identical v4 handoff is copied to actual /path/to/local-artifact without replacing a different existing file; packaging verifies matching bytes.

## Attachments & References

User PRD: /path/to/local-artifact Original pasted request: /path/to/local-artifact text.txt. User screenshot of the access page was at /var/folders/q6/6v08vrs14kbfyrl5fzqjc4jc0000gn/T/TemporaryItems/NSIRD_screencaptureui_cqOwjW/Screenshot 2026-10-17 at 6.45.19 AM.png (temporary path may expire). The access issue was resolved through the local launcher.

Primary guidance: https://console.groq.com/docs/speech-to-text ; https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/interimResults ; https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html ; https://www.prepared911.com/ ; https://operations.osmfoundation.org/policies/tiles/ ; https://operations.osmfoundation.org/policies/nominatim/ ; https://leafletjs.com/examples/quick-start/ ; https://www.openstreetmap.org/copyright . Prepared/Zello previously informed workflow hierarchy; no interoperability or reliability claims.

## Output & Working Style

The user wants autonomous implementation with sustained effort, practical evidence and a demo they can open. They dislike generic white/identical panels, stiff AI wording, repeated permissions and stopping at plans. Use concise plain updates, actual local edits and proportional tests. Keep the calm functional minimalist direction, with enough semantic color and disclosure to separate work. Preserve literal evidence/approved instructions rather than cosmetically rewriting history. Miles are the display preference.

Do not commit/deploy/reset actual data/send real outside messages or upgrade accounts without explicit user authority. The task is autonomous implementation, not guided teaching; no learner typing/checkpoint protocol applies. Skills used: prompt, churn, humanize, UI Design Studio art direction/implementation/QA and handoff. No subagents or recurring automations were used. Final replies should lead with the outcome, give the live-demo steps, link the authorized launcher and v4 handoff, and distinguish tested synthetic microphone input from unperformed human/operational validation.
