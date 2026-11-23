# StopotsBOT: the Python bot (app.py)

Snapshot: `fix/bot-game-loop` @ `ceb80c9` plus uncommitted work (2026-11-22). Verified with ruff and one live headless session in a public room. No automated Python test exists (user decision 11).

## Run
```
uv run --frozen python app.py --headless [--username NAME] [--log-file PATH] [--room ID]
```
- Playwright 1.58 needs chromium build 1208: `uv run playwright install chromium` once.
- `--room` takes digits only and uses the join page of that room. Not proven live yet. Rooms with a password are refused with an error (decision 17).
- Exit codes: 0 on Ctrl-C, 1 on a crash, 2 on a bad argument. On exit the log lists every letter + category left blank.

## Shape
- `GameEngine`: loop every 0.2 s, rejoin when the entrance page shows, give up after 5 drops in a row or 10 failed ticks in a row.
- `RoundPlayer`: dismiss popup, confirm the screen (AVALIAR every time, ESTOU PRONTO once per screen, never STOP!), fill a new round.
- `GamePage`: every read is a `query_selector` or one `evaluate`, so nothing waits for an element that may never come.
- `RoomEntrance`: landing page or join page, same flow, different selectors (`Entrance.public()` / `Entrance.for_room()`).
- The repo hook `immutable-rules-check.py` blocks: logic in `__init__`, more than 3 parameters, union types, vague method names such as `run`.

## Bugs of the old app.py (all reproduced by the analysis workflow)
- Only round 1 was filled: the "filled" flag was reset only after clicking JOGAR, a button that does not exist inside a room.
- `text_content` / `input_value` auto-wait up to the 180 s default timeout when the element is gone (ranking screen, validation screen). That explains the 121 s and 222 s gaps in the old stopots.log.
- The inactivity popup was never clicked: the code looked for the text "afk bypass", the button says "OK".
- `context.route(...)` was never awaited, so resource blocking never applied. `except TimeoutError` never caught the Playwright timeout. `--single-process` kills the browser on close.

## Traps found live on 2026-11-22
- After clicking JOGAR the landing screen stays in the DOM for about 1.5 s inside `.screen-exit`. A naive "is the username input present" check sends the bot into a rejoin loop. Evidence, first run: `Back on the entrance page (drop 1 of 5) - rejoining` five times, then `Bot crashed: sent back to the entrance page 6 times in a row`, `EXIT=1`.
- argparse runs `type=` on string defaults, so a validator must accept the empty default.
- `websocket` is a Page event. `context.on("websocket")` never fires. Frame payloads are plain `str` or `bytes`, they have no `.text`. Fixed: both socket listeners attach to the page. Evidence, run 3: `ws=38 google=0`.
- The HTTP log filter used `"stopots.com" in url`, which also matched Google analytics URLs that carry the site in a query parameter. Fixed with a hostname check.

## Logs and feed (decisions 19 and 20)
- Terminal: INFO and above. File (`--log-file`, default stopots.log, rewritten on every start): DEBUG too (HTTP, raw socket frames, each validation screen, per player confirmations).
- One line per round (`Round 2 [B] 12/12 filled: label=answer | ...`) and one after each ranking (`Ranking after round 1: 100 pts, position 4 of 5`). "round 0" means the bot joined during a ranking.
- `Feed | ...` lines come from `RoomEventTranslator`, which maps socket codes to sentences (table in `live-site.md`). A frame it cannot read is logged at DEBUG and skipped, never fatal.
- A public test room for `--room` can be made with a second headless browser: CRIAR SALA, pick `#public`, read the id from the URL, click INICIAR through JS once a guest is in (a share popup covers the button). Strangers can join such a room from the room list.
