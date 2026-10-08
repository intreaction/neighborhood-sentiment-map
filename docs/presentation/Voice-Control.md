# Local voice and agent control

Run Node.js 22 or newer. The prepared datasets and built web assets are checked in;
no API key, Python analysis, Chrome flag, extension or browser automation is needed.

```sh
npm run start:place -- --open
```

The server binds to `127.0.0.1:8766`, or a free port if occupied. It prints the page
URL and writes `.place-runtime.json` with private local credentials (ignored by Git).
The CLI discovers the running server from that file. Re-running the default launch
reuses a healthy bridge with the same dataset revision. Restart after changing
server code or dataset files; the server pins JSON data to its startup snapshot.
The Python `src/serve_place.py` is a static viewing alternative without voice tools.

## Codex presentation session

Open a Codex session in this repository. Its AGENTS.md explains the CLI. A useful
initial prompt is:

> We are presenting Place Lab. Use `node src/place_cli.mjs` directly for all data
> questions and page commands. Check context once, then keep each interaction to
> one CLI call where possible. Use `--show` for finding and selecting an area.
> Keep voice answers to one or two sentences and read the tool's `say` result.
> Infer city and period from the connected presentation page.

Then activate the voice interface available in your client. Example requests:
“Switch to Tucson”, “Find the area with the most activity and show it”, “Go down”,
“Compare this ZIP with 85719”, “Show Sun Link's sentiment chart”, “Go back to the map”.
The model still handles speech and intent; the bridge removes the Playwright path.
End-to-end voice latency includes the model/client; `timing.server_ms` measures only
local query/command handling, including browser acknowledgment for view commands.

## Tools

| Tool | Arguments and behavior |
|---|---|
| `get_context` | Coverage, full schemas, selected page and timeline |
| `rank_areas` | `measure`, optional city/order/limit/filters/time/show |
| `get_area_profile` | ZIP, optional city/time/show; measures, medians, ranks, support |
| `compare_areas` | Two to five ZIPs, optional time; each with its own city context |
| `get_area_timeline` | ZIP, optional city/grain/smooth/time; reviews and sentiment series |
| `compare_projects` | Optional kind: all/trail/waterfront/civic/transit |
| `get_project` | Historical `project_id`, e.g. sun-link |
| `define_term` | Term key or name |
| `set_view` | Any combination of city/zip/focus/section/kind/project_id/chart |
| `set_time` | Period, or from/to/length; optional grain/smooth; reset or start_at_project |
| `navigate` | up/down/left/right/in/out/north/south/east/west; optional steps 1–5 |

`node src/place_cli.mjs tools` returns complete JSON schemas without page automation.
Activity means engagement density. Total reviews are a different measure. Other
measure keys are listings, engagement_change, sentiment, sentiment_vs_metro,
access_discussion, income, poverty and area. Null values mean limited/unavailable
data. The page's period and support thresholds are included in query context.

```sh
node src/place_cli.mjs rank_areas --city Tucson --measure engagement --limit 1 --show
node src/place_cli.mjs rank_areas --city Tucson --measure reviews --limit 3
node src/place_cli.mjs rank_areas --city Philly --measure access_discussion --filters '[{"measure":"poverty","min":20}]'
node src/place_cli.mjs get_area_profile --zip 19134 --time '{"period":"2016Q3"}'
node src/place_cli.mjs set_time --from 2013 --to 2017 --length 4
node src/place_cli.mjs set_time --reset
node src/place_cli.mjs set_view --section map
```

The CLI preserves string ZIPs and period strings, accepts `--args` or one JSON
object for nested arguments, prints one JSON response, and exits nonzero on errors.
Responses include `say`, context/dataset revision and timing. View-changing calls
also include `display.status: applied`, the page's actual view and its revision.

## HTTP integration for any local LLM application

Read the runtime file inside your local application, then send authenticated JSON.
Never include its token in prompts, URLs or public logs.

```js
const runtime = JSON.parse(await fs.readFile('.place-runtime.json', 'utf8'));
const response = await fetch(runtime.url + '/api/call', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${runtime.token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    tool: 'rank_areas',
    arguments: {measure: 'engagement', limit: 1, show: true},
    command_id: crypto.randomUUID()
  })
});
const result = await response.json();
```

Expose `/api/tools` schemas as your model's function tools and forward function
calls to `/api/call`. HTTP is the integration contract; a specific LLM provider or
MCP setup isn't required. The CLI is already usable through Codex's shell tool.

| Endpoint | Purpose |
|---|---|
| GET /api/health | Authenticated readiness and dataset revision |
| GET /api/tools | Eleven tool definitions |
| GET /api/sessions | Connected page IDs, current state, revision |
| POST /api/call | tool, arguments, optional session_id and command_id |
| POST /api/connect | Same-origin browser registration; establishes session cookie |
| GET /api/sessions/:id/events | Persistent SSE command stream |
| POST /api/sessions/:id/state | Browser's manually changed view and revision |
| POST /api/sessions/:id/results | Browser acknowledgment with actual result/view |

## Sessions and delivery

One connected page is selected automatically. With multiple pages, use
`node src/place_cli.mjs sessions`, then `--session ID`, or specify `session_id` in
HTTP calls. Queries requiring inferred context and all view actions use that page.
Without a page, city-dependent queries require an explicit city and use the
published default period unless given a time override. Project/glossary queries
also work without a page. A query with `show: true` requires a connected page.

Calls for one page are serialized. Each view command has an ID, a five-second
expiry and an expected page revision. The browser applies allowlisted operations
through its normal application functions and reports success. Manual changes are
reported after a short debounce, and stale commands are rejected. The event stream
reconnects and registers again after a server restart.

Supply the same `command_id` to safely retrieve the cached outcome of an HTTP
retry. Reusing it with different arguments fails. Results and failures are cached
for 30 minutes in memory. Commands are not automatically replayed after a disconnect;
a timed-out command may already have applied, so inspect current state before retrying.
A batch of validated view operations executes in sequence; it is not a rollback
transaction if the browser encounters an unexpected failure partway through.

The server binds to loopback, checks Host/Origin and requires bearer credentials
or an HttpOnly same-origin cookie. Input schemas reject unknown fields and invalid
values. Commands contain named operations, never arbitrary JavaScript. Sessions and
query context are isolated; research inputs stay in memory and aren't modified.

## Troubleshooting

- No runtime file: start the Node server in a persistent terminal.
- No connected page: open its printed URL and allow the app to finish loading.
- More than one page: choose a session explicitly.
- Page changed: fetch context and send a fresh command after the manual change.
- Command timeout: inspect context before retrying; the page might already have moved.
- Static hosting: the browser tools still work through `window.placeLab.call`, but
  the localhost bridge is available only when using the Node server.

## Observed local latency

Five calls of each kind were measured on this Mac during development. Data-query
CLI calls had a median of 67 ms; combined rank-and-show calls had a median of 55 ms,
including browser acknowledgment. Median server processing was 1.6 ms and 5 ms,
respectively. These are a small local sample, not end-to-end voice measurements or
a guaranteed latency. Speech recognition, model inference and the Codex tool runner
are additional. The browser was also checked for timeline numerical parity, manual
city synchronization, and automatic reconnection after a server restart.
