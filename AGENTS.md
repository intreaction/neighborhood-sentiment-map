# Place Lab live presentation

Take a step back and explore context before answering technical questions.

For live page control and data questions, use the localhost CLI below. The CLI
returns structured JSON with a short `say` answer and an acknowledgment when the
page changes. Use it directly; browser automation adds avoidable latency.

## Start a demo

- From this repository, start `npm run start:place -- --open` in a persistent
  terminal session if the local bridge is not running. Read its launch URL.
- Check `node src/place_cli.mjs get_context` once to learn the selected city,
  time period and connected page. Then use individual tool calls directly.
- If multiple pages are connected, run `node src/place_cli.mjs sessions` and
  use `--session ID` for the user's presentation page.
- If the sandbox blocks local sockets, request the CLI's localhost access once
  using the `node src/place_cli.mjs` approval prefix, then reuse that approved
  access for subsequent commands.
- Do not print `.place-runtime.json`: it contains local bridge credentials.

## Fast voice commands

```sh
node src/place_cli.mjs set_view --city Tucson
node src/place_cli.mjs rank_areas --measure engagement --limit 1 --show
node src/place_cli.mjs get_area_profile --zip 85701
node src/place_cli.mjs compare_areas --zips 85701,85719
node src/place_cli.mjs get_area_timeline --zip 85701 --grain quarter
node src/place_cli.mjs navigate --direction down
node src/place_cli.mjs navigate --direction north
node src/place_cli.mjs set_time --period 2016Q3
node src/place_cli.mjs set_view --project-id sun-link --chart sentiment
node src/place_cli.mjs compare_projects --kind trail
node src/place_cli.mjs define_term --term 'business engagement'
```

- Activity/busiest defaults to `engagement` (reviews/km²/year). Most reviews
  uses `reviews`. Interpret traffic as historical review activity and say so.
- Infer omitted city and time from the connected page. Data queries can use an
  explicit city without a browser. For “find and show”, use `--show` in one call.
- Speak the `say` result concisely. Don't narrate routine tool execution in voice
  presentation mode unless a command fails or the user requests an explanation.
- Acknowledge a view change only if `display.status` is `applied`. If the page
  changed during the command, refresh context and retry once with a new command ID.
- Query time overrides use `--time '{"period":"2016Q3"}'`. They don't change
  the map unless `--show` is also requested. ZIPs are strings.
- Keep answers historical. Data end in 2021, income/poverty use older ACS estimates,
  review activity doesn't measure visits/sales, and project comparisons aren't
  causal effects or forecasts. Include the relevant qualification without
  repeating the full limitations on every simple navigation command.

## Computer use

Prefer connectors, APIs, CLIs or native AppleScript before UI automation on macOS.
Use UI inspection when a visual check is needed. Sending messages to other people
requires user authorization.

See docs/presentation/Voice-Control.md for the tool catalog and HTTP contract.
