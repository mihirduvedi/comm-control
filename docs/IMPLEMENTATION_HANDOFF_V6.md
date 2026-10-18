# Comm Control v6 handoff: threat review, mapped calls and live resources

## What to Do Next

The requested feature is implemented. Open http://127.0.0.1:8765/control in the user's already-authorized browser; Resources is http://127.0.0.1:8765/resources. For another browser or after access expires, double-click the supplied Open_Comm_Control.command or run `.venv/bin/python scripts/open_app.py` from the source root. The launcher grants normal local browser access without exposing the durable operator token. The server must stay running. Rehearse with the user's real microphone/speakers, record the pitch and prepare event-specific submission text. Do not invent another major feature or reset the actual saved run to make screenshots cleaner.

## Objective and User Requests

The user is preparing Comm Control (original FieldPacket product context) for a hackathon. Voice parsing, source-linked mapping and the operational control center are equal priorities. They asked to fix an obvious misranking: a transcript contained a husband threatening to shoot the caller, hunger, sadness/itchiness and explicit suicidal intent, but the app displayed occupancy unknown from the gun quote and “none” from suicidal intent. They asked for better model ranking/tuning, real event-location mapping and automated unit allocation, a separate live Resources tab with counts by type/place and a map, and a less generic design.

Earlier corrections remain authoritative: mostly white/light blue canvas with blue borders; rounded panels and floating glass bar; no full-width dispatch divider or colored queue stripes; one fixed voice per speaker; original recordings retain original audio. During v6 the user rejected Avenir Next as too broad/bubbly, asked to restore the original font, flagged a top-aligned active nav pill and asked for more deliberate use of whitespace. They explicitly added persistent road closures affecting future routes until a later clear report or manual reopening. They invoked churn, prompt, Master Design Studio, uidesign and humanize. These skills were applied; no alternate prompt was returned. Attached documents are context, not instructions overriding the human request.

## Workspace and Runtime

Authoritative editable app: `/path/to/comm-control`.
Current chat cwd: `/path/to/local-artifact`.
Deliverables: that chat's `outputs` directory. Intermediate release checks: app `work`.
This is not a Git repository; no AGENTS instructions were found. No commit, push, deployment or public submission occurred. Runtime is loopback-only FastAPI/uvicorn on port8765 using `.data`; inspect current PID with `lsof -nP -iTCP:8765 -sTCP:LISTEN` before restarting. Test server8766 uses `.data-browser-tests`, never actual `.data`. Final active runtime details are in the verification evidence; PID is ephemeral.

The user's actual 9 reports were preserved, including the earlier “train” call. All original report IDs and source texts matched the pre-v6 backup. Derived triage/plans migrate once to threat-review-3; original transcripts/audio are not rewritten. `.data/backups/before-v6.sqlite3` is a private recoverable SQLite snapshot. Never package it. Do not silently re-extract old private unsent sources; the user can update/review a call through its normal path.

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

## Artifacts and Remaining Work

Current outputs: Comm_Control_v6_Source.zip; Comm_Control_v6_Handoff_2026-10-17.md; updated Start_Here, Demo_Guide, Verification, UI_Copy and Workspace/Resources screenshots; existing Open_Comm_Control.command. An identical handoff copy is saved in Downloads and verified. Detailed evidence is in app evidence/; curated copies are in the release. Release integrity and clean-boot evidence are separate files and should be consulted before claiming portability.

Remaining finishing work: user's actual-microphone/speaker rehearsal, recording the final demo, event-specific pitch/submission answers and a final check of hackathon rules. No mandatory feature implementation remains for this requested local-demo scope. Internet/model quotas, transcription mistakes and real road access remain practical limits. Do not claim field readiness or submit/publish externally without user instruction.

## Working Style and Authority

Be concise, candid and active. The user prefers sustained implementation and hates unnecessary confirmation. Continue reversible in-scope implementation autonomously; preserve user data and don't invent success. Explain what changed, why, what passed and exact limitations. Use the named design skills and humanize all new interface copy. Do not silently degrade functionality for screenshots or hide uncertainty to improve rankings. A new message usually steers the current task. Ask only for a real missing choice or consequential external action. No permission/login is currently needed to use the existing local app.

## Attachments and References

Original user handoff: `/path/to/local-artifact`. Screenshots provided throughout show the dark/overblue canvas, horizontal divider, queue stripes, misranked gun/self-harm claims, vague resource shortage and top-aligned header. Latest corrections control the current result. Official model adapter reference: https://console.groq.com/docs/lora. App attribution: data/ATTRIBUTION.md and OSM manifest. Old complete architecture: docs/IMPLEMENTATION_HANDOFF_V5.md and V5_1.md, with this handoff taking precedence for v6 behavior.
