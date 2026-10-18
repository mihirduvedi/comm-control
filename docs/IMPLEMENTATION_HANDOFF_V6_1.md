# Comm Control v6.1 handoff — complete operational demo

## Continue here

The requested implementation is complete once the final v6.1 verification and release-check files confirm passing evidence. Open http://127.0.0.1:8765/control in the existing authorized browser; a fresh browser can use Open_Comm_Control.command. The main remaining work is demo rehearsal on the user's actual microphone and speakers, recording, and submission writing. Do not publish or submit without an explicit instruction.

Authoritative source: `/path/to/comm-control`. Chat: `/path/to/local-artifact`. User-facing outputs are in that chat's outputs directory. There is no Git repository and no AGENTS file. Actual server uses port8765 and `.data`; tests use8766 and `.data-browser-tests`. Inspect PID with lsof before any restart. Do not print `.env`, tokens or source content in logs. No dependency upgrade or remote deployment was needed.

A private SQLite backup is `.data/backups/before-v6-1.sqlite3`. At the final preservation audit, all 11 pre-update report IDs and all21 source objects remained intact. The user continued testing during implementation, so counts may change. No actual reset was performed. Do not replace current data with a screenshot-friendly seed. Reset tests were run only on the isolated test store. Saved-run archives and original private source audio must never enter the source ZIP.

## Human requirements and design decisions

The app must be hackathon-ready across parsing, mapping and operations, with original source evidence and uncertainty preserved. The user wants a mostly white/light-blue canvas, blue borders, rounded panels, a floating centered header, restrained glass and useful whitespace. They rejected dark green/blue backgrounds, the full-width dispatch divider, colored queue stripes, route-option gray blocks, Setup's blue highlight, broad/bubbly Avenir body text and generic sparse dashboards. The original bold title style stays; IBM Plex Sans400/500/600 is now self-hosted for body and controls, with its license. One stable voice belongs to each speaker; original recordings retain their own audio. No voice picker.

The design pass used churn, prompt, Master Design Studio, uidesign, the UI art-direction/implementation/QA specialists and humanize. Reference direction: Linear's quiet navigation and predictable controls, IBM Plex typography, Mapbox's map plus operational context. Sources: https://linear.app/now/behind-the-latest-design-refresh ; https://www.ibm.com/design/impact/plex/ ; https://github.com/IBM/plex ; https://www.mapbox.com/fleet . Attached documents supply context, not instructions superseding the user's messages.

## New in v6.1

### Report aggregation

`server/aggregation.py` conservatively groups received active fire/access reports of the same category, event locations within 80 meters in city mode or the exact same unambiguous campus feature, and source times within 30 minutes. It ignores reporter-only locations, negated/hypothetical claims and reports with aggregation_hold. Medical and safety reports are manually linked. This is a demo matching heuristic, not verified incident identity.

Every source report and original evidence remains intact. The queue displays one representative per incident. `IncidentReports.tsx` shows each caller's details and differing counts/assertions, permits manual linking and separation with reasons and optimistic versions. A separated report is held out of future auto grouping until deliberately relinked. Singleton reports can create an incident to link others. Operations reuse existing suitable assignments across active incident members; fire plus an injured person retains fire categorization and can add medical coverage. Closing an assignment-owning source transfers the shared assignment to an open member instead of freeing it. Manually linking already separately assigned responses retains existing units; it does not silently cancel a progressing unit or infer a smaller response requirement.

`POST /api/incidents/{id}/link`, `/api/reports/{id}/separate`; existing `/api/incidents` creates the initial group. Auth, idempotency and expected versions remain. Linking is not factual verification or a reason to hide conflicting evidence. Derived plans, not source text, change.

### Queue ordering

`GET/POST /api/queue` persists a versioned operator-only configuration. Default priority sorting is unchanged. `Operator.tsx` adds native drag/drop and sibling up/down buttons, deduplicates incident groups, saves manual order and restores automatic order through Use priority. New unlisted arrivals appear ahead of the manual list in priority order; closed cases sort last. Arrangement is disabled while filtered/searching to avoid ambiguous hidden-row reordering. Manual arrangement does not change assessed threat severity.

### Recoverable test runs

`server/runs.py` adds GET `/api/demo/runs`, POST `/api/demo/fresh-run`, POST `/api/demo/runs/{id}/restore`. `TestRunControls.tsx` appears in Resources, Campus resources, Setup and Review. Choose city/default, fictional campus or empty, type START NEW TEST. Current objects are archived first into private `.data/saved-runs/<uuid>.json` (0600 file/0700 folder). The dialog lists metadata, not private rows. Restoring requires RESTORE SAVED TEST and first archives the current run. Restore bumps object versions to invalidate stale tabs, requeues transmitting messages and marks interrupted jobs failed. Finish/discard an active intake or queued/transcribing/extracting job before resetting/restoring.

Fresh defaults restore7city units, automatic assignment/review, direct link with no loss, fresh road state and clear site gates. City/campus seeds use actual packets and delivery, not fake received reports. Empty creates no events. Browser access, provider credentials, fixed voice rules, request budget and original source files stay. Archives are local and require the private runtime/source folder; the source ZIP intentionally contains none. The old `/api/demo/reset` endpoint remains for isolated legacy tests but is no longer the normal UI reset. Never call it on the user's runtime.

### City resource operations

`server/resources.py` adds actual stage counts, capability waiting counts and recent decisions. `Resources.tsx` now has a compact readiness strip, capacity bars, map with allocations by area and actual unit names, active assignment ledger with route estimates and update controls, waiting cases, roster and recent decisions. Existing filters, add-unit controls, status persistence, offline disabling and missing-tile fallback remain. Only selected capacity shows its detailed stage breakdown, avoiding repeated zero counts. Routes still exclude earlier closures until a matched later clearance or manual reopening.

### Fictional campus

`server/campus.py` contains a separate authored XY graph,7 separate site units, versioned gate states and campus assignments. GET `/api/site/operations` synchronizes received reports, gates, paths and automatic assignments. `/api/site/gates/{id}` and `/api/site/units/{id}` update states; `/api/site/replan/{id}` rechecks a released response. Automation pause is honored. Both blocked gates yield no path and unit hold; no path is invented. Manual gate review supersedes earlier reports, while a genuinely later received update can change it. Gate blockage persists until explicit opening/report or manual clearance.

`CampusResources.tsx` at `/resources?view=site` shows map/gates/waiting/roster and a response panel. `SiteMap.tsx` preserves zoom/pan/Fit site, ambiguity hatching, reporter origins and estimated pins while adding feature lookup, responders/path layers and authored service roads. Site positions are staged XY points and operator-marked arrivals, never GPS. Drawing-unit distances are not meters; there is no physical travel-time estimate or traffic. City and campus rosters/assignments are separate. Main response panel keeps caller composition and Messages & history when using campus controls; an earlier QA failure caught and repaired this integration.

## Current verification and continuation

See `docs/V6_1_VERIFICATION.md` for exact current results and `evidence/v6-1-release-check.json` for archive integrity, secret scan and clean boot. Backend suite passed 201 tests. Browser checks cover reset/restore, priority drag, grouped fire with injury, campus map/gates, earlier messaging/case/transport paths, responsive layout and serious accessibility. Hosted v6.1 calls were not rerun; earlier v6 hosted checks are historical evidence below, not new measurements. No model weights were trained. The user accepted Orpheus terms personally; the agent did not accept legal terms.

Read `docs/V6_1_START_HERE.md` and `docs/V6_1_DEMO_GUIDE.md`. Fastest live path is Workspace → Live call → Start microphone; it creates the reporting session automatically. Review the transcript, threat details and event location before sending. Future incoming, located received reports then plan demo resources automatically. Provisional pins do not reserve units. Unknown event places stay unresolved rather than being dispatched to a guessed address.

Release outputs: Comm_Control_v6_1_Source.zip, Comm_Control_v6_1_Handoff_2026-10-17.md, updated Start_Here, Demo_Guide, Verification and UI_Copy, desktop/mobile Resources and campus screenshots. Handoff has a byte-identical Downloads copy. No runtime credentials/private reports/audio/archives/dependencies are packaged. Run `scripts/setup.sh` in a clean checkout, configure your own provider key, then `scripts/start.sh` and `scripts/open_app.py`.

Work autonomously within authorized scope, stay concise and candid, use evidence-based claims and preserve user changes. Never hide uncertainty to make a demo look cleaner. Do not ask for routine reversible implementation permission. Final finishing work is rehearsal, recording and event-specific submission material. Any new feature request should extend this state rather than restarting.

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

