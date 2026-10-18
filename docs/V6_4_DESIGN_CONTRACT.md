# Comm Control v6.4 design contract

The workspace is a dispatch desk, not an analytics landing page. The selected incident, its sources, the route and response status carry the hierarchy.

- One locally served Nunito Sans family throughout: 475 body, 650 controls, 700 headings. The previous split with system headings was rejected as incohesive.
- White panels, pale blue canvas and blue borders share a 20–22 px panel radius. Glass is reserved for navigation and map overlays, where content passes beneath it.
- Restore semantic color: medical blue, fire coral, access amber, safety violet, assistance teal. Queue tags, selected-row tint, incident tags and resource totals repeat the same meaning. No vertical colored queue stripes.
- Important page descriptions are 15–16 px; resource facts 14–16 px; resource secondary information at least 13 px. Technical map annotation may be smaller.
- Shared page headings, framed forms, tables and lists restore the spacing and contrast lost in v6.3. Empty states stay compact. Resources has no tall empty coverage panel stretched beside a long roster.
- Native selects keep their platform keyboard behavior with an 18 px SVG chevron inset 13 px from the edge and 42 px text padding. Details use the same quiet chevron with inset breathing room.
- Preserve the large map: desktop canvases at least 550 px high, mobile canvas square. Fit the selected USC response route as well as the destination footprint. Wheel zoom stays on the canvas; the enclosing panel scrolls elsewhere.
- Keep the one shared sliding selection across navigation and adjacent button bars; reduced motion disables the slide.

References consulted: [Atlassian select examples](https://atlassian.design/components/select/examples) and [Shopify Polaris Select](https://polaris-react.shopify.com/components/selection-and-input/select). Adopt the inset indicator and concise field-label grammar; retain the existing native selects and real handlers. The legacy Polaris page currently redirects to the current Polaris reference.

The current request overrides earlier font trials. Rejected Plex/Source Sans faces remain excluded from the release. Do not revive the fictional site, gray route-option blocks, Setup highlight, or decorative horizontal/vertical divider stripes.
