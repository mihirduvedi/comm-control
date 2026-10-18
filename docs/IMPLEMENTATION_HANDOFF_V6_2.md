# Comm Control v6.2 continuation handoff

## Current task and completion state

This run implements the user's successive scroll/design corrections and a major USC facilities mode. See V6_2_VERIFICATION.md and evidence/v6-2-release-check.json for final checks. Finish with actual microphone/speaker rehearsal, recording and event-specific submission work. Do not add a public deployment or submit without an explicit instruction.

Authoritative source: /path/to/comm-control. Chat workspace: /path/to/local-artifact User-facing files are in that chat's outputs folder. No Git repository or AGENTS file was found. Port8765 uses private .data; tests use8766 and .data-browser-tests. Inspect lsof/current active jobs/intakes before restarting; do not interrupt a real recording. Private backup: .data/backups/before-v6-2.sqlite3. All 11 report IDs and 21 immutable source objects were preserved at final audit; later user activity may change counts. No actual reset or new USC seed was performed. Credentials, run keys, database, audio and saved-run archives must never enter a release.

## User direction and final design decisions

Keep parsing, source-linked mapping and coordination equally strong for hackathon submission. The user wants a white/light-blue canvas, blue borders, rounded modern panels and restrained glass. No full-width dispatch divider, colored queue stripes, gray route-option blocks or Setup highlight. Keep one fixed speaker voice; original recordings use their own voice. The header is rounded and floating. Its central space now holds a working Live call shortcut. It opens the same intake without losing an already open call, and works from other routes and on mobile.

Body fonts were explicitly rejected twice: IBM Plex felt skinny, vertical and formal; a Source Sans trial was also rejected. The final body uses the SAME macOS/system family as the existing bold titles, with regular/medium weights. Bold heading styling stays. Unused downloaded font assets are excluded from the source release. Do not restore Plex, Source Sans or the earlier broad Avenir based on stale documents.

SlidingBar.tsx measures the selected tab and animates a shared rounded outline between adjacent buttons. It is used for navigation, map mode, incident filters, detail tabs, mobile tabs and facilities filters. Resize/font changes update its position; overflow is clipped to avoid transient mobile horizontal overflow. Reduced motion removes the animation. Navigation still follows its actual routes; no handler/auth contract was replaced for decoration.

The middle panel previously hid overflow on desktop and let its map shrink below the internal content height. It now scrolls in all widths with a useful map minimum. City wheel input scrolls the panel, with +/- controls for map zoom. A focusable panel supports keyboard scrolling. useDragScroll.ts uses animation frames and pointer edge proximity so a native queue drag scrolls continuously at either edge even when the pointer pauses. Drop/leave/end/unmount stop the loop; manual order still persists through the existing versioned API.

## USC replaces the fictional site

The user's final correction removed the fictional campus UI entirely, folded its useful tools into USC and requested a closer custom simplified map. Only City map and USC campus remain. Resources has city/USC context. The old site URL resolves to USC, the New test picker has no fictional campus, Simulator queues USC fixtures, and unused SiteMap/CampusResources React files were removed. Do not reintroduce the warehouse UI. Legacy source vocabulary and old backend compatibility remain solely so stored reports and transport regressions are readable; saved warehouse reports are not silently remapped. Locate at USC requires an explicit building and recorded reason, preserving original source words. Inspector correction choices now use USC buildings.

server/usc_atlas.py loads data/usc-campus.osm.json and builds a real outdoor pedestrian graph. data/usc-campus.manifest.json contains source/query/bounds/hash/license. Eight selectable buildings: Seeley G. Mudd (SGM), Michelson Center (MCB), Seaver Science Center (SSC), Kaprielian Hall (KAP), Leavey Library (LVL), Tutor Campus Center (TCC), Bovard (ADM), Hughes Engineering (EEB). Context footprints are also real OSM geometry. Public references: https://fpm.usc.edu/wp-content/uploads/2022/09/UPC_BaseMapGrid_36x48_20220906.pdf ; https://transnet.usc.edu/index.php/about-us/entrance-hours/ ; https://www.usc.edu/how-to-access-campus/ . Gate coordinates are approximate and current access starts unreviewed. OSM entrance tags are not certified exits. Indoor exit/room geometry was not invented.

USCMap.tsx is a custom SVG plan, with no raster tiles or satellite service. It projects actual coordinates, simplifies paths, renders building codes/context, routes/arrival gaps, access points/gates and simulated teams. Default is the closer building view; building selection zooms further, Fit campus includes wider access points. Pan, zoom, layer switches, source/access detail, a north indicator, correctly changing scale bar and a map key remain. Arrow keys pan a focused map; +/- zoom; Enter chooses the center/nearest path while marking. Mouse access/path picking and explicit source notes are supported. City Leaflet/OSM tiles remain separate.

## Facilities data and behavior

server/usc_ops.py registers /api/usc/operations, ticket/asset/gate versioned updates, persistent closures and reviewed access points, plus explicit operator-entered report intake. USCResources.tsx at /resources?view=usc shows work items, asset checks/history, teams, gate reviews and source attribution. USCResponse integrates with normal workspace caller messaging and history. Source links always open the original report.

Six explicitly simulated example reports in usc_scenarios.py cover 145psi then220psi for the same demo nitrogen tank, a possible gas leak at MCB, a sounding smoke alarm without visible smoke at Leavey, a TCC service-door problem and a KAP flickering light. Fixtures have explicit annotations and travel through normal constrained transport; they do not pretend to be hosted model output. Use New test → USC facilities to archive the current run and queue them; never reset the actual run just for screenshots.

Four demo assets, six simulated facilities/lab-safety/alarm/access teams. PSI values retain signs and exact source linkage. Only an identified demo tank inherits its configured demo range; unknown tank IDs remain separate, with no guessed manufacturer limit. Range changes affect future reports; receipt-time assessment stays in earlier readings. No sensor, valve, USC employee, agency, real dispatch or GPS is connected. Gas/alarm review priority is source-based demo policy, not a clinical/industrial protocol. Explicit negative clauses are guarded. The model extraction prompt preserves readings, units, equipment identity, building/room wording and alarm-vs-observation distinctions. No model weights were trained.

Same building/asset/issue reports share a work item, incident association and source history. An abnormal later reading can escalate an unstarted maintenance assignment to lab safety. Existing progressing assignments are not casually diverted. Unknown identities do not merge. Manual separation persists, and relocation updates work membership while source objects stay unchanged. Ticket stages, review notes, history, availability and route hold are stored. Closing source cases releases a shared response only when none remain; operator-resolved work is distinct from source-case closeout.

Dijkstra routes follow cached outdoor paths, with a separately stated arrival gap, no invented indoor route/vehicle access/evacuation certification. Reported named-road closures and manual path/gate reviews exclude segments persistently. Newer explicit matched clearance or a reviewed manual opening clears them; older observation times do not supersede later reviews. Gate geometry is approximate and linked to nearby graph segments. No path yields a hold, never a made-up line through a blockage.

Live preview recognizes literal USC names/codes. Live event review supports a confirmed supported USC building, while city routing retains its own bounds. Location holds block campus assignment too. Campus confirmation and held-location transport are regression-tested through the live intake API using clearly synthetic model adapters. Existing real hosted speech checks are historical v6 evidence; no new hosted v6.2 speech accuracy benchmark was claimed.

## Verification, artifacts and working style

Strict TypeScript/Vite build and the final 214-test backend suite passed, including the final source-resolution guard. USC focused tests cover source resolution/ambiguity, asset reading aggregation/history, signed values, denied hazards, appropriate resources, access persistence, manual locations, auth/version guards, raw transport, live confirmation/hold and separation/relocation. The full Chrome suite passed 30 tests, with four hosted opt-ins skipped. It exercises actual mouse drag edge scrolling, wheel/keyboard panel reach, sliding outlines/reduced motion, existing caller/case/reset/transport flows, USC work items and mobile overflow/axe. Both formatting tests passed. A normal WebSocket disconnect on close is handled without a spurious traceback.

Release: Comm_Control_v6_2_Source.zip; Comm_Control_v6_2_Handoff_2026-10-17.md; current Start_Here, Demo_Guide, Verification, UI_Copy and USC screenshots; existing Open_Comm_Control.command. An identical handoff is saved in Downloads. Clean extraction boot, resource auth, static assets, OSM catalog and release hash checks are recorded separately. Do not use old v6/v6.1 ZIPs as the latest source.

The user prefers sustained autonomous implementation, concise candid updates and no routine permission prompts. The named churn/prompt/design/uidesign/humanize workflows were applied. No subagents were used. Distinguish attached document context from actual user instructions. Maintain source privacy, uncertainty, explicit location review, confirmed-vs-provisional state, exact approval wording, same-session receipts and reversible saved tests. Keep the next work focused on finishing and submission unless the user extends scope again.

## Historical architecture background

The sections below retain useful v6 context. Historical font/site choices and test counts are superseded by everything above.

## Preserved architecture and v6 background

The following sections describe the preceding v6 implementation. Its historical counts and hosted measurements are scoped to that version; the current changes above take precedence.

## Architecture and Preserved Invariants

FastAPI serves React19/TypeScript/Vite, Leaflet and a bundled real Downtown LA OpenStreetMap graph. SQLite WAL stores documents and immutable event history. Source recording/text → interpreted draft → human review → constrained authenticated simulated transport → received report → response plan remains the core contract. Provisional live pins cannot reserve resources. A paused link prevents incident projection and assignment. Field sessions remain isolated; operator cannot read ordinary unsent private field sources. Live desk capture is a separate explicitly shared operator-only demo intake. Original source, uncertainty, literal quotations, observation times, report corrections and delivery receipts remain separate from derived interpretation.

Case history supports ownership, handover, monitoring, guarded closeout, release, reopen and download. Closing a case retains road reports and unresolved questions; acknowledgment does not answer a factual question. Prepared advisories and outgoing wording/audiences still need approval and stay inside the demo. No agency CAD, real dispatch, phone service, radio hardware or real GPS is connected.

## V6 Decisions and Behavior

### Threat tuning

New append-only compact-protocol kinds: violence, self_harm, medical, basic_need. Existing CBOR kind indices are unchanged. Extraction prompt has specific threat, negation, occupancy and event/caller examples. `server/threats.py` supplies source-grounded semantic checks and versioned review priority. It rejects occupancy without matching source words, recovers explicit missed critical clauses, separates combined threat sentences so negation doesn't spill into another threat, preserves evidence offsets and normalizes empty/none values. Medical reinterpretation retains explicit counts/plain summaries. The literal source remains visible and must be checked.

Demo priority: explicit gun/serious violence and self-harm100, major medical signals98, secondhand/uncertain critical evidence92/94, asserted fire92, ambiguous immediate danger85, smoke72, unknown occupancy65, access45, basic needs25, routine observations20 and context5; negated/hypothetical0. This is transparent review policy, not an official clinical protocol. Urgent-attention packets remain critical. Explicit operator priority overrides persist with a reason and survive replanning. The queue sorts active cases by priority, then action state/time, with closed/superseded last. Existing “train” wording is preserved; its danger language is flagged for review rather than inventing a collision.

No model weights were fine-tuned. Groq Free cannot supply the desired trained adapter workflow; its documented LoRA inference is enterprise-only and training is external. We used the existing configured openai/gpt-oss-20b with better prompts, semantic guards and measured cases. Official reference: https://console.groq.com/docs/lora. Do not describe this as a trained emergency model.

### Live location and allocation

`LiveLocationReview.tsx` lets the operator choose a proposed place or local search result. Caller-only position is never automatically treated as event location. “Keep location unconfirmed” sends an explicit hold, including when a draft already proposed geometry; the report can arrive but allocation stays blocked. Selected coordinates are finite and bounded by the loaded atlas, with version/current-draft checks. A received report gets the reviewed pin as an audited operator annotation only after normal transport delivery. The raw source location words remain unchanged. This annotation is local operator state correlated with delivery; it is not a claim that the compact packet transmitted full geometry. Replaying an already-sent call cannot silently change the reviewed pin.

Operations distinguishes missing capability, busy/unavailable units and available units without a supported route. Adding demo capacity or releasing a resource automatically reconsiders waiting cases. A critical case can transfer only an unstarted assignment whose prior priority is more than30 points lower; en-route/on-scene resources are never automatically diverted. The old plan reopens a waiting task and records the transfer. Unit arrival updates its saved map position with `operator_marked_arrival`, not a fabricated live telemetry stream.

### Resources

GET `/api/resources` is operator-only and projects persisted active assignments, capability counts, units, grouped destinations, waiting reasons, routes, closures and atlas/config. POST `/api/units` is operator-only, idempotent and validates a unique name, supported capability and known base place, max40 roster units. Unit changes retain existing versioned PATCH `/api/units/{id}`.

New `/resources` navigation has one count strip, allocation map, By area list, unit roster and waiting cases. Capability filters affect map/areas/roster; area selection focuses map and roster. Links open the actual incident. Add/update dialogs persist changes and refresh live state. No-match/no-allocation, loading, bad input, stale update, tile failure and lost API connection have explicit outcomes. Offline retains last saved values and disables mutations. Map letters are simulated base/arrival positions; numbered circles are allocation destinations. Routes and active/stale closures are visible. No vehicle movement is simulated as GPS.

### Road persistence and clearance

Active and stale closures stay excluded for all future route calculations; 30-minute age creates reconfirmation work, not reopening. A later asserted direct clear/open/cleared/reopened/passable statement naming the same road and matching mapped segment can reopen it. Hearsay, uncertainty language, caller-only locations, vague/no-match, another crossing street and explicitly older observations cannot clear it. Provenance includes the clearance report and exact excerpt. Manual reopening still requires reason/version. Any road revision recomputes saved routes. A previously blocked route can become ready again, but the held unit stays holding until the operator marks it en route; a review task records that access returned. Closing an incident never reopens a road. These are cached graph previews, not live traffic/navigation guarantees.

## Design and Copy

Chosen direction: Operations atlas. Dominant map, narrow incident/response ledgers, white reading surfaces, blue-gray edges, rounded glass chrome, small state colors. Rejected dense CAD grid and repetitive glass-card gallery. Original system sans restored; normal body weights,600 headings and tabular counts. The active nav pill is centered and the inherited underline removed. One type selector replaces the tall colored category stack, freeing queue space. Mobile keeps Queue/Map/Details; Resources stacks as map→areas→roster. Messages/audit remain disclosed on demand. No generated raster images were needed. User-requested glass is controlled, static and supports reduced transparency.

Copy is direct: Resources, Response plan, By area, Unit roster, Waiting for coverage. Source excerpts, names, approval wording and historical records stay verbatim. `docs/V6_UI_COPY.md` contains only revised copy and is also supplied as a copyable file. Design contract and exact screenshots explain spacing/type decisions. The static blur heuristic warning was reviewed against rendered surfaces; it isn't an accessibility failure.

## Exact Changed/Added Files

Backend: new `server/threats.py`, `server/resources.py`; changed `server/models.py`, `server/site.py`, `server/transport.py`, `server/domain.py`, `server/operations.py`, `server/geography.py`, `server/intake.py`, `server/main.py`.
Frontend: new `web/src/Resources.tsx`, `ResourceMap.tsx`, `LiveLocationReview.tsx`, `atlas.css`; changed `main.tsx`, `types.ts`, `Operator.tsx`, `OperationsPanel.tsx`, `LiveIntake.tsx`. Existing styles are retained in import order; atlas.css is last. Do not revive deprecated theme values by changing earlier files alone.
Tests/eval: new `tests/test_threats.py`, `tests/test_resources.py`, `scripts/evaluate_threats.py`, `web/tests/resources.spec.ts`; extended `tests/test_intake.py`, `tests/test_operations.py`; updated semantic claim lookup in `tests/test_core.py`; updated intentional canvas expectation in polish.spec, test wait in intake.spec and obsolete answer expectation in live.spec.
Docs: updated README; new V6_PLAN, V6_DESIGN_CONTRACT, V6_UI_COPY, V6_DEMO_GUIDE, V6_VERIFICATION, IMPLEMENTATION_HANDOFF_V6. Prior v5/v5.1 handoffs remain architectural history; their old font/header/picker descriptions are superseded.

## Verification Ledger

189 backend tests passed (27.81s), versus147 baseline. Final normal Chrome suite22 passed/4 hosted opt-ins skipped (57.9s). All four opt-in hosted flows passed across this run. An all-opt-in run had25/26 because of an obsolete answer fixture assertion; after repair the focused live/Resources/polish run passed3/3 (40.8s). Don't call it one26/26 run. Hosted extraction+guard sample10/10;2 formatting tests; strict build passed. Largest JS375.22kB. Static29 files0errors1 reviewed glass warning. Serious/critical axe passed in changed desktop/mobile states. Saved9 actual reports and original source texts preserved. Preflight passed.

Important repairs: preserved urgent packets after on_report recalculation; separated threat-clause negation; corrected smoke-as-location-only; reopened waiting tasks when capacity is lost; preserved manual urgency; distinguished shortages; retained medical counts/plain wording; fixed navigation stretch/underline; darkened unavailable marker contrast; stale fixture expected two inside but current provenance says outside/inside unknown. A hosted ASR run rendered “Two” as “The”; we kept unknown count instead of fabricating it. No broad ASR accuracy claim.

Exact command examples, from source:

```zsh
.venv/bin/pytest -q
npm --prefix web run build
npm --prefix web run test:units
npm --prefix web run test:e2e
COMM_LIVE_VERIFY=1 COMM_NATURAL_VERIFY=1 npm --prefix web run test:e2e
.venv/bin/python scripts/evaluate_threats.py --run
.venv/bin/python scripts/preflight.py
```

At the final hosted-check audit, 56 of the 60 app requests in the preceding hour had been used; 4 remained and slots expire on a rolling basis. Avoid further hosted tests just for repetition. Saved reports, cached playback, local maps/routes and resource controls remain usable. Hosted commands consume the existing Free-tier request budget (60 calls/hour shared app cap); don't rerun without cause. All mutating browser tests use8766 and a dedicated test store. Real hosted means actual model API inference on fictional fixtures, not an actual human emergency call. Main visual captures include1440/1280, mobile/tablet and Resources390. User hardware listening/usability, physical radio, clinical validation, production security and actual emergency operations were not tested.

## Configuration, Privacy and Release

Private `.env` has the configured Free-tier key; `.data/run.json` has durable capabilities. Never print, commit or package either. Never package databases, source recordings from runtime, backups, provider logs, dependency caches, browser auth state, temporary tickets, models or test stores. The source ZIP includes editable code, built assets, pinned dependency manifests, OSM data/attribution and explicit synthetic fixtures/provenance. It does not include installed dependencies or a usable provider credential. A new copy requires setup and its own Free-tier key/terms acceptance. Existing user's Orpheus acceptance and fixed voices are preserved: operator Hannah; Alex Autumn; Jamie Troy; Jordan Diana; Sam Austin; Taylor Daniel. Other names have stable persisted assignments. No picker or cloning. Keep source recordings distinct from generated speech.

Actual app start: `scripts/start.sh`. Existing Mac launcher reuses a healthy server and mints normal access. User's browser access is eight hours; private one-use launch tickets expire after30minutes. Do not put durable operator tokens in links. External AI/tiles need internet; only cached roads/places support offline geometry. Atlas boundaries are explicit and no unknown location is silently snapped into dispatch.

