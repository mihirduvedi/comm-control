# Local demo access repair, October 17, 2026

The local server was healthy, but ordinary links opened a browser without the operator capability. The old launcher also saved access in only one tab, and a launch fragment on an already-open route did not remount the app.

The launcher now creates a one-use link that expires after 30 minutes. Its fragment is exchanged through a same-origin JSON request for an HttpOnly, SameSite Strict browser cookie. Sessions expire after eight hours and survive server restarts. Only hashes of temporary links and browser sessions are stored, outside report objects and exports. The durable operator capability stays in the local launcher. Anonymous visitors cannot create links or acquire operator access. Explicit field and invalid bearer credentials never fall back to operator cookies. Cookie mutations and sockets check the exact origin, including the port. Existing field links and source permissions remain in place.

The app checks the browser session on entry, handles same-page access fragments, clears the fragment from the address bar, and accepts a used link only when that browser already has a valid session. Fresh browsers need a new launcher link. The regular demo address works in connected browsers, including new tabs. Use `scripts/open_app.py --link` to create a temporary link for a different browser.

Verified: 137 backend tests, production TypeScript/Vite build, and five focused browser checks. Those checks cover a signed-out page receiving a launch fragment without a full navigation, reloads, new tabs, a persisted session creation, link replay from another browser, field-role isolation, microphone denial, and saved-recording recovery. Desktop and 390px mobile renders were inspected, with no serious or critical automated accessibility findings in the connected live-call screen. The actual 8765 service was restarted and checked with all eight existing reports and eight sessions retained. The working live-call screen was also observed in the Codex browser panel. No new provider calls were needed for this access repair.

Current source and the running app include this repair. The earlier V4 ZIP remains the pre-repair release.
