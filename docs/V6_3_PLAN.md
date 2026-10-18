# V6.3 implementation plan

Objective: a larger map with wheel zoom, independent city/campus operating views, warm body typography and a sliding header selection across real pages.

1. Complete: inspect supplied clipped-map screenshot, existing API/UI and prior passing evidence. Preserve private source/run data in a pre-change SQLite backup.
2. Complete: scope snapshots, alerts, sessions, queue orders, assignments and intake by operating world. Preserve old sources without rewriting them. Reject cross-world grouping and allocation.
3. Complete: retain the header during real route changes so its selection can animate. Keep link URLs, browser history, modifier-click behavior and auth contracts.
4. Complete: locally host Nunito Sans for body text while preserving the existing title family. Compress incident context into a disclosure. Give the main canvas near-square desktop proportions, square mobile geometry, wheel zoom and an expanded map view.
5. Complete: render and repair desktop/mobile, wheel/pan, keyboard, reduced-motion, context isolation and regression flows. Run the relevant browser/backend/build checks.
6. Complete: preserve original sources, boot a clean extraction, verify hashes/secrets and deliver the current handoff. The actual run stays intact.

Design direction: Map desk. The map is the largest working surface; the incident queue and response ledger support it. The incident title and location remain visible, while long context is disclosed. The white/blue palette and rounded header remain. Geometry, readable type and continuity carry the design instead of added decoration. We considered a map-only screen and a denser CAD grid; both would hide useful case context or increase clutter.

Behavior contract: city and USC are operating contexts rather than interchangeable basemaps. The selected context follows navigation/reload/history. A confirmed source location outside its originating context cannot allocate the other world's resources. Original evidence is unchanged. Global transport/provider configuration and recoverable full-run reset remain explicitly shared demo controls.

Sources: Nunito Sans from Google Fonts, with local font/license/provenance files; Leaflet's official reference for wheel behavior. No real sensor, unit, agency, access status or indoor egress verification is claimed.
