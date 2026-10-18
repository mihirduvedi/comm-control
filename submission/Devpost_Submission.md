# Comm Control

## Elevator pitch

Comm Control turns spoken reports into mapped incidents and coordinated response plans, helping operators review uncertainty, assign available teams and route around reported blockages.

## Project description

### Inspiration

A report like “There's smoke near City Hall” leaves a coordinator with several decisions to make. Where is the incident? What help is needed? Which team is available, and can it reach the scene? The answers often arrive across separate calls and messages, while the situation keeps changing.

We built Comm Control to bring that work into one place. We wanted the original report to stay connected to the decisions it produces, so an operator can check what someone actually said before acting on an AI interpretation.

### What it does

Comm Control turns a spoken report into a structured incident that an operator can review, locate on a map and coordinate a response to. The prototype includes separate Downtown Los Angeles and USC campus workspaces.

An operator can record a voice report in the browser, review the transcript and extracted details, and confirm the event location. The incident retains its source evidence, including uncertainty such as “I don't know if anyone is still inside.” Missing or unresolved locations hold the response for review.

Once a reviewed report reaches the control center, the system checks available demo resources by capability and finds a supported route around reported road or path blockages. A persistent resource queue lets the operator arrange next stops, pause automatic advancement, finish work and reassign a task. Reported blockages remain active until supported clearance or an explicit operator decision reopens the route.

Operators can prepare and approve outgoing instructions, with receipt, acknowledgment and reply tracked as separate states. Case history keeps corrections and earlier decisions available for review.

The same workflow has civilian and proposed government applications. Campuses, warehouses and facilities teams could use it for daily operations. Emergency-response organizations could use a future validated version to organize incoming reports and coordinate resources during disruptions. Our current demo uses fictional reports and teams; it does not dispatch real responders.

### How we built it

We built the frontend with React, TypeScript and Vite, and the backend with Python and FastAPI. SQLite stores reports, source evidence, resource assignments, queues and case history.

Browser audio goes to Groq-hosted Whisper for transcription and GPT-OSS for structured extraction. Source excerpts remain attached to the resulting claims so operators can check the interpretation. We refined extraction prompts and added local evidence guards and prioritization rules rather than training model weights.

Leaflet and bundled OpenStreetMap data support the city and campus views. Local routing graphs account for reported closures, while capability and availability checks determine which simulated resources can take a task. Version checks, idempotency and transactions protect queue changes against conflicting updates.

We also built a compact-packet transport simulator to exercise delayed delivery, retries and receipts. Hosted AI requires internet access, and the transport simulation does not establish physical radio performance.

### Challenges we ran into

The hardest part was deciding when the system should wait. A caller's location may differ from the incident location. A place name may be ambiguous. A reported blockage can make an otherwise suitable team unable to reach a case. We made those unresolved states visible instead of forcing a precise pin or an assignment.

We also had to keep coordination consistent as conditions changed. Queued work rechecks current closures when a resource becomes available. A failed reassignment preserves the original assignment, and a stale blockage remains blocked until someone has evidence to reopen it.

Voice intake introduced another practical challenge: starting a new report must open a fresh call, while refreshing the browser should preserve an interrupted one. We implemented distinct paths for those actions and kept failed recordings available for retry.

### Accomplishments that we're proud of

We built a working path from voice intake through reviewed incident records, mapping, resource allocation and response planning. Both workspaces preserve their own queues and resources, while the interface keeps source evidence and uncertainty accessible beside the operational view.

The project verification record reports 241 backend tests and 45 distinct browser checks passed. Four hosted speech/model checks were skipped in that release. These results cover software behavior and recovery; they do not establish model accuracy or operational emergency readiness.

### What we learned

The quality of a response plan depends on what the system preserves from the report. A confident summary is less useful if it loses uncertainty, changes the meaning of a statement or hides the source. We learned to keep interpretation reviewable and make missing information an explicit part of the workflow.

We also learned that coordination continues after an assignment. Resources need queues, closures need a clearance process, and delivery needs states that distinguish an attempted send from a person's acknowledgment.

### What's next for Comm Control

Our next step is a supervised pilot with a facilities team, measuring case review time, critical corrections and assignment quality. We would use those observations to refine the workflow and evaluate speech and extraction against realistic, consented reports.

We plan to add regional map packs, local operating procedures and evaluated language support. A Spanish-language warehouse pilot in Mexico City is a proposed expansion after an initial Los Angeles pilot. Hardware transport integration and government deployment would require separate testing and validation.

## Built with

Python, FastAPI, React, TypeScript, Vite, SQLite, Groq, Whisper, GPT-OSS, Leaflet, OpenStreetMap, Web Audio, MediaRecorder, pytest, Playwright

## GitHub / source code

https://github.com/mihirduvedi/comm-control

## Thumbnail

Upload Comm_Control_Thumbnail.png. It is 1200 × 800 pixels (3:2), approximately 200 KB.

## Gallery captions

1. Operator workspace: review an incoming report alongside its mapped location, source evidence and response plan. Fictional reports and teams.
2. Resource coordination: capability-based demo assignments and persistent next-stop queues support ongoing work.
3. Voice intake: record a report, review its transcript and confirm the incident location before adding it to the received queue.

## Optional short answers for additional information

### Dual-use applications

Comm Control's initial civilian use is daily coordination for campuses, warehouses and facilities teams. Its proposed government use is helping emergency-response operators organize incoming reports, review uncertain locations and coordinate available resources during disruptions. The shared foundation is source-linked voice intake, mapping, resource availability and human-reviewed response planning. Government use would require operational validation, appropriate security controls and integration with existing procedures.

### Global expansion

We would start with a supervised Los Angeles facilities pilot, then evaluate a Spanish-language warehouse pilot in Mexico City. Expansion would require tested language support, regional maps and local response procedures. Each deployment would need evaluation with its users rather than assuming the Los Angeles workflow transfers unchanged.

### Business model

Our proposed model is a $2,000 site setup fee and a $500 monthly subscription per site. Setup would cover maps, local terminology and workflow configuration. Pricing, support needs and AI usage costs still need customer validation.

### Federal funding

We would investigate DHS S&T SBIR Phase I as a possible funding route, subject to an applicable solicitation, topic fit and eligibility. This is a proposed route, not funding received or an application submitted.

### Team

Mihir Duvedi: coding and technology.
Tyler Tran: business and research.
Shen Tan: business and research.

## Links to add yourself

Demo video: add your hosted video URL.
Slides: add your chosen deck URL if requested.
Live app: no public hosted app is claimed; the repository contains local setup instructions.
