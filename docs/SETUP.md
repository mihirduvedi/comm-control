# Run Comm Control locally

The public demo is the fastest way to explore saved sample incidents. Run locally to use your own microphone and hosted voice processing.

## Prerequisites

Use Python 3.11 or newer, Node.js 20.19 or a compatible newer release, npm, zsh, and FFmpeg for audio decoding. The helper scripts target macOS/zsh. Hosted processing requires internet access and your own Groq account.

```sh
git clone https://github.com/mihirduvedi/comm-control.git
cd comm-control
scripts/setup.sh
```

Configure your provider privately with the supplied helper. Enter the credential at its prompt; don't put it in a public issue, screenshot or commit.

```sh
.venv/bin/python scripts/configure_key.py
scripts/start.sh
```

In another terminal, from the repository directory:

```sh
.venv/bin/python scripts/open_app.py
```

The launcher opens the authorized workspace. A plain localhost URL doesn't grant operator access. Keep the server terminal open while using the app.

## Try the workflow

Choose **Start voice report**, allow the microphone, then use a fictional report such as:

> There's smoke near City Hall. Two people are outside. I don't know if anyone is still inside. Please send fire support.

Finish the call, review the transcript and event location, then add the reviewed incident. Only a received report gets a response plan. **Sessions** creates separate reporter views. The City and USC workspaces maintain separate operational state.

Without a configured model account, use the labeled sample scenarios and manual incident controls. Those exercise the coordination backend without running speech recognition. They aren't evidence of a new AI result.

## Checks

Build the frontend before running backend checks, because access tests also verify that the application page is served.

```sh
npm --prefix web run build
.venv/bin/pytest
npm --prefix web run test:units
```

Browser checks run against a separate test database and port:

```sh
npm --prefix web run build -- --outDir dist-next
npm --prefix web run test:e2e
```

Some hosted speech checks are gated and require explicit configuration. Check the result for skipped tests; don't count a skipped integration as a passing hosted call. The checked-in browser configuration uses Google Chrome at its standard macOS application path; install Chrome there or adjust that path for your system.

The local application uses private runtime data under `.data`. Test runs use separate data. Never reset a real operator run to prepare a screenshot or regression test. Keep provider credentials, recordings, databases and backups out of Git.

## Temporary public demo

The shared public demo is a separate sample instance. It intentionally allows visitors to explore and change fictional coordination data, and blocks hosted voice intake. Its URL depends on the host laptop and tunnel process; it isn't permanent deployment infrastructure. The local application's default access boundaries remain in place.
