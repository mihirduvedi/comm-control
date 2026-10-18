# Comm Control v6.5 continuation handoff

This v6.5 section supersedes conflicting v6.4 instructions below. It records the current implementation; user messages remain authoritative. Recheck mutable runtime state before acting.

The latest user request is implemented and verified: 39 browser checks pass, four hosted opt-ins are skipped, three focused final layout/USC checks pass, and strict build/two formatting checks pass. The companion release check records archive integrity and clean boot. The request covered whole-page workspace scrolling, a wider queue, inset response tabs without a divider, balanced panel shadows, removal of typographic middle-dot separators, and clearer emphasis on voice-to-response automation.

## Current behavior

- **Start voice report** is the primary header action on every operator page. It opens real LiveIntake directly; no manual session setup is required. Microphone, upload and typed alternatives preserve their actual handlers. Finish, review transcript/event location, and add the reviewed incident. Received reports then drive assignment and routing under the saved automation settings.
- **ResponseJourney.tsx** shows saved detail/location/team/route state above the map. It reads active assignments across linked reports or an active USC work item. It never changes operational state. Voice, typed, manually entered and annotated City demo inputs have different source labels. USC fixtures were manually annotated and retain Manual report. Unknown location, no team and no route are shown as pending.
- The header caption is **Voice to coordinated response**. Live intake says **One call starts the response**, uses a world-specific example and the same white/blue surface and readable text as the rest of the desk.
- Whole document scrolling outside maps moves all three workspace columns together. The middle incident pane uses overflow:clip and no internal scroll. Response content grows with the document. Maps still consume wheel input to zoom. The bounded queue still scrolls and supports native drag edge auto-scroll.
- At 1440 px, queue width is 292 px and response width 340 px. The overall shell grows to 1800 px; wide windows use a 300 px queue. Intermediate desktop uses 270 px and 300 px side columns. Timestamps move beside caller names so building titles get the full row.
- Detail tabs have 16 px top inset and no bottom divider. Main panels use a shadow with zero vertical offset. Recent-report rows have complete borders and soft surrounding shadows. Semantic colors, tags and Nunito Sans remain.
- Designed JSX metadata no longer uses typographic middle-dot separators. Original source quotations and histories are unchanged.
- USC provisional intake fits candidate buildings, labels them Not reviewed and hides the previous incident route. Existing campus incidents remain on the map, but their response is not assigned to the new call. Closing intake restores the selected response.
- Starting voice intake selects Details even before a small-screen resize. Clicking the main voice action from Map reopens the intake. Keep this covered in layout.spec.ts.

## Code and verification

Source: `/path/to/comm-control`.

Main files changed: `web/src/main.tsx`, `Operator.tsx`, new `ResponseJourney.tsx`, `LiveIntake.tsx`, `system.css`, and metadata text in Resources/USCResources/USCMap/WorldMap/IncidentReports/TestRunControls. No backend logic or schema was changed in v6.5.

Use `docs/V6_5_START_HERE.md`, `V6_5_DEMO_GUIDE.md`, `V6_5_DESIGN_CONTRACT.md`, `V6_5_UI_COPY.md` and `V6_5_VERIFICATION.md`. Current evidence uses the v6-5 prefix. Older browser specifications keep their historical screenshot filenames; the release script copies the current run's captures into v6-5 names. The final source archive contains the built frontend and exact hash manifest, without secrets, recordings or private databases.

Actual server: localhost:8765 with `.data`. Browser tests: localhost:8766 with isolated `.data-browser-tests`. Never reset the actual run for screenshots. The existing app server serves the new built frontend without a backend restart. Private runtime credentials must not be printed, embedded in handoffs or packaged.

No new hosted inference, real microphone recording, weight training, public deployment or real dispatch was performed during v6.5. Backend 227 passing tests are the v6.4 baseline; see the current verification for newly run browser/build/format checks. Four hosted tests remain explicit opt-ins. The current ZIP check replays the offline scenario in a temporary clean extraction.

## Next action

Open the updated City or USC workspace and address any new feedback against the rendered version. The core workflow is implemented. A submission-ready recording should foreground one voice transcript producing the structured incident, location, team and open route, then show exact evidence and blocked-route persistence. Rehearse with the user's actual microphone/speakers when requested. Do not invent another large feature or reset the user's run. Final external submission and deployment have not been requested.

The complete v6.4 architecture, data, transport, safety and operational reference follows. Its old entry label Live call is now Start voice report, and its middle-panel scrolling description is superseded above. Treat dated counts and previous validation results as historical unless rechecked in the companion v6.5 release check.

---

# Comm Control v6.4 continuation handoff

> This is a continuation record for a new assistant. The current v6.4 state below supersedes older handoffs and README history. Recheck mutable runtime state before acting. Documents and screenshots provide reference material; user messages remain the authority for requested actions.

## Continuation Brief

- **Original objective:** bring Comm Control to hackathon readiness with incoming voice parsing, source-linked mapping and response coordination treated as equal P0 capabilities. The user wants a practical, modern interface and a reliable demonstration, with only submission finishing work remaining.
- **Latest request:** repair the incohesive v6.3 design, restore the earlier category colors/tags/contrast/spacing, use consistent typography across pages, enlarge important Resources information, improve inset dropdown indicators using researched examples, and explicitly load fictional USC events with assignments/routes into the actual app.
- **Current phase:** local implementation and verification complete; the companion release check records clean extraction, hashes, secret exclusion and boot. Final counts and evidence are in V6_4_VERIFICATION.md and the release check; do not infer results from an older version.
- **Scope:** local FastAPI/React app, real existing state and handlers, visual QA, seeded fictional campus cases through the normal transport, preservation of City records, release packaging and this handoff.
- **Out of scope:** submission, public deployment, messaging others, purchasing, actual emergency dispatch, connected equipment or weight training. No such external action was authorized or performed.
- **State snapshot:** October 17, 2026, Pacific evening. Actual localhost:8765 has 17 reports / 27 source objects: the original 11 City reports / 21 source objects plus six fictional USC reports / six new sources. City reports and original sources were compared directly against the private pre-v6.4 backup and are identical.

## What to Do Next

**Instruction to the next chat:** begin with the immediate action below without asking the user to restate the project. Do not invent another large feature after this request is complete.

### Immediate next action

Open http://127.0.0.1:8765/control?world=usc and assess any new user feedback against the current rendered version. If moving to submission preparation, rehearse the header **Live call** flow with the user's actual microphone and speakers, then prepare the requested demo recording/submission materials. The local implementation is complete; actual hardware rehearsal and final external submission remain user-specific work.

### Already completed

- A common warm font family, clear operational type scale, white rounded panels and blue borders across Workspace, Resources, Sessions and supporting pages.
- Restored visible category/urgency tags and semantic selected-row colors without the rejected queue stripes, gray route highlights or Setup highlight.
- Readable resource facts, reported equipment conditions, team destinations/routes, compact empty states and framed Sessions forms/tables.
- Native select chevrons inset within controls; consistent details disclosure arrows; existing keyboard/select behavior preserved.
- Six fictional USC reports loaded in the actual run, forming five work items with appropriate teams and nonzero outdoor routes. The two SGM pressure sources are grouped, with the abnormal reading updating the work-item title.
- City/USC separation, persistent closures, review/approval/source preservation, map wheel zoom, near-square canvases, scrolling, drag auto-scroll and sliding header navigation retained.
- A reset race fixed: the compatibility synthetic reset now restores the City roster immediately rather than waiting for a periodic operations tick.

### Remaining work

No implementation is intentionally left for this request. User hardware rehearsal, recording, event-specific pitch/submission fields and any deployment need the corresponding user request. Do not reset the actual run to obtain screenshots.

### Completion check

Use the final backend/browser logs, built app, accessibility evidence, direct source preservation comparison and release check. Blockers: none for local implementation. Real USC access, sensors and dispatch are not connected or certified.

## Project / Task Context

Comm Control is a local hackathon communications desk. Each caller has a private reporting endpoint. Speech/text becomes a source and reviewed claims, a compact packet travels through a modeled radio/direct link, and only received reports become operator incidents. The operator can locate calls, inspect exact source excerpts, rank/group reports, assign simulated resources, avoid blocked roads/paths, prepare a response, approve it and verify recipient delivery/human response. It is not a dashboard over a replacement mock backend.

Two distinct use cases are supported: Downtown Los Angeles city response and USC University Park facilities coordination. USC uses actual publicly mapped building footprints and outdoor paths with fictional equipment, readings, people and teams. It is useful for demonstrating campus/building/warehouse-style operations without claiming a real facility connection.

### User design history that affects future changes

- Calm, practical, feature-rich interface with progressive disclosure; Apple and the Dickman Mini Analyzer are inspirations.
- Whiter background with happy light blue accents, rounded floating header/panels and restrained glass. Do not restore the early dark green/blue canvas.
- Restore meaningful category color, spacing and contrast from earlier iterations. v6.3 was rejected as sparse, inconsistent and more generic.
- Latest direction asks for cohesive typography throughout. v6.4 uses one locally served Nunito Sans family, different weights/sizes for hierarchy. This supersedes the earlier request for body/title families to differ. Do not cycle back to rejected Plex/Source Sans/skinny formal faces or introduce another fashionable font.
- No colored vertical queue-edge stripes, horizontal dispatch separator, gray route-option blocks or Setup highlight.
- A large near-square map is the main working surface. Wheel/trackpad input over it must zoom. Long details must not make the map unreachable.
- Adjacent controls and header page navigation keep one sliding selection outline. Respect reduced motion.
- Important information must be readable; Resources details are mostly 14–16 px, secondary information at least13 px. Technical map annotations can be smaller.
- City and campus are separate worlds: no Union Station report or city alert in USC. Removing the old fictional site must not auto-map old warehouse reports onto a real campus building.
- Each caller has one fixed natural demo voice. Do not bring back a voice picker or describe synthetic playback as an actual call recording.
- Prioritize source-linked evidence and truthful local-demo claims. Do not claim weight fine-tuning, live sensors, real dispatch or field proof from these tests.

## Workstream Status & Roadmap

| Workstream | Current outcome | Verification |
|---|---|---|
| Shared visual system | Complete; system.css owns current type, colors, surfaces and page rhythm | Cross-page font checks, rendered desktop/mobile, axe |
| Sessions | Complete; framed creation form and roster, scoped to current world | Empty/create/populated views and real session API |
| City Resources | Complete; semantic capacity cards, readable allocations, compact waiting state | Resource state controls, responsive and tile-failure tests |
| USC facilities | Complete; six fictional reports, five linked/routed work items, readable equipment/team cards | Received packets, appropriate capabilities, source history, route tests and actual run |
| Maps/interactions | Complete; fit selected USC route, preserve zoom/pan/expand and drag scrolling | Browser wheel, bounds, expansion, keyboard and persisted order |
| Preservation/release | Complete subject to companion release check | Private backup comparison, clean ZIP boot and manifest scan |
| Submission preparation | Not requested as an external action in this pass | Actual microphone/speaker rehearsal and final materials remain |

## Work Completed

The v6.3 map-first and world-isolation behavior was preserved. v6.4 added one shared visual layer instead of reverting functional code to an old release. Category/urgency moved back out of Report details so the selected incident retains its meaning at a glance. Queue rows gained type tags and category tint; large decorative edge stripes remain absent.

Admin Sessions now uses the same heading scale and white/blue panel system as Resources. A real session form has a clear heading, name label and private-link context; the table is framed with a rounded pale-blue heading. Existing create/open/copy handlers still run. The simulator shows scenarios for the chosen world instead of mixing both sets into one section.

Resources uses larger operational information and category-colored capacity labels/tracks. Areas, active assignments and rosters share the same panel grammar. Empty coverage no longer stretches to the height of a long roster. USC work items repeat the category/urgency grammar; equipment cards show existing reported conditions and response state rather than empty filler. Team rows show their assigned building and mapped route length.

USC seeding now stages only pristine available demo teams at real mapped buildings away from the demonstration incidents. A team with an active ticket or an updated version is not moved. Six annotated reports still travel through the normal packet transport; no hosted inference is substituted with an unlabelled canned output. The same tank's two reports aggregate into one work item. A higher-priority update changes the work-item title/capability, retaining both original sources. Campus condition categories map gas/pressure to Safety, smoke alarms to Fire, door/access issues to Access and maintenance to Assistance; this keeps tags/colors consistent with Resources.

The selected USC view fits route coordinates plus the destination footprint; refreshing identical route data does not reset manual zoom. Building code buttons are separate from their decorative count badges so visible labels match accessible names, including at clipped/zoomed positions. Keyboard activation and map/source controls remain.

### Exact implementation files changed in v6.4

- server/main.py — synchronous roster restoration on compatibility reset.
- server/usc_scenarios.py — safe demo team staging before queued USC fixtures.
- server/usc_ops.py — coherent campus condition categories and higher-priority work-item title updates.
- web/src/main.tsx — imports system.css after the existing layout styles.
- web/src/system.css — current shared typography, semantic palette, panels, readable Resources/Sessions, select/disclosure treatment and responsive finishing.
- web/src/Operator.tsx — visible selected-incident tags and queue type tags.
- web/src/Resources.tsx — capability classes for semantic resource cards.
- web/src/Admin.tsx — framed Sessions, scoped copy and selected-world simulator scenarios.
- web/src/USCResources.tsx — work tags, reported equipment conditions, team destination/route information and consistent type.
- web/src/USCMap.tsx — full selected-route fitting and accessible building-code/count structure.
- tests/test_usc.py — demo source preservation, grouping, category consistency, nonzero routes, safe staging and one-shot behavior.
- tests/test_runs.py — immediate roster restoration despite a throttled tick.
- web/tests/design.spec.ts — cross-page type/readability/selects, semantic colors, route containment, desktop/mobile axe, Sessions creation.
- web/tests/usc.spec.ts — expects the latest pressure title while checking both original sources.
- web/tests/scroll.spec.ts — clearer accessibility failure output; retains actual scroll/drag checks.
- README.md, DEMO.md, VERIFICATION.md and docs/V6_4_* — current instructions, design contract, copy and verification.
- work/package_v6_4.py — release builder; not itself shipped in the source allowlist.

## Current State

### Runtime and directories

Authoritative application:
`/path/to/comm-control`

Chat outputs:
`/path/to/local-artifact`

Actual app: http://127.0.0.1:8765, private `.data`. Isolated browser server: http://127.0.0.1:8766, private `.data-browser-tests`. Find current PIDs with lsof rather than trusting an old PID. Check active jobs/intakes before restarting. An intake in `queued` means the report was already submitted; a model job in `queued` is still processing work. Never interrupt a live recording or reset the actual run for QA.

No Git repository or AGENTS file was found. No commit/push/deployment was performed. Prior work in this application is user work and must be retained.

Private backup: `.data/backups/before-v6-4.sqlite3`, created through SQLite backup and chmod0600. Actual City 11 reports and original 21 source objects were compared directly and remain identical. Current totals are17 reports / 27 sources; USC 6 reports / 5 work items / 5 assigned teams. At the live snapshot, mapped routes were gas967m, smoke867m, pressure483m, access506m and maintenance346m. Assignment order can change in a fresh replay; tests require appropriate teams and useful open routes, not those exact distances.

### Authentication and fresh browser access

The app uses private operator/field capabilities and one-use launch links. Existing authenticated browsers can use the plain app URLs. A fresh browser should use the existing Mac launcher or run `.venv/bin/python scripts/open_app.py`. This opens a one-use link without printing the durable operator token. Do not put tokens in docs, logs, URLs shared with the user, screenshots or the release archive. Caller field pages still need their own private links.

## Work Organization

`server/` owns API, domain, transport, triage, operations, grouping and persistence. `web/src/` is the real React/TypeScript UI. `web/tests/` and `tests/` exercise UI/API behavior. `data/` contains cached public map geometry/provenance, and `fixtures/` contains synthetic demonstration recordings/inputs. `web/dist/` is the built frontend served by FastAPI. `docs/` is current/historical product and implementation documentation. `work/` and private data folders are intermediate/runtime material.

Styles load in order: styles, dispatch, tone, daylight, glass, atlas, workspaces, system. `workspaces.css` owns large-map and context layout mechanics; `system.css` supplies the current cohesive visual system. Older files remain for existing behavior, but their visual experiments are overridden. Do not add a new font at the end of another stylesheet as a local screen-only fix.

## System Design & Interfaces

### Data flow

Caller microphone/text → immutable source → reviewed claims → compact packet → selected modeled transport → receiver persistence → world-scoped report → triage/grouping/location → City operations or USC facilities → assigned demo unit/team and closure-aware route → operator-reviewed outgoing message → recipient persistence/receipt → human response.

### World separation

`server/worlds.py` validates `city|usc`, uses explicit new session/report world when present, infers old report world from interpreted event locations otherwise, and scopes reports, sessions, operations, incidents, messages, conflicts and exports. Original sources are not rewritten. This is one operator with two operating contexts, not a tenant-security boundary.

- `GET /api/control/snapshot?world=city|usc`
- `GET /api/queue?world=...`; `POST /api/queue {world,version,mode,order}`
- `POST /api/sessions {name,world}`
- `GET /api/reports/{id}/context` resolves old report deep links without losing the ID.
- `GET /api/export?world=...`
- Live intake create/current/resume is world scoped; recorder recovery keys are distinct.
- USC snapshots exclude City units/road closures. USC operations excludes City reports. Cross-world manual grouping/order IDs are rejected.
- A USC call naming an out-of-area city place is held for location review and never assigns a City unit. City calls mentioning USC likewise do not assign a campus team.

The global provider budget, transport and saved-run recovery are shared. **New test saves/restarts both worlds**, which is disclosed in the UI. Never reset one world by deleting the entire object store under an unqualified “campus reset” label.

### USC contracts

`GET /api/usc/operations` returns site/buildings/paths/access geometry, teams, tickets, assets, reports, gates and closures. Tickets retain `report_ids`, `asset_id`, `capability`, `priority`, `team_id`, `route`, `state`, `version` and history. Mutations use idempotency and version checks with reasons; source reports remain linked.

`POST /api/demo/usc` is a one-shot annotated scenario for a clean USC reporting context. Six session slots are needed in USC; existing City sessions do not consume that capacity. It creates ordinary source/draft/message records. Received pressure 145 and 220 psi sources share a tank work item; abnormal pressure requests lab safety. Gas gets lab safety, smoke alarm gets an alarm technician, door/access gets an access team, light maintenance gets facilities. A technician can be marked en route/on scene/resolved through the real work-item dialog.

USC uses real cached OSM footprints and outdoor graph geometry. A route ends on a mapped path near the destination and reports the remaining unmapped arrival gap. Do not fabricate indoor routes, verified emergency exits or actual equipment specifications. A manually marked access point needs a source and remains unverified. Persistent path/gate closures remain excluded until an explicit later matching clearance or manual confirmation; stale time alone does not reopen them.

### Core invariants

- Source excerpts, negation, uncertainty, device location versus event location and unknown indoor position remain distinct.
- Report grouping retains all source reports and can be manually separated. Higher priority does not erase earlier observations.
- Reviewed/sent instructions retain approval, transport, delivery and human-response history. Receipt is not compliance.
- Persistent road/path closures govern actual graph route selection, including future reports; no decorative bypass line substitutes for the route.
- City route/ETA estimates are demonstration estimates, not real vehicle navigation. Campus teams/equipment are simulated.
- Never reintroduce a second voice picker; use one fixed natural demo voice for each speaker. Preserve actual raw recordings as raw sources.

## Decisions & Rationale

The chosen approach restores category meaning and readability without rolling back v6.3 world isolation and map mechanics. One family across headings/body makes every page part of the same system. Type weights/sizes provide hierarchy; category color encodes function, urgency tags encode priority. Borders, spacing and small inset chevrons replace the previous mixture of flat tables, tiny text and irregular forms.

Select references were [Atlassian Select examples](https://atlassian.design/components/select/examples) and [Shopify Polaris Select](https://polaris-react.shopify.com/components/selection-and-input/select). Polaris’s legacy URL currently redirects to its updated reference. The implementation retains native controls and real handlers rather than introducing a custom menu library.

Pristine-only staging is intentional: loading a demonstration can give new demo teams illustrative starting positions, but must not silently move an operator’s active or previously updated resource. Work-item title escalation fixes the misleading145psi title when a later220psi source is the reason for review.

Rejected approaches include replacing the backend with mock fixtures, auto-mapping old warehouse locations to USC, making every pane a glass card, restoring all old large incident headings at the expense of the map, or treating a score/prompt adjustment as trained model weights. Previous typography trials are not the current design authority.

## Implementation Details

The full current files are in the source archive. Key code excerpts follow.

### Current seed implementation

```python
def seed_usc(d):
 from .worlds import report_world,session_world
 if any(report_world(r)=='usc' and str(c['location'].get('feature_id','')).startswith('usc-') for r in d.store.list('report') for c in r['claims']):raise ValueError('USC reports already exist. Use New test for a clean facilities run.')
 if sum(session_world(d,s)=='usc' for s in d.store.list('session'))+len(SCENARIOS)>10:raise ValueError('Six campus session slots are needed. Use an existing campus run or start a new test.')
 # Stage only pristine available demo teams. Never move an operator's active or previously used team.
 from .usc_ops import bootstrap
 from .usc_atlas import atlas
 bootstrap(d)
 staging={'Facilities 01':'usc-hughes','Facilities 02':'usc-bovard','Lab Safety 01':'usc-bovard','Lab Safety 02':'usc-leavey','Alarm Technician 01':'usc-tutor','Access Team 01':'usc-kaprielian'}
 buildings={b['id']:b for b in atlas()['buildings']}
 for team in d.store.list('usc_team'):
  if team['status']=='available' and not team.get('ticket_id') and team['version']==1 and team['name'] in staging:
   base=buildings[staging[team['name']]]
   team.update(position=base['center'],demo_staging={'building_id':base['id'],'note':'Simulated starting position for the USC demonstration; not a real team base.'})
   d.store.put('usc_team','operator',team,event='usc_demo_team_staged')
 result=[]
 for name,text,claims in SCENARIOS:
  s=d.create_session(name,'usc');draft=d.manual_draft(s['endpoint_id'],s['id'],text,claims);m=d.send_report(draft);result.append(m['id'])
 return {'label':'Six simulated USC facilities reports queued through the demo link.','message_ids':result}
```

### Exact local verification commands

Run from the application directory:

```zsh
.venv/bin/pytest -q
npm --prefix web run build
npm --prefix web run test:units
npm --prefix web run test:e2e
.venv/bin/python scripts/preflight.py
.venv/bin/python /path/to/local-artifact --json web/src
```

The browser config starts/reuses localhost:8766 with `COMM_DATA_DIR` pointing explicitly to `.data-browser-tests`. Do not point these tests at the actual store. Hosted tests are opt-in and skipped for this pass; they consume the shared provider budget and were not needed for these changes.

To start the actual app on this laptop, use `scripts/start.sh`, then in another terminal `.venv/bin/python scripts/open_app.py`. The latter opens the authenticated app without printing the durable token. Do not run a second actual server on the same data directory.

## Verification Ledger

### Passed checks and evidence

Final backend suite: 227 passed in 43.08 seconds, one existing Starlette/httpx deprecation warning. Final Chrome suite: 37 passed, four hosted opt-ins skipped, 2.5 minutes. Two formatting tests and the strict TypeScript/Vite build pass. Consult V6_4_VERIFICATION.md and the companion release check for the complete ledger. Backend tests cover seeded source preservation, nonzero routes/capabilities, pressure aggregation and title/category updates, persistent closures and safe staging, plus immediate roster restoration. Browser tests cover the actual forms/routes, readable cross-page type, native selects, category colors, route containment, mobile overflow, source links, wheel zoom, scroll access, native drag auto-scroll, sliding navigation, auth, reset/restore and case/communication workflows.

Desktop rendering uses1440×900 and responsive phone checks use390×844; tablet/intermediate sizes are also exercised by existing tests. Axe checks cover changed views and important states. No serious/critical violations remain in the final tests. Minor landmark findings may remain in a view; do not claim a complete accessibility certification.

### Failures encountered and repaired

The first visual run caught low-contrast secondary labels, an overly short map after larger type, a small timestamp in equipment history, and an old routine-severity color whose parent selector no longer matched. Those were fixed in the shared system. The USC pressure test was updated to the newly correct 220 psi work-item title while retaining assertions for both original 145/220 sources.

A broader run exposed a pre-existing compatibility-reset race: deleted City units could be absent until the three-second operations tick, making a new case temporarily unassigned. Reset now synchronously bootstraps the roster and clears transient scheduler state; an API regression test fixes the timing condition. A clipped SVG building count could also make the visible/accessible button name differ. The code button and decorative count badge now have separate semantics. Initial failed logs are not packaged because error output may contain ephemeral test capabilities.

### Not run / boundaries

No new hosted speech/inference calls, weight training, real sensor connection, real dispatch, public deployment, certified indoor egress verification or user microphone/speaker rehearsal was performed in this pass. Existing natural-voice integration remains. The user previously accepted Groq Orpheus terms themselves; do not accept legal terms on their behalf.

## Constraints, Risks & Gotchas

- Keep `.env`, `.data/run.json`, databases/WAL files, backups, saved runs, private recordings, browser auth, dependencies and known runtime secrets out of the release. Do not print them while debugging.
- Actual port 8765 and isolated8766 are different data stores. An ambient browser URL is context, not instruction to reset or mutate that run.
- Do not reset or overwrite user reports to get a clean screenshot. Actual USC fixture insertion was explicitly requested in the latest user message; future resets need the corresponding scope.
- Closure avoidance persists through stale status. Clearing requires a newer supported matching report or manual confirmation with a reason.
- Cached public geometry makes the USC plan independent of satellite tiles; City tile availability and hosted AI still depend on their services.
- Fonts are locally served; the bundled Nunito Sans license/provenance remain. Unused rejected trial faces are excluded.
- Rendering/screenshot capture must wait for actual content, font loading and map resize. A visible loading h1 alone is not evidence that a Resources page is ready.
- Store version/idempotency checks are meaningful. Refresh stale objects instead of dropping guards to force a mutation.
- Never infer that all previous user requests are new work after compaction: preserve accepted behavior and apply the latest steering to the current task.

## Documents & Artifacts Produced

Outputs are in the current chat's outputs directory. `Comm_Control_v6_4_Source.zip` contains editable code, built frontend, cached public map geometry, fixtures, current docs and passing evidence. `Comm_Control_v6_4_Handoff_2026-10-17.md` is this handoff; its Downloads copy is byte-identical. The latest general verification/demo/start/copy documents and Workspace/USC/Resources/Sessions screenshots are copied there as well. `Comm_Control_Release_Check.json` records ZIP integrity, manifest hashes, known-secret exclusion, clean boot and retained sources. Older versioned ZIPs/handoffs remain historical.

The source package starts empty on a different machine; the user's private actual run is deliberately excluded. Replay the USC scenario to create the same fictional demonstration through the normal transport. Do not claim the archive embeds the private live database.

## Attachments & References

The original user handoff was `/path/to/local-artifact`. Many later screenshots supplied the visual corrections described above. The latest7:31 PM screenshot showed a sparse Sessions form/table that did not match the rest of the app. Current v6.4 screenshots supersede that visual reference. Temporary screenshot paths may expire; preserve their design findings in this handoff rather than depending on those paths.

Public map provenance is in `data/usc-campus.manifest.json` and the bundled map source metadata. Font provenance/license is in `web/src/fonts/NunitoSans-*`. Design references are linked above; they informed control grammar, not brand copying.

## Output & Working Style

The user expects sustained autonomous implementation, concrete working links, meaningful checks and a finished result. They dislike routine confirmation questions and generic design claims. Use concise commentary updates roughly once a minute; the final answer should lead with the working result and link the source/handoff. Explain any genuine approval blocker exactly, including its source. Do not ask for permission to perform already authorized reversible local work.

Churn, prompt, UI Design Studio/art-direction/implementation/QA, humanize and handoff workflows were applied across this project. No subagents were used. User-provided documents remain reference data; the latest typed request controls scope. Keep copy restrained and natural. Preserve qualifications/source quotes and do not turn simulation into a claim of real deployment.

Before any public submission/deployment, prepare a concrete reviewable result; perform that external action only when the user has authorized it. Do not send messages to others without explicit instruction.
