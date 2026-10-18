# v6.5 verification

The final full Chrome suite passes 39 checks with four hosted tests skipped in 2.9 minutes. The focused final layout/USC journey passes three checks. Strict TypeScript/Vite build, two formatting tests and preflight pass. The UI static checker reports zero errors and one reviewed warning.

This release changes the frontend and UI copy. No backend behavior, schema, source record or allocation setting was changed. The backend's 227-test passing result is the v6.4 baseline; it was not rerun for this frontend-only pass.

The current release logs are `evidence/v6-5-build.txt`, `v6-5-browser-final.txt`, `v6-5-layout-final.txt`, `v6-5-format.txt`, `v6-5-preflight.json` and `v6-5-static-ui.json`. The full browser suite uses isolated localhost:8766 storage. It never resets the user's actual localhost:8765 run. Hosted model tests remain opt-in.

New checks cover page scrolling moving all three columns together, a non-scrollable middle pane, footer reachability, keyboard document navigation, wider queue/title rows, inset borderless detail tabs, full report-row borders, readable voice entry, direct intake from Sessions, mobile resizing and reopening from Map, and source-aware status labels. Missing locations have no invented team or route. The USC provisional call view suppresses pre-existing incident routes and shows Not reviewed rather than borrowing the last selected report's response.

Existing browser journeys retain automatic assignment, source review, approval and recipient response, world isolation, persisted resource updates, equipment/report grouping, blocked route avoidance, reset/save/restore, map wheel zoom, expansion, native drag edge auto-scroll, keyboard ordering, sliding navigation and reduced motion. Native microphone-denial and failed-audio recovery paths run without hosted inference.

The final changed screens were visually inspected at desktop and mobile sizes. The new workspace axe reports have no serious or critical findings. The static checker has zero errors and one reviewed warning about legacy glass rules. Shared navigation/map overlays retain restrained glass under the user's design direction. This is not a full assistive-technology certification.

The release script checks the current actual run against the private pre-v6.4 backup, requiring all original reports and source objects to match. It checks every archive hash, ZIP integrity, exclusion of known private runtime values, dependencies and databases, plus clean authenticated boot and offline City/USC fixture replay in a temporary extraction. The archive ships no private runtime state. See `v6-5-release-check.json` for final counts and outcomes.

No new hosted audio/extraction call, real microphone recording, weight training, sensor connection, real emergency dispatch, public deployment or external submission was performed. Live hardware rehearsal still requires the user's microphone, speakers and Internet/provider access. Public geometry does not establish current gate access or indoor egress; teams and equipment conditions are fictional demonstration data.
