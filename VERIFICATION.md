Current release: see [v6.5 start guide](docs/V6_5_START_HERE.md), [demo guide](docs/V6_5_DEMO_GUIDE.md) and [verification](docs/V6_5_VERIFICATION.md). Historical version notes below are superseded where they conflict.

# Current verification

See [V6_4_VERIFICATION.md](docs/V6_4_VERIFICATION.md) and the passing v6-4 evidence logs. Older records below are historical.

# Comm Control v4 verification

Verified October 17, 2026 Pacific, on this Mac. This release adds quieter color zones, humanized product copy, imperial display units and a live microphone-to-map demo. The data, real routing preview, source evidence, approvals and constrained simulated link are preserved.

| Current check | Result | Evidence |
|---|---|---|
| Backend/domain/API/model/transport/intake suite | **125 passed**, one upstream TestClient/httpx deprecation warning | evidence/v4-backend-results.txt |
| Distance display cases | **2 passed** | evidence/v4-units-results.txt |
| Browser UI/native audio | **16 passed** in the combined run, plus7focused final rechecks and2legacy-map rechecks | evidence/v4-browser-results.json |
| Hosted live microphone flow | **1 passed**, three actual provider calls in the verified ten-second synthetic run | evidence/v4-live-intake.json and v4-live-browser-results.json |
| Accessibility | No critical/serious axe findings in tested city, legacy, live-empty and live-ready states | v4-accessibility.json, accessibility.json, v4-intake-empty-axe.json and v4-intake-ready-axe.json |
| TypeScript/Vite | Production build passed | web/dist; final JS about512.7kB /153.8kB gzip, with Vite chunk-size advisory |
| Static UI heuristic | 22 files, zero errors/warnings | evidence/v4-ui-static-check.json |
| npm audit | Zero reported vulnerabilities | evidence/v4-npm-audit.json |
| Resource preflight | Built UI, configured key/Free confirmation, ffmpeg, native speech helper and no local weights; about13.9GiB free | evidence/v4-preflight.json |

## Live call evidence

An actual Chrome MediaRecorder captured synthetic WAV microphone input. After the first cumulative audio snapshot, real Groq speech recognition returned a partial transcript and the local catalog found City Hall. The operator map displayed an unreviewed provisional pin while recording continued. There were zero received reports and zero assignments at that point.

Finishing the call sent the final cumulative audio snapshot. A normal source/job/draft pipeline extracted six source-linked facts, including unknown inside occupancy. The operator reviewed and added the report. With the selected link paused, no incident appeared. Restoring the link delivered the bounded authenticated report, then the existing policy engine assigned a demo fire unit and generated a real OSM route shown in miles. No canned transcript, simulated speech-recognition result or direct incident-insertion shortcut was used in this check.

The latest hosted test took15.1seconds (17.6seconds including startup). These are synthetic test timings, not an ASR, response-latency or human-performance benchmark. The live workflow uses roughly five-second cumulative snapshots rather than a subsecond streaming telephone feed. Microphone capture stops at30seconds, with one snapshot in flight and at most8audio updates. Files use the existing decoder limit. The same local60requests/hour cap and Free confirmation apply.

The explicit desk-captured intake is operator scoped and shares only its associated source/draft. Normal unsent field sources, raw audio and other callers remain protected. A transcript/place preview never becomes a confirmed event or resource action. Cancel prevents a late transcription from creating a draft or pin; sequence/hash checks handle replay/out-of-order data. The original transcript remains immutable when corrected, and stale source/draft versions cannot be sent as current.

## Other new checks and repair evidence

Calculated distances are miles and device accuracy feet; raw geographic data remains meters. Precision, small nonzero distances, invalid values and outward accuracy rounding were checked. Source instructions with0.5miles or30feet cannot silently become meters. Literal source quotes and approved messages weren’t humanized.

The new colors and shorter copy were rendered at1440,1280,800,390 and720×500 CSS-space workflows. City and legacy source links, corrections, replacements, exact instruction approval, saved recording recovery, device accuracy and real route detours still work. The live panel handles microphone denial and saved failed audio across reload. The combined browser suite has8legacy,5city/unit,2intake and1native-playback checks. After the last recovery-copy and field-map fitting fixes, all7affected city/intake checks passed again. The7-case report is v4-focused-final-results.json; the earlier16-case report is v4-browser-results.json. Two additional live-intake checks use legacy-only reports to verify that direct live links stay on the city map (v4-intake-final-legacy-results.json). New UI controls were tested against real persisted outcomes; the synthetic provider-outage UI check is explicitly stubbed and separate from real hosted voice evidence.

Early failures were repaired: nested domain transactions in intake, a Leaflet layer intercepting a notice close button, low-contrast labels on tinted surfaces and outdated text selectors. The final suites and rendered checks passed after those fixes. Full VoiceOver, real microphones/speakers, unfamiliar human calls, operational routes, telephony and physical radio remain untested.

## Release boundary

Source ZIP includes the final source, lockfile/built assets, ODbL data+manifest+attribution, tests, docs and selected evidence. .env, capabilities, runtime sources/databases, node_modules and virtual environments are excluded. Package integrity, exact-known-secret scan and clean extracted-source startup/graph checks are recorded by the release script. Historic v2/v3 model evidence below retains its own chronology. The40-case transcript evaluation was not rerun after prompt/style changes, and its tuned rechecks aren’t held-out accuracy.

# Historical v3 verification

Verified October 16, 2026 (Pacific), on this Mac. Synthetic calls and demo units use actual OpenStreetMap streets/landmarks. No real emergency, public alert channel, phone integration, live traffic or agency dispatch was exercised.

| Current check | Result | Evidence |
|---|---|---|
| Backend/domain/API/transport/automation | **116 passed**, one upstream TestClient/httpx deprecation warning | `evidence/v3-backend-results.txt` |
| Production frontend | TypeScript and Vite build pass | `web/dist`, npm run build |
| Browser regression/new city/native audio | **13 passed** | `evidence/v3-browser-results.json`; 8 legacy UI, 4 city/automation, 1 native audio |
| Real hosted city voice integration | **1 passed**, four real hosted calls using two synthetic audio uploads | `evidence/v3-live-city.json`, `evidence/v3-live-browser-results.json` |
| Accessibility | No critical/serious axe violations in selected city and legacy workspace; keyboard, dialog Escape, narrow reflow exercised | `evidence/v3-accessibility.json`, `evidence/accessibility.json` |
| Static UI heuristic | 19 files; zero errors/warnings | `evidence/v3-ui-static-check.json` |
| npm dependency audit | Zero reported vulnerabilities | `evidence/v3-npm-audit.json` |
| Resource preflight | No local model weights, built UI, key/Free confirmation configured; about 11.7 GiB available when checked | `evidence/v3-preflight.json` |

New backend checks exercise real landmark/intersection resolution, vague/caller-only locations, actual directed routes, alternative routes, excluded edges, no-path and outside-coverage outcomes, modeled one-way and turn restrictions, no invented straight-line navigation, closure subject selection, expiration remaining excluded, automatic assignment/resource exhaustion/reassignment, duplicate packets, changed-source approval invalidation, no-route holding and en-route guard, negated hazard without unrequested dispatch, real place names protected in outgoing approval, operator-only new endpoints, valid coordinates, optimistic configuration/route versions and estimated map-point provenance.

New browser checks exercise actual online OSM tile rendering, live clock tick, categorized queue/brief, automatic unit/task creation, source quotation, a saved detour that excludes the blocked graph edge, exact advisory/audience approval before local publication, persistent automation switches, existing-run city scenario control, responsive 1440/1280/800/390 layouts, visible response action and map attribution. Screenshots were visually inspected. The mobile map now scrolls within its pane to keep map controls and attribution reachable.

The city voice check uploaded synthetic native-speech recordings to the real configured Groq provider. Extraction preserved unknown inside occupancy, resolved City Hall and the Main/Temple access report; the local policy engine reserved a capable demo fire unit and found a road route avoiding received closures. A separate operator audio upload produced an instruction retaining City Hall, the Main Street prohibition and occupancy question. Browser review/approval, destination IndexedDB persistence and a returned acknowledgment were exercised. The question stayed open after acknowledgment. This check is four hosted calls, not a human speech/ASR benchmark or live dispatch validation. The earlier v2 MediaRecorder/voice-answer evidence is retained separately below.

## Release and QA boundary

The v3 source package includes the ~3.3 MiB ODbL road extract, manifest, attribution, source, pinned dependencies, built UI, tests and selected evidence. It excludes .env, capability tokens, raw runtime databases, node_modules and virtual environments. Packaging performs ZIP integrity and exact-known-secret scans; a clean extracted copy is checked for graph/route/API startup without a bundled provider key. See the release manifest for exact source hashes and check chronology.

Map basemap browsing is worldwide; automated matching/routing is bounded to the bundled Downtown LA area. No live traffic, time-dependent road conditions, full conditional/via-way restrictions, vehicle height/weight constraints or agency response policy is modeled. Last-mile gaps remain dotted and labeled. A reported blockage is unverified and excluded until explicitly reopened; stale reports request reconfirmation.

Automatic actions are local demo reservations, route recalculation, case briefs and internal review tasks. Caller messages retain the actual reviewed return transport. Contact notes/public advisories publish only to a local demo board, after exact wording/audience approval. None of these records contacts outside people or services. Device location is optional, visually distinct and never substitutes for event location.

Manual gates remain: actual microphone acoustics/speakers, VoiceOver and real device scaling, unfamiliar/unseen call phrasings with independent human adjudication, operational route verification, teammate usability/task times, timed rehearsal and any real integrations. The 40-case historical transcript evaluation below was not rerun after the real-location prompt extension; no held-out or production accuracy claim is made.

## V3 repair history

- Isolated service/parking nodes initially produced no useful snap; routing now snaps within the largest connected road component while preserving directed edges and restrictions.
- A named cross street could be mistaken for the blocked subject; closure matching now requires a grounded blocked subject and excludes the corresponding segments.
- A later closure leaving no path now holds the demo unit and prevents marking it en route.
- Expiring a reported blockage no longer silently opens the road; stale reports remain excluded pending review.
- Released units now trigger resource reconsideration for waiting cases.
- Negated hazard/information-only updates no longer create an unsolicited resource assignment.
- The fixed response footer, contrast corrections, evidence tab navigation, source-to-world-map focus and scrollable mobile map were repaired and checked in rendered browsers.
- Early browser failures included stale selectors, a duplicate advisory selector and test-worker resets cascading through stateful tests. Selectors were scoped, tests marked serial, actual contrast defects fixed; the final 13-check run passed.


# Historical v2 verification (retained evidence)

The following records describe the earlier fictional-site release. The v3 checks above cover the current implementation; historical model evaluation is not a new evaluation of the extended location prompt.

Verified October 16, 2026 on this Mac (Apple M4 Pro, 24 GiB RAM). This ledger separates working software from operational claims. Source and site identities are synthetic. No real emergency, RF network, production deployment or human usability study was tested.

## Passed engineering checks

| Layer | Result | Evidence / reproduction |
|---|---|---|
| Backend/domain/API/codec/model-boundary suite | **87 passed**, one Starlette TestClient/httpx deprecation warning | `.venv/bin/python -m pytest tests -q`; `evidence/backend-results.txt` |
| Frontend | TypeScript and production Vite build passed | `npm --prefix web run build`; built assets in `web/dist` |
| Browser UI | **8 passed** | `web/tests/ui.spec.ts`; `evidence/browser-eight-tests.json` |
| Native audio on final playback code | **1 passed** | `web/tests/audio.spec.ts`; `evidence/native-playback-final.json` |
| Hosted speech loop | **1 passed**, real provider calls with synthetic speech | `web/tests/live.spec.ts`; `evidence/live-voice-e2e.json` |
| Accessibility | No critical/serious axe violations in populated workspace; keyboard skip link and dialog Escape exercised | `evidence/accessibility.json`; this is not a VoiceOver certification |
| Static UI heuristic | No errors; focus styling reviewed and explicit focus-visible ring retained | `evidence/ui-static-check.json` |
| Dependency audit | npm reports zero vulnerabilities | `evidence/npm-audit.json`; no claim of a complete security audit |
| Source delivery | Archive integrity and known-secret scan passed; clean extracted source served UI and created a session without a bundled key | Source ZIP excludes private runtime/dependency folders |
| Resource preflight | Built interface, ffmpeg, key configured, Free confirmation, native speech helper; no weights | `scripts/preflight.py`; `evidence/preflight.json` |

Backend coverage includes literal evidence/Unicode offsets, reporter/event separation, ambiguous/unlocated/parent-only geometry, negative/unknown occupancy, protected instruction clauses, frame authentication/tampering, body limits, paused transport, reordered/duplicate delivery, closed-recipient receipt boundaries, return-path human responses, restart, expiry, five-batch exhaustion, idempotency, approval/audience binding, stale edits, malformed requests, private source access, exact reset phrase, 20 turns across 10 sessions, silent/corrupt/overlong audio, provider failures with retained sources, relative/unknown time, operator estimates, sent corrections/out-of-order dependencies, same-session replacements and retry correlation preservation.

The eight UI checks exercise populated queue/map/source links, 1440/1280/800 layouts, 390-pixel field reflow, reviewed exact instructions, IndexedDB-before-receipt behavior, Cannot follow return, keyboard/axe, count correction, estimated location, service outage/reconnect, narrow 720×500 reflow/dialogs, microphone denial, pending upload recovery after reload, reviewed replacement delivery/history, session creation, real simulator controls, trace, export, guarded reset and setup. Screenshots were inspected, not just generated. The 720×500 check approximates the CSS space of a 1440×1000 view at 200% zoom; actual macOS display-scale/VoiceOver/device testing remains a presenter check.

## What the voice E2E established

An actual browser MediaRecorder captured native synthetic speech through Chrome's fake microphone WAV input. The recording went through real Groq STT and extraction; smoke, two people outside, unknown occupancy and source provenance were checked. With transport paused, nothing appeared in the operator projection; restoring it delivered the report.

An operator synthetic audio recording was uploaded and processed through real STT and instruction drafting. The test checked the north-gate prohibition and inside question, approved and sent the draft, confirmed recipient IndexedDB persistence, and observed actual HTMLAudioElement progress during exact-text native playback. A Received tap left the question open. A separately recorded synthetic voice answer crossed the return transport and appeared as a source-linked answer candidate in the right thread. The test took about 26 seconds on the Local direct profile, including approximately 12 seconds of recording. This is not modeled-radio latency or a human speech benchmark.

A later no-AI playback check verified the final native helper/player code using an exact manual instruction: Audio readyState ≥2, currentTime >0 and paused after Stop. Audible speaker quality was not judged by a person.

## Hosted model evaluation

`fixtures/evaluation-cases.json` contains 40 frozen **synthetic transcript-level** cases, not 40 audio clips. Actual Groq calls were paced at 20 seconds to respect the Free tier.

| Category | Initial frozen run | Prompt-guided failed-case rechecks (combined) |
|---|---:|---:|
| Clean inbound | 18/20 | 20/20 |
| Difficult inbound | 9/10 | 9/10 |
| Outgoing protected-field checks | 10/10 | 10/10 |
| Total case-level pass | **37/40** | **39/40** |

Initial clean misses: a door malfunction classified as access instead of observation, and a help request phrased as a question marked uncertain. The difficult hypothetical-fire case was classified hypothetical hazard instead of hypothetical fire. A general taxonomy clarification was added to the prompt. Both clean misses passed on recheck; the hypothetical case's recheck returned provider HTTP 400 and safely failed with source retained. No error was replaced with a canned result. `evidence/model-evaluation-initial.json` and `evidence/model-evaluation.json` retain both results.

The rechecks reuse the same cases after tuning, so **39/40 is not a fresh held-out result**. The scoring script checks one expected main fact's kind/assertion/count/location, or outgoing literal protected fields. It does not establish complete fact recall, extra-claim precision, semantic equivalence, clinical accuracy or ASR WER. Initial median hosted call time was ~0.49 s clean, ~0.52 s difficult and ~0.42 s outgoing; those numbers exclude recording, queueing, normalization, transport and human review. Max initial call time was ~1.01 s. Do not promote this small sample into an SLA.

## Failures repaired during implementation

- An initial provider structured-output failure on a longer turn: bounded output increased and low reasoning effort selected. Unsupported excerpt failures still surface explicitly.
- Model output could place a question only in a side list: the actual recipient text now includes normalized direct questions and approval validates protected source details.
- New instructions could replace the active reading context: new-arrival notice now requires deliberate selection; replacement state changes only after delivery.
- Premature spool receipts: browser IndexedDB completion is required for field receipt; a closed tab remains unconfirmed.
- Received review status incorrectly matched “unreviewed”: compact codec now checks the distinct reviewed suffix.
- Unknown event time was equated to message issue time: capture, issue, receipt and explicit observation time now remain separate.
- A failed correction retry could lose its source revision/target: retry keeps the immutable source ID and correction correlation.
- Accessibility/contrast/SVG naming defects, stale build test runs and narrow layouts were repaired and rerun.
- A browser startup/reset run timed out. File cleanup now runs off the event loop; subsequent eight-test runs passed, including a 16.8-second run. The exact macOS cold-start delay was not isolated.
- A first playback assertion used a Chrome response-body capture that returned zero bytes despite a valid generated WAV. The check now verifies actual player readyState/currentTime, and a final native-playback test passed.
- Some test failures were harness issues (stale selectors and reused idempotency keys across distinct operations); the application guard correctly rejected the latter.

## Acceptance mapping and remaining product gates

A01/A09/A10 have actual connected synthetic voice evidence, replacing the original local-AI assumption by direct user instruction. A02–A08/A11–A14/A19–A24 have backend and/or UI evidence as described above. A15 is amended: disconnected AI is not delivered; local assets/manual operation and explicit AI failure paths are implemented. A16/A17 have browser reflow/keyboard/axe/screenshots, with real assistive-device/display testing still unperformed. **A18 teammate usability, task times and timed rehearsals have not been performed.** Do not claim the original 60-case human-annotated audio protocol or all intended product gates passed.

Human microphone acoustics, real speaker listening, independent source adjudication, unseen paraphrase evaluation, a production security review, multi-host clients, telephony, Spanish translation, physical radios/clock skew, fully disconnected inference, customer interviews, business economics, a demo video and hackathon submission remain outside the verified release. No known failing engineering check blocks the implemented local connected-AI prototype.
