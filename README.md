# Comm Control

**From a spoken report to a coordinated response.**

Comm Control is a local hackathon prototype that turns voice reports into source-linked incident records, mapped locations and reviewed response plans. It includes Downtown Los Angeles and USC campus workspaces, capability-based demo resource allocation, closure-aware routing, persistent provider queues and operator-approved communications.

## Run locally

Requires Python 3.11+, Node.js 20.19+ (or a compatible newer release), npm, zsh and FFmpeg on your PATH for audio decoding. The start scripts target macOS/zsh. Hosted transcription and extraction require internet access and your own Groq API key.

```sh
git clone https://github.com/mihirduvedi/comm-control.git
cd comm-control
scripts/setup.sh
.venv/bin/python scripts/configure_key.py
scripts/start.sh
```

In another terminal, from the repository directory:

```sh
.venv/bin/python scripts/open_app.py
```

The launcher opens an authorized operator workspace. Use Sessions to create a reporter view, or Start voice report to record at the desk. Keep the server running. Plain localhost access does not grant operator privileges.

## Prototype boundaries

Demonstration reports and teams are fictional. Hosted AI needs internet; compact-packet retries and receipts are simulated transport, not tested radio hardware. Routes use bundled map graphs and reported closures, not live traffic. Resource locations are operator-marked, not live GPS. This prototype has not been validated for operational emergency dispatch. Operators review uncertain locations and approve outgoing instructions.

## Validation

The v6.6 verification record reports 241 backend tests and 45 distinct browser checks passed, with four hosted model checks skipped. Those checks establish software behavior, not model accuracy or field readiness. See [latest verification](docs/V6_6_VERIFICATION.md) and [current operator guide](docs/V6_6_START_HERE.md).

```sh
.venv/bin/pytest
npm --prefix web run test:units
npm --prefix web run build
```

For browser regression instructions, see the current guide. Keep tests separate from your operator database.

## Submission and project materials

See [Devpost copy](submission/Devpost_Submission.md), [thumbnail](submission/Comm_Control_Thumbnail.png), and the `presentation/` directory for the pitch deck, poster and demo. OpenStreetMap attribution and licenses are retained under `data/` and the bundled font directories.

## Detailed implementation history

The notes below document development iterations. Current v6.6 guidance takes precedence over older notes.

## v6.6 resource queues and repeatable tests

Start with [V6_6_START_HERE.md](docs/V6_6_START_HERE.md). Resources now supports persistent next-stop queues, automatic advancement and guarded manual reassignment in both City and USC. Case history can remove incidents with recovery through Archived; sources and reported blockages are retained. Reporting sessions support 100 callers per workspace. Every explicit Start voice report opens a blank call while refresh recovery stays available. Location picking no longer loses map clipping, linked source reports share their assignment route, and case-history markers align on one axis. See [continuation notes](docs/IMPLEMENTATION_HANDOFF_V6_6.md). Earlier version notes are historical where they conflict.

## v6.5 voice to coordinated response

Start with [V6_5_START_HERE.md](docs/V6_5_START_HERE.md). **Start voice report** is now the main action across the operator interface: capture a call, review its transcript and location, then watch the received incident produce a team assignment and an open route. Each incident shows its actual details, location, assignment and route states. Source labels distinguish voice, typed/manual and annotated City demo inputs; missing locations or teams stay pending.

Both workspaces use document scrolling outside the maps, a wider incident queue, inset response tabs without a divider, and balanced surrounding panel shadows. Map wheel zoom and native queue drag auto-scroll remain available. Typography, category colors and source quotations are preserved. Designed metadata uses spacing and labels in place of middle-dot separators.

See [verification](docs/V6_5_VERIFICATION.md), [current demo guide](docs/V6_5_DEMO_GUIDE.md) and [continuation handoff](docs/IMPLEMENTATION_HANDOFF_V6_5.md). Earlier version notes below are historical; v6.5 supersedes conflicting layout and entry-point descriptions.

## v6.4 shared design and populated USC demonstration

Start with [V6_4_START_HERE.md](docs/V6_4_START_HERE.md). Workspace, Resources and Sessions share locally served Nunito Sans, white rounded panels, blue borders, readable operational text and restored semantic color tags. Category and urgency stay visible beside the selected incident. Native dropdown indicators have inset spacing. The USC scenario stages pristine available demo teams away from incidents; six received reports form five routed work items, including the aggregated pressure updates. The operator’s actual run has been populated with these fictional USC examples without resetting the city context. Equipment cards and team rows show reported conditions, response states and destinations.

See [V6_4_VERIFICATION.md](docs/V6_4_VERIFICATION.md), [V6_4_DEMO_GUIDE.md](docs/V6_4_DEMO_GUIDE.md) and [IMPLEMENTATION_HANDOFF_V6_4.md](docs/IMPLEMENTATION_HANDOFF_V6_4.md). Earlier sections below are historical and superseded wherever they conflict with v6.4.

## v6.3 map desk and operating workspaces

Start with [V6_3_START_HERE.md](docs/V6_3_START_HERE.md). City and USC now have independent report queues, alerts, sessions, resources, queue orders and live-call intake. The selected workspace follows real navigation and reload. Both maps support pointer-centered wheel zoom; compact incident context and floating search/building controls make the map the main surface. Expand map and Escape/Restore provide a wider working view. Body text uses locally hosted Nunito Sans, distinct from the preserved title family. The persistent header lets its selection outline slide across pages, including browser history and reduced motion. See V6_3_VERIFICATION.md and IMPLEMENTATION_HANDOFF_V6_3.md for exact checks and continuation details. Historical sections below are superseded where they conflict.

# Comm Control

A working local hackathon dispatch desk. Reports become categorized incident briefs, real-world map locations, road-aware route previews and automatic demo resource assignments. An operator reviews uncertain details and outgoing communications. The original source and approval history remain accessible in Evidence.

## V6.2 USC facilities and interaction update

USC is the only campus view, with a custom locally rendered plan from real building/path geometry. Source-linked facilities work items, reported pressure histories, demo ranges, appropriate simulated teams and persistent gate/path reviews complement the existing city workflow. Middle maps scroll, native queue drags auto-scroll at either edge, tab outlines slide and the header opens live intake from every page. Body text uses the same system family as the titles. See [current guide](docs/V6_2_START_HERE.md) and [verification](docs/V6_2_VERIFICATION.md).

## Start on this laptop

Dependencies and the private Groq key are already configured. In Terminal:

```zsh
cd /path/to/comm-control
scripts/start.sh
```

In another Terminal:

```zsh
cd /path/to/comm-control
.venv/bin/python scripts/open_app.py
```

The second command opens an authorized workspace without printing the private launch token. Plain `http://127.0.0.1:8765` does not grant operator access. Keep the server Terminal open; Ctrl+C stops it. Sessions → Create session → Open field view creates each reporter's separate recording and instruction page. Use fictional reports only for the demo.

## Try a live call on the map

Choose **Start voice report** at the top of the workspace, then **Start microphone**. Allow microphone access and say:

> There’s smoke near City Hall. Two people are outside. I don’t know if anyone is still inside. Main Street is blocked at Temple Street. Please send fire support.

About every five seconds, the app sends the audio recorded so far to your configured Groq speech model. The transcript and mentioned places appear on the map while you’re talking. A dashed teal pin means **Not reviewed**. It doesn’t create an incident, reserve a unit or send a message.

Choose **Finish call** (or let the 30-second limit stop it), check the extracted facts and location, then choose **Add reviewed incident**. If you correct the transcript, add a note and choose **Update call details** first. The normal selected link carries the report to the control center. Only received reports get a response plan and demo unit assignment. Pausing the link holds the report, including in live mode.

The keyboard and upload buttons provide typed or prerecorded input. They’re labeled alternatives, not fake live speech. Uploads use the existing 60-second/10 MiB decoder limit; microphone capture is capped at 30 seconds. A failed recording is saved on the device for Retry/Discard. Close stops the microphone. After an interrupted session, discard the saved call or update its transcript before starting another.

This is microphone capture at the desk, not a phone integration. Each call uses one reusable dedicated demo session, with its transcript explicitly shared through the operator-only live-intake endpoints. Ordinary unsent field sources stay private. Only literal places in the loaded Downtown LA catalog become preview candidates. The preview may include a caller’s position or more than one place; final extraction/review determines the event location.

The same free-tier key and 60-requests/hour cap apply. A typical ten-second call uses two audio transcriptions and one extraction; longer calls use more snapshot requests. Updates are throttled with one in flight and a maximum of eight audio updates per call. No browser speech provider, additional account, local model or paid fallback was added.

## Current v6 workflow

Threat review uses dedicated violence, self-harm, medical and basic-needs kinds. Extraction prompts and evidence guards reject unrelated occupancy labels, retain explicit serious threats, preserve each clause’s polarity and rank the received queue using a versioned demo policy. Exact excerpts remain visible. Explicit operator priority changes survive replanning. This is prompt and policy tuning, not model-weight training or a validated emergency dispatch protocol.

In a finished Live call, review **Event location**, choose a proposed place or search a Downtown LA landmark, address or intersection. The selected pin is an operator annotation applied after the authenticated report arrives. **Keep location unconfirmed** holds allocation even if the draft contained a proposed pin. Caller position alone never locates the incident. Outside the loaded Downtown LA graph, the app requires location/routing review.

**Resources** shows actual saved demo assignments by capability and destination, map routes and road closures, unit states, and cases waiting for coverage. Select a capability to filter the map/areas/roster, or an area to inspect its units. Add a named demo unit at a known base to increase fictional capacity; waiting incidents are reconsidered. Unit updates persist; on-scene pins are operator-marked arrivals, not live GPS. Busy, missing and unroutable resource reasons are distinct. Only unstarted, much lower-priority assignments may be transferred to an immediate threat; en-route/on-scene units are not automatically diverted.

Earlier blocked-road reports affect all later routes. Expiry requests review and keeps the segment excluded. Reopen manually with a reason, or receive a later asserted clearance naming the same road and mapped segment. Secondhand, vague, crossing-street or older clearances leave it blocked. Routes recalculate; a held unit stays held until the operator marks it en route. Closing an incident does not clear its road report.

## Layout and wording

The current interface uses a mostly white canvas, blue edges, a centered floating glass header and the original system sans font. The map dominates the workspace; one type filter replaces the category-pill stack. Unit and area allocations use quiet ledgers. Secondary messages and audit tools open on demand. Colored queue strips and the dispatch separator remain removed. Calculated distances use miles and device accuracy uses feet; literal source units remain unchanged.

Revised interface copy is in docs/V6_UI_COPY.md. Source quotations, approvals, names and historical records retain their original wording. See docs/V6_DESIGN_CONTRACT.md, docs/V6_VERIFICATION.md and docs/IMPLEMENTATION_HANDOFF_V6.md for the current design, evidence and continuation state.

## Try the new city workspace

Open the workspace and choose **Load city demo**. If your existing run already has the earlier warehouse samples, use **Simulator → Queue city demo** to add the four city examples without deleting the run. These are annotated synthetic reports at real Downtown Los Angeles landmarks; AI is not run for this button. The selected transport still delivers every packet.

The queue uses coral for fire/smoke, blue for medical, amber for road access, violet for safety, teal for assistance and gray for information updates. Category filters and separate severity labels keep unlike cases distinct. A live Pacific date/clock appears in the header. Location, needed help, observation time and receipt time sit above the map. Unknown observation time stays unknown.

Response plan shows what automation handled, assigned demo units, road alternatives, unresolved reviews and prepared communications. Evidence preserves exact received quotations, interpretation corrections, location provenance and earlier instructions. On smaller screens, Queue / Map / Details become separate tabs. The response button stays available while details scroll.

## A complete voice loop

1. Sessions → Create session → Open field view. Record or upload `fixtures/city-report.aiff` (synthetic speech). New transcription and extraction use the configured hosted model.
2. Review the extracted facts, uncertainty and location before sending. City Hall, Union Station, Grand Park, local exact addresses and intersections resolve against the bundled OSM catalog. A vague or unsupported place stays unlocated.
3. Send reviewed report. Only after the received packet reaches the operator does automation categorize it, summarize needs, reserve the closest available capable demo unit with a supported route, flag uncertainty and prepare messages. Two people outside never becomes zero inside. Caller position is separate from event location.
4. Select the received incident. The real street map shows demo units and road routes. A reported blocked road is excluded, routes recalculate and alternatives appear. Route & alternatives → Report a blockage tests another closure. An expired road report stays excluded until reviewed/reopened.
5. Review a prepared caller update or Respond. Dictate, upload `fixtures/city-operator.aiff`, or write exact words. Inspect text, recipients, protected details and expiry; approve and send through the existing constrained transport.
6. On the field page, Listen reads exact approved text. Received, Cannot follow, questions and reviewed voice replies use the return transport. An acknowledgment does not answer an occupancy question or resolve a case.
7. Review contact notes or public advisory drafts. Approve exact wording/audience, then publish to the **local demo board**. No outside person, emergency service or public platform receives these records. Setup provides independent automation, assignment and escalation switches.

Demo unit status controls persist assigned → en route → on scene → released. A blocked route holds a unit until a route is available. Exhausted resources produce review tasks; a released capable unit can serve a waiting case. No real vehicle or staff roster is connected.

## Real-world map and routing coverage

Leaflet displays OpenStreetMap standard tiles with visible attribution. The basemap can be browsed worldwide; **automatic place resolution and driving-route previews are bounded to the bundled Downtown LA extract**, approximately 34.035–34.073 N and 118.265–118.215 W. No Google Maps account, billing, public geocoder or paid routing service is needed. Search is local and sends no call text to a geocoder. Ordinary tile requests expose viewport/IP metadata to the tile provider; do not use this demo for confidential incidents.

The cached extract is 3,498,190 bytes; snapshot timestamp is recorded in `data/downtown-la.manifest.json`. The directed graph respects modeled one-way roads and simple via-node turn restrictions and avoids reported closures. Estimates use road length/class speeds, with no live traffic or emergency-vehicle access rules. Conditional and via-way restrictions are not fully modeled. Dotted endpoint gaps are approximate connections, not drivable directions. Outside coverage, ambiguous locations and no-path outcomes require review; no straight-line driving route is invented.

Real-world tiles need internet and follow [OSMF tile policy](https://operations.osmfoundation.org/policies/tiles/); no bulk/offline tile download is implemented. Cached local road routing, the catalog and the original fictional SVG site plan work without map tiles. Data: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See `data/ATTRIBUTION.md`. No live traffic, phone system, agency CAD, SMS or public-alert feed is connected.

## Free hosted AI and laptop resources

The disk was about 98% full when checked. Local weight downloads started during the earlier implementation were stopped and removed. This app stores no model weights and does not train or provision a custom model.

Actual hosted speech recognition uses Groq `whisper-large-v3-turbo`; structured extraction and instruction drafting use `openai/gpt-oss-20b`. Source audio/text goes to Groq only when you request AI processing. The API key stays server-side in the ignored `.env` file. Browser launch capabilities are different from that provider key.

Stay on Groq's **Free tier**. Do not add billing or upgrade to Developer. The app requires a local Free-tier confirmation, caps AI requests at 60/hour across evaluation and application use, and stops on provider/budget failures. It does not change your account tier or fall back to a paid provider. The provider controls account limits; this cap is not a billing control for a separately upgraded account. See [Groq billing](https://console.groq.com/docs/billing-faqs), [rate limits](https://console.groq.com/docs/rate-limits), and [models](https://console.groq.com/docs/models).

To configure a fresh installation, create a free account at [Groq Console](https://console.groq.com/), create a key at [API keys](https://console.groq.com/keys), then run:

```zsh
.venv/bin/python scripts/configure_key.py
```

Enter it at the hidden prompt, confirm the account is Free, and never paste it into chat. This laptop is already configured.

## Connected and disconnected behavior

New AI transcription/extraction and real-world map tiles require internet. Cached road routing, the fictional site map, records, manual source-linked reports, exact written instructions, local playback, approvals, export, and the transport simulator use the local server. A failed upload remains in the browser's IndexedDB for Retry/Discard; an accepted source remains in its origin's private server store. The server must stay running. This is a single-host simulation, not communication between physically disconnected devices.

Listen uses one assigned demo voice for the speaker. Operator instructions always use Hannah; callers have a saved, stable voice assignment. Alex Rivera uses Autumn, Jamie Chen uses Troy, Jordan Chen uses Diana, Sam Okafor uses Austin, and Taylor Brooks uses Daniel. New names get a deterministic caller voice that is stored on the session. There is no voice picker. Actual source recordings are retained in their original voice; generated fixtures are explicitly fictional. First playback sends the unchanged approved message text to Groq and caches the WAV privately. The existing Free-tier confirmation/shared 60-request/hour cap apply. No voice cloning, local weights or paid fallback is used. Native local readout remains a backend compatibility route, without a user-facing voice selector. Written instructions remain authoritative.

Case history adds a durable handover note/owner, monitoring, explicit closeout, reopening and a downloadable Markdown case record. Closeout requires an outcome and explicit acknowledgment of outstanding reviews/questions/delivery. It releases demo units and closes the response plan without answering questions, reopening roads, deleting sources or inferring safety. Reopen uses current resource/routing policies. The Closed queue filter and open incident counts reflect these states. Case updates require operator access, current report version and an idempotency key.

## Transport, persistence and evidence

FastAPI + SQLite WAL serves the React/TypeScript UI with Leaflet/OSM mapping and a bundled directed road graph, plus the original self-authored SVG site pack. Source, draft, approved message, outbox, received projection, device persistence receipt and human reaction are separate records. Operator snapshots cannot read unsent field sources. Private capability links isolate up to 10 sessions; this is demo authorization, not production identity management.

The simulator uses canonical CBOR bodies ≤1,024 bytes, up to eight 128-byte chunks, 32-byte headers, CRC, and a 16-byte HMAC tag. Frame size is ≤176 bytes. One shared half-duplex scheduler applies seeded loss, propagation delay, byte airtime, receipt/urgent priority, retries and expiry. No raw audio crosses it. A full eight-frame batch alone models 11.264 seconds at 1,000 bit/s, before delay/receipts/contention. Default simulated profile is deliberately slower than Local direct.

Pause global/endpoint links in Simulator, send, and observe queued/unconfirmed states. Restore to resume. Retry exhaustion and expiry never turn into a fake receipt. A closed field tab can have a server spool entry but cannot emit the browser-persistence receipt. Source corrections retain the original, cross the link as a new correction packet and wait for the original if received out of order. Unknown observation time remains unknown; receipt time is labeled separately.

Review → Export includes only received evidence, approved instructions and trace/history, excluding keys, raw audio and unsent drafts. Reset requires the exact phrase and clears only this application's synthetic run. It also removes its current source recordings. Existing exported files and other projects are unaffected.

## Install elsewhere

Needs Python 3.11+, Node 20.19+/22.12+, npm and ffmpeg. On macOS `say` supplies the optional native Listen helper. `scripts/setup.sh` checks for at least 500 MiB free, installs pinned Python dependencies and npm lockfile dependencies, and builds. It downloads no model weights. No account, deployment or paid service is provisioned.

The source archive excludes `.env`, private runtime data, virtual environments, node_modules and capabilities. Configure your own Free-tier key for AI; manual mode works without it. Never bind this demo to `0.0.0.0` or publish its private field links.

## Verification commands

Run from this directory:

```zsh
.venv/bin/python scripts/preflight.py
.venv/bin/python -m pytest tests -q
npm --prefix web run build
(cd web && npm exec -- playwright test tests/dispatch.spec.ts tests/ui.spec.ts tests/audio.spec.ts tests/intake.spec.ts)
```

Browser tests use existing macOS Chrome and a separate `.data-browser-tests` database/port 8766. They reset only that test run. The live microphone test is opt-in. The verified ten-second run used three hosted calls:

```zsh
(cd web && COMM_LIVE_VERIFY=1 npm exec -- playwright test tests/intake-live.spec.ts)
```

It uses synthetic native-speech WAV input through an actual Chrome MediaRecorder, real hosted speech snapshots and extraction, an interim City Hall map pin, source review, paused-link checks and a received incident/demo assignment. The earlier city-live.spec.ts and live.spec.ts tests retain separate synthetic upload and voice-answer evidence. It is not a human field test. See `VERIFICATION.md` for actual results and limits.

`fixtures/evaluation-cases.json` is frozen synthetic text evaluation. `scripts/evaluate_models.py --run` makes 40 real calls paced at 20 seconds each; `--failed` reruns failures and **is tuned rechecking**, not a new held-out evaluation. Keep the initial result when comparing. No automatic AI retry loop.


## Current v5 delivery

The current white-glass UI has a floating rounded navigation bar, translucent rounded panels with blue borders, and soft stationary blue background shapes. The full-width dispatch divider and colored queue strips have been removed. `docs/V5_DESIGN_CONTRACT.md` records the direction. `docs/IMPLEMENTATION_HANDOFF_V5_1.md` is the latest continuation point; v5 is historical context. `fixtures/voice-provenance.json` describes the refreshed, fictional, naturally generated audio fixtures; they are not human recordings. `scripts/refresh_demo_voices.py` rebuilds these samples after model terms acceptance, using the existing provider guard and cached clips. No account/billing tier changes are made.
