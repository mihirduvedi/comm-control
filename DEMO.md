Current release: see [v6.5 start guide](docs/V6_5_START_HERE.md), [demo guide](docs/V6_5_DEMO_GUIDE.md) and [verification](docs/V6_5_VERIFICATION.md). Historical version notes below are superseded where they conflict.

# Current demonstration

See [V6_4_DEMO_GUIDE.md](docs/V6_4_DEMO_GUIDE.md). USC fictional examples are loaded in the actual app; city data is retained. Older instructions below are historical.

# Comm Control live-call demo

Open the authorized launcher and choose Live call → Start microphone. Speak clearly and include a Downtown LA landmark. This example is short enough for the demo:

> There’s smoke near City Hall. Two people are outside. I don’t know if anyone is still inside. Main Street is blocked at Temple Street. Please send fire support.

While you’re talking, point out the transcript and dashed teal location pin. Updates arrive about every five seconds. The pin is marked Not reviewed, and no unit has been assigned yet.

Choose Finish call, review the actual extracted facts, then Add reviewed incident. The selected demo link delivers the report. The control center opens its incident brief, miles-based road route and capable demo unit assignment. Unknown occupancy remains unknown. If no suitable unit or route is available, show the review state instead of claiming a dispatch.

To show a correction, edit the finished transcript, explain the change and choose Update call details. To show a failure, pause the link before adding the report. It stays queued until the link resumes. Recording, transcription, review and received assignment are separate steps.

For return communication, Respond or open Messages to review the prepared update. Approve exact wording and recipients before sending. The field page’s Received button acknowledges the instruction and leaves any question open. Announcements/contact notes stay on the local demo board.

Microphone access is requested only after Start microphone. The 30-second capture limit and five-second updates keep the live demo bounded. A failed clip is saved for Retry/Discard. Upload or type instead if needed, and say which input you used. Speech processing and map tiles need internet. Cached routes and manual workflows remain available locally.

The test evidence uses synthetic speech through a real MediaRecorder and real hosted model calls. A presenter still needs to try actual acoustics, speaker volume and unfamiliar wording. This microphone demo isn’t connected to a telephone system or real emergency services.

## Alternate five-minute city walkthrough


Use fictional identities and synthetic incidents. These are rehearsal timings, not measured operator-performance results. Internet is needed for hosted AI and map tiles. Routing/catalog and manual workflows use local cached data. Nothing here contacts a real emergency service.

1. **0:00–0:45 — Orient the desk.** Open Comm Control. On an empty run choose Load city demo; on an existing run use Simulator → Queue city demo. Explain that the examples are annotated, not freshly AI-processed. Show category colors/text, live date/time and the separate incident queue, case/map and response plan. Select City Hall smoke.
2. **0:45–1:30 — Show the automatic work.** Location, requested help, receipt/unknown observation time, a reserved capable demo fire unit and travel estimate are already filled. Expand Automatic handling. Unknown occupancy and supervisor review remain visible in amber. Category and severity have separate meanings.
3. **1:30–2:15 — Demonstrate real road rerouting.** The map uses actual OSM streets. The Main Street blockage was received from another synthetic caller. Expand Route & alternatives and choose Report a blockage on this route. Enter a synthetic reason. Save; the route changes to exclude that graph segment. Alternatives, closures and unit assignments are persisted. The preview is limited to Downtown LA; no live traffic or real vehicle tracking is connected.
4. **2:15–3:15 — Take a fresh voice report.** Create a new field session. Say “There is smoke near City Hall. Two people are outside. I do not know if anyone is still inside. Main Street is blocked at Temple Street. Please send fire support.” Or upload fixtures/city-report.aiff and call it prerecorded synthetic speech processed now. Review actual extracted facts, open Show map and send. Select the newly received case; show automatic categorization/assignment. If units are exhausted, show the honest resource-needed state.
5. **3:15–4:15 — Return a reviewed instruction.** Review prepared update or Respond. Say “At City Hall, stay outside. Do not use Main Street. Ask whether anyone is still inside.” Review protected details, recipients and expiry, approve, send, and show field device persistence. Listen is exact approved text. Tap Received; the occupancy question stays open until a reviewed answer arrives.
6. **4:15–4:45 — Contact and public communication.** Review a prepared contact note/advisory. Edit audience and exact message. Approve then Publish to demo board. It is a local record only, with no phone, SMS or public-alert connection. Show Setup automation switches.
7. **4:45–5:00 — State the boundary.** “The extraction, organized response plan, demo resource decisions and closure-aware routes are working. We use free hosted inference and a small local road graph to fit this laptop. Real dispatch integrations and operational validation remain future work.”

## Backups and failure proof

- AI limit/failure: source/error stays available. Use Review a report manually or Use an exact written instruction and label it manual. Never claim a fallback fixture is fresh AI output.
- Map unavailable: saved coordinates, cached road routes, route steps and the fictional site plan remain. Real map tiles need internet.
- No supported route: the demo unit holds; review access. Do not present dotted endpoint gaps as driving directions.
- Unknown location: Review location → local landmark/intersection search or estimated map point; provide the reason. No automatic dispatch from a caller-only coordinate.
- Pause a link in Simulator: send and observe queued/unconfirmed. Restore; actual modeled delivery resumes. At 1,000 bit/s wait for modeled airtime or explicitly switch to Local direct for a shorter software demonstration.
- Field page closed: browser-persistence receipt remains unconfirmed until reopened. Received is a human reaction, not proof of comprehension.
- Mic denied: allow microphone or use the synthetic audio upload. No playback: read exact text; do not claim the speakers played.

The presenter still needs to try actual microphone acoustics, speaker volume, unfamiliar phrasing and a timed rehearsal. No demo video or hackathon submission was published.
