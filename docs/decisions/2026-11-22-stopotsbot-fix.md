# StopotsBOT: fix the bot so it plays every round

Date: 2026-11-22. Source: grill session after a read-only analysis (4 lenses, each finding re-run by a skeptic, plus 2 passive probes of a public room).

## Decisions

| # | Decision | Chosen | Why | Depends on |
|---|----------|--------|-----|------------|
| 1 | Source of truth for the dictionary | dictionary.json. stopots-autofill/dictionary.js is generated from it | The two hand kept copies drifted (115 vs 112 categories) and dictionary.js lost getAnswer | none |
| 2 | Uncommitted dictionary expansion | Clean it and keep it | 7924 answers, only 5753 valid: 458 one letter fillers, 1713 wrong letter | 1 |
| 3 | Surfaces that must work perfectly now | Python bot run locally (uv run app.py) | Chosen by the user. Extension and Docker are out of this scope | none |
| 4 | Where to validate live | Public room, headless, random username | Same as the bot does today | 3 |
| 5 | How to fix app.py | Rewrite the game loop into small steps, remove dead code, replace absolute XPaths with class and id selectors seen on the live site | The loop is the bug: only round 1 is ever filled | 3 |
| 6 | STOP button | Never click it | Keeps the current discreet behaviour | 5 |
| 7 | Disconnect or kick | Rejoin alone, give up with a non zero exit after 5 drops in a row | 5 is the retry count safe_goto already uses | 5 |
| 8 | Extension | Minimum only: bring getAnswer back, generate dictionary.js from the clean json, tests green, a test that fails when the two files differ | Out of scope (3), but must not stay red | 1, 3 |
| 9 | Cleaning rule | Base rule (2+ letters, right first letter after accent folding, no duplicates, folded keys) plus 3 fixes: drop 2 letter non words by a fixed list (keep fe, no, pe, re, ra with their accents), drop answers longer than 20 chars, move 4 misfiled words (enfermaria, calcinha, coronel, soldado) | The site input cuts at 20 chars. Fragments such as "qu" are not answers | 2 |
| 10 | No answer in the dictionary | Leave the field blank on both surfaces. getAnswer returns "" instead of "X-NaoSei" | One behaviour. Makes the uncommitted "if (!answer)" guard in content.js work | 8, 9 |
| 11 | Automated test for the Python bot | None. Only the live session | Chosen by the user | 5 |
| 12 | Definition of done for the live session | 3 complete rounds in a row: filled, all validation screens confirmed, ESTOU PRONTO clicked, no exception in the log, clean exit on Ctrl-C | Proves round 2 onward, which is the main bug | 4, 5 |
| 13 | Packaging (Docker, requirements.txt, README, .gitignore, uv.lock) | Not touched | Chosen by the user | 3 |
| 14 | Delivery | New branch from master, logical commits, no push. The uncommitted work of the user lands in those commits because it lives in the same files | Chosen by the user | none |
| 15 | Extras | --room <id> to join one specific room, and a summary of letter + category left blank, logged when the bot stops | Chosen by the user | 5 |
| 16 | Proof for --room | Claude creates a test room with a second headless browser and joins it with the bot | No third party involved, does not block on the user | 15 |
| 17 | Room password | Not supported. If the room asks for a password the bot logs it and exits with an error | Less to build and to prove | 15 |
| 18 | Uncommitted features that never worked | Make both work: WebSocket logging (handler attaches late today) and blocking of images, CSS and fonts (route call is never awaited today). The CSS blocking must be proven in the live session | Chosen by the user | 5 |
| 19 | Bot logs (asked mid build, "melhore os logs") | Terminal shows INFO and above, the log file keeps DEBUG (HTTP, WebSocket, each validation screen). One INFO line per round with every answer, one line with points and position after each ranking | A round used to print about 38 INFO lines plus hundreds of DEBUG lines in the terminal | 5, 18 |
| 20 | Real time feed of the room (asked mid build) | Translate the WebSocket frames the site sends into one readable line each, in the terminal and the file. Unknown event codes are shown raw. "Player confirmed the validation" goes to the file only (about 100 per round) | The chat panel of public rooms only has emojis and join/leave notices; the socket carries everything | 18, 19 |
| 21 | README (asked after the build, narrows decision 13) | Rewritten to teach install, run, options, how to read the output, how to edit the dictionary. Docker and the extension are described as not working with this version | The old README had an empty install step and a wrong dictionary format | 13 |

Fixes that go in without a question because they are plain bugs: username cut to 15 chars (site limit), remove --single-process (kills the browser on close) and ignore_https_errors, safe_goto catches the Playwright error instead of the builtin TimeoutError, a crash exits non zero instead of 0, dictionary.json is opened next to app.py instead of the current directory.

Assumptions made by Claude (cheap to undo, say so if wrong): branch name fix/bot-game-loop. HTTPRequestLogger stays as it is (it works). The generator for dictionary.js is one npm script inside stopots-autofill/package.json, no new file. The extension "enabled" write back in content.js stays.

## Open risks

- The live site can change its markup at any time. Selectors were read from the DOM on 2026-11-22.
- Blocking CSS may change what Playwright sees as visible. If the live session shows that, decision 18 is reopened.
- Whether a room created by one headless browser lets a second player join and start a match is not known yet. If it does not, --room stays marked as not proven.
- A bot in a public room can be reported by players. Decision 6 keeps it discreet, but it still confirms every validation screen in about 1 second.
- No automated Python test (decision 11): the next layout change breaks the bot without warning.

## Left undone on purpose

- Extension selectors do not match the real site, so the extension has never filled an answer (not at HEAD either). Also: ESTOU PRONTO is toggled every 500 ms, JOGAR is clicked on the landing page, lastLetter never resets, tests pin a guessed DOM, lint reports nothing.
- Docker: requirements.txt cannot install on Python 3.13, the image downloads Firefox and WebKit, compose publishes port 8000 with nothing listening.
- README: empty install step, wrong dictionary format, sample output the code no longer prints. No repo .gitignore. uv.lock is not tracked. tabulate is unused.
