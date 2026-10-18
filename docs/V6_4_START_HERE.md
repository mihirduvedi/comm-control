# Comm Control v6.4

Open [USC campus](http://127.0.0.1:8765/control?world=usc) or [Downtown LA](http://127.0.0.1:8765/control?world=city). Use the existing Mac launcher for a fresh browser session if access has expired.

Your USC world now contains six fictional reports at real buildings, combined into five work items: a gas concern at Michelson, an alarm at Leavey, two pressure checks at SGM, a door fault at Tutor Campus Center and a light fault at Kaprielian. Five simulated teams have mapped outdoor routes. The later pressure report updates the work item to 220 psi while keeping the earlier 145 psi source. Your city reports are retained.

The same warm font, white panels, blue borders and category colors now run through the workspace, Resources and Sessions. Category and urgency tags stay visible above the selected incident. Resources uses larger text and shows equipment conditions, team destinations and routes. Dropdown chevrons have space around them.

Choose the operating workspace in the header. Reports, alerts, queue order, sessions and resources remain separate. The choice follows navigation and reload. In Resources, select a building or work item to inspect its sources and assigned response. Reported conditions and demo pressure ranges are distinct from a real sensor feed.

Use **Live call** in the header to capture a new call directly. You do not need to create a session first. Finish recording, review the transcript and event location, then add the incident. Unknown locations stay for review; USC calls do not allocate city units.

Wheel or trackpad scrolling over either map zooms it. Scroll outside the canvas or focus the middle panel and use Page Up/Down for long details. **Expand map**, **Restore workspace** and Escape work as before. The USC view fits the selected response route and destination. Blocked road/path segments stay excluded until a matching later clearance or manual review reopens them.

**New test** in Resources saves and restarts the complete local run, including both worlds. Saved tests can restore it. To replay the USC examples in an empty USC world, choose **Load USC demo** or its Simulator scenario. Teams are staged only if they are pristine, available demo resources; an operator’s active or previously updated team is not moved.

This is a local coordination demo. Buildings and outdoor geometry come from public map data; reports, readings, pressure ranges and teams are fictional. Indoor exits and current gate access have not been independently verified.
