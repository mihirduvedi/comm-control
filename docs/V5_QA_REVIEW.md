# V5 QA review

## Behavior and visual contract

The actual built interface was inspected through the in-app browser and Chrome screenshots. The blue navigation floats with rounded corners and an outer gutter. The queue/map/response layout, source quotes and actual map remain central. No additional decorative dashboard cards were introduced. Desktop and mobile case views and the recipient natural-voice view are captured in evidence.

## Repaired defects

- Header demo label had dark text on its inherited dark badge. Removed the badge fill and verified axe again.
- Setup retained inherited white text after the header became light. Replaced with blue ink.
- Recipient connection, clock and mode labels failed contrast against the new blue surface. Darkened the relevant roles and reran the real playback/accessibility check.
- New case fixture setup initially omitted the JSON body for city seeding and inherited disabled automation from an earlier settings test. Made both prerequisites explicit, retained assertions for real received reports and real assignment release.
- New closeout count assertion assumed whitespace between DOM nodes. Changed to a whitespace-tolerant visible count assertion.
- Chrome's intercepted streaming response body returned empty in a test even though the actual browser audio played. Verification now checks content length, real playback time, stop, and byte-identical cached responses using the authenticated HTTP test client.
- Natural voice initially required model terms. The user explicitly confirmed acceptance; six actual voices and real recipient playback were subsequently verified.
- Stale case revisions are rejected; outstanding acknowledgment resets after a conflict. The open editor retains its reviewed revision until save.
- Incident detail tabs now support arrows/Home/End and one Tab stop. The case journey exercises keyboard selection.
- The earlier large Vite bundle advisory was removed by splitting maps/react modules; no new dependency was added.

## Review

Concept 2, hierarchy 2, typography 1, composition 2, imagery/form 2, craft 2, accessibility 2, content fit 2 (15/16). System typography remains an intentional practical choice. The visual review is for these tested screens; this is not assistive-technology or real-device certification.

Owned copy was reviewed for concrete actions, matching outcomes and restrained tone. Source quotations, approved instructions, proper names and historical events were deliberately preserved. Fictional sample recordings remain labeled generated, with hashes and exact scripts. No human-performance or operational dispatch claim is made.

Final results and remaining human rehearsal checks are recorded in the v5 handoff and verification file.
