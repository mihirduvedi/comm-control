# Map data and attribution

© OpenStreetMap contributors. OpenStreetMap data is available under the Open Database License (ODbL) 1.0: https://opendatacommons.org/licenses/odbl/1-0/ . Copyright information: https://www.openstreetmap.org/copyright .

`downtown-la.osm.json` is a bounded unmodified Overpass response containing original OSM elements, received from https://overpass-api.de/api/interpreter . The adjacent manifest includes the exact query, timestamp, bounding box, byte count and SHA-256. This source database is redistributed under ODbL 1.0. The in-memory graph is built by `server/geography.py`; no proprietary map database is included. Original OSM tag names and IDs are preserved.

Leaflet is BSD-2-Clause; its license is included with the npm package. Standard OpenStreetMap raster tiles are requested normally for the visible viewport and are not bundled or bulk downloaded. Respect https://operations.osmfoundation.org/policies/tiles/ . No service-level availability is promised. No public Nominatim geocoding endpoint is used.

USC campus: `usc-campus.osm.json` is a bounded OSM response, licensed ODbL 1.0; adjacent manifest records source, bounds, hash and retrieval date. `server/usc_atlas.py` builds the outdoor graph and custom SVG plan from this geometry. USC public Facilities campus map and Transportation entrance descriptions supply building/gate reference names. No map tiles or proprietary satellite imagery are bundled or requested for the USC plan. Approximate campus gate points and operator-marked access points are separate from surveyed building exits.
