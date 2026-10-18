# Comm Control v6.6

Open the running app at [Workspace](http://127.0.0.1:8765/control?world=city). The existing browser authorization is required. If a fresh browser asks for access, run `.venv/bin/python scripts/open_app.py` from the project folder; this opens a private launch link without printing it.

## Remove an incident

Select an incident, open **Case history**, then choose **Remove incident**. Review the outstanding items and confirm **Remove from queue**. Linked source reports are removed together, their evidence is retained, and their units are released. Existing road or path blockages remain active until a supported clearance or manual reopening.

Use **Archived** below the incident list to find removed cases. **Restore incident** returns them to **Closed**; reopen a case explicitly if it needs another response. Reporting sessions now allow 100 callers per workspace. Up to 100 unarchived source reports can be received across the run; removing incidents frees report capacity. **New test** saves the current run before starting another.

## Give a unit its next stops

Open [City Resources](http://127.0.0.1:8765/resources?world=city#unit-queues) or [USC Resources](http://127.0.0.1:8765/resources?world=usc#unit-queues), then expand a row under **Unit queues** or **Team queues**.

- Choose a compatible incident and **Add to queue**. Move stops up or down, or remove them.
- Keep **Take the next stop automatically** checked to advance when the resource becomes available. Global automatic assignment in Setup must also be enabled.
- **Finish assignment & take next** marks the current destination as reached and checks the next route. City incidents stay open for case review. Finishing USC work closes that work item and retains its source reports.
- **Reassign** moves a resource immediately after checking its capability, the destination and an open route. It requires a reason. The original job stays available for review.
- **Take next now** can explicitly dispatch an available resource whose automatic queue is paused.

Queues persist across reloads and saved-run restoration. A paused queue reserves its resource. Routes use the last saved position, not live GPS. Blocked or unmapped destinations hold the next stop instead of creating an unsupported route. City resources may provide additional coverage at a case; a USC work item keeps one assigned team.

## Start another voice report

Every explicit **Start voice report** click opens a blank call in the current workspace. A plain page refresh can recover an interrupted call. The previous unsent call remains in the local records but no longer fills a new intake. Other workspaces are independent.

The shortest demo path is **Start voice report → Start microphone → Finish call → review transcript and event location → Add reviewed incident**. Receipt at the control center triggers classification, mapping, resource selection and routing. It is desk microphone capture, not a telephone integration.

## Why some old City reports have no route

The operator's run contained old warehouse samples with no real event coordinates, a threat report whose location was unconfirmed, an information-only clearance, a support request waiting for the only support unit, and a medical plan that still claimed assignment after its unit had been released. The released-unit plan is repaired to a resource-review state. Shared incidents now show the route belonging to any linked source report.

Unconfirmed locations require **Locate this incident**. Missing capability requires an available suitable resource or manual reassignment. Routes outside the loaded Downtown graph, or disconnected by reported closures, require routing review. The app does not invent an address or route to make those cases appear complete.

## Interface repairs

Location picking preserves Leaflet's container classes and map clipping. The case timeline uses one centered marker/connector axis, aligns markers with timestamps and ends at the last entry. The existing typography, semantic tags, spacing and white/blue panels are retained. The loading screen has a main landmark and readable text.

This remains a local hackathon demonstration with simulated resources and transport, cached map geometry and connected AI. There is no real emergency dispatch, live traffic, indoor egress certification or model-weight training.
