# Comm Control v6.6 continuation

Project: `/path/to/comm-control` (not a Git repository).

Read `V6_6_START_HERE.md` for operator instructions. This release adds persistent provider queues, automatic next-stop assignment, guarded reassignment, recoverable incident removal, reporting capacity beyond ten, fresh explicit voice intake, and fixes for location-picker overflow and timeline alignment. Earlier v6.5 layout and typography remain in place.

## Implementation

- `server/dispatch_queue.py`: world/provider queue persistence, capability and current-route checks, FIFO advancement, held/paused reservations, finish and reassignment. Operator authentication, idempotency, optimistic queue/provider versions and transactions protect mutations. A finish updates the resource's last operator-marked position. City completion leaves the case open; USC completion resolves the work item. No GPS claim.
- `server/operations.py`: reconciles plans whose required units were manually released, sets a review hold and avoids silent redispatch. Explicit replan/new report clears that hold. Auto-allocation respects queued reservations. Completed capabilities prevent a finished queued job from being immediately reassigned.
- `server/domain.py`, `server/cases.py`: 100 reporting sessions per workspace; report capacity excludes archived records; linked removal is atomic and version-guarded. Sources and closures persist. Restore returns reports to Closed before explicit reopening.
- `server/intake.py`: `/api/demo/intake/new` ends previous unsent intake in the selected world without deleting sources. Cancelled audio responses cannot restore the old call. `LiveIntake.tsx`, `Operator.tsx` and the shared header distinguish explicit fresh starts from refresh recovery.
- `web/src/ProviderQueues.tsx`: shared Resources ledger for both worlds. Add/reorder/remove stops, pause auto-next, take next, finish and reassign, with real API outcomes.
- `WorldMap.tsx`: stable canvas className preserves Leaflet-owned classes. Picking state belongs to the outer section; explicit overflow clipping. Shared incidents draw assignments belonging to linked reports.
- `CasePanel.tsx`, `system.css`: remove/restore actions and centered timeline axis. `IncidentQueue.tsx`: Archived footer and recoverable case selection.
- `server/main.py`: optional `COMM_WEB_DIST` points test server at a staged frontend. Normal app defaults to `web/dist`.

## Tests and runtime

Backend: `.venv/bin/pytest`. New tests are `tests/test_dispatch_queues.py` and `tests/test_v66_recovery.py`. The original isolation test now enforces the intentional 100-session limit.

Frontend: `npm --prefix web run build -- --outDir dist-next`, `npm --prefix web run test:units`, `npm --prefix web run test:e2e`. Browser tests use port 8766, `.data-browser-tests` and `web/dist-next`; never reset port 8765 to run tests. `web/tests/v66.spec.ts` exercises real local mutations. The recovery-only UI fixture is explicitly synthetic; hosted AI tests are separate and gated.

The actual app is port 8765 with private `.data`. Keep `.env`, runtime credentials, databases, recordings and backups private. Before a backend restart check for listening/processing intake and pending jobs. Use SQLite backup, not a copy of a live WAL database. Promote the verified staged assets to `web/dist`, restart normally and verify source preservation.

## Routing boundary

An earlier road/path blockage remains excluded until supported clearance or manual reopening. Staleness alone never clears it. A queued assignment rechecks the current closure revision when the provider becomes free. A blocked head stays held; a manual reassignment failure retains the original assignment. A City Hall centroid can be disconnected from Union Station in the cached graph with the Main Street closure. Do not bypass this by drawing a straight line or snapping around the closure.

The operator's pre-v6.6 backup contains 17 reports and 27 source objects. No actual run reset, report removal or demonstration queue assignment is needed to deploy this release. Reconciliation may legitimately update plan state; source objects and report identities/claims must remain intact.

## Design and continuation

Preserve Nunito Sans, readable metadata, category colors, white rounded panels, blue borders, surrounding shadows and the floating header. Avoid colored incident stripes, gray route-option fills and typographic middle-dot separators. Whole-page scrolling outside maps, map wheel zoom, drag edge autoscroll and moving selection outlines are already implemented. City and USC remain separate worlds.

Future submission work: record the short voice-to-response demo, confirm hosted speech/extraction once with fictional input if needed, prepare the submission narrative/video and perform final presentation QA. Do not claim real dispatch, field validation, live GPS, live traffic, hardware transport or weight fine-tuning.
