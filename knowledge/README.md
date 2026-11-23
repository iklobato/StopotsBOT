# StopotsBOT: knowledge index

Snapshot: `fix/bot-game-loop` @ `ceb80c9` plus uncommitted work (2026-11-22). Verified by running: jest, ruff, 2 passive probes of a public room, 1 live bot session (still running when this was written). Not read: Dockerfile and compose were only analysed by a workflow agent, not changed. Facts rot; re-check before acting on a number or line ref.

## Status at a glance
- **Done:** dictionary.json cleaned (7924 -> 5686 answers, 0 invalid). stopots-autofill/dictionary.js is now generated from it (`npm run build:dict`), jest 129/129. app.py rewritten: it fills every round, confirms every validation screen, clicks ESTOU PRONTO once, rejoins after a drop. Live proof (5 headless runs on 2026-11-22): run 1 played 3 full rounds in a public room (36 AVALIAR, 3 ESTOU PRONTO, 0 warnings, clean Ctrl-C exit 0); run 3 joined a test room with `--room` and filled a round; run 5 showed the new log format and the real time feed. Terminal now shows INFO only, the file keeps DEBUG.
- **Discovered:** the old bot only ever played round 1 (see `bot.md`). The extension has never filled an answer because its selectors do not match the site (see `live-site.md`). The site keeps the leaving screen in the DOM for about 1.5 s (`.screen-exit`, `.page-exit`).
- **Next steps:** 1) read the adversarial review of the diff and fix what is confirmed. 2) commit in logical commits on `fix/bot-game-loop`, no push.
- **What's left:** everything under "Left undone on purpose" in `docs/decisions/2026-11-22-stopotsbot-fix.md` (extension selectors and loop, Docker, README, .gitignore, uv.lock untracked). Filler words reused across unrelated categories in the dictionary (for example "jing" under 16 categories of J).
- **Monitor:** site markup can change at any time; selectors were read on 2026-11-22. CSS blocking is on (decision 18): if clicks start timing out, suspect it first.

## Topics
- `bot.md`: how app.py is built now, how to run it, the bugs that were fixed and the traps found live.
- `live-site.md`: stopots.com screens, selectors, room flow and socket protocol as observed.
- `dictionary.md`: data format, cleaning rule applied, how the extension copy is generated.

## Session log
- 2026-11-23: adversarial review of the diff (3 lenses + 3 skeptics) confirmed 13 findings (9 distinct). Applied 8: off-room page counts as a drop (was a silent hang forever), player memory reset before a rejoin, confirm click bound to the label read, give up on the 5th drop, feed name list cleared per room, crash screenshot cannot hide the crash, broken dictionary.json reaches the log, deeply nested frames ignored. Not fixed: "Future exception was never retrieved" on some Ctrl-C (cosmetic, 3 attempts failed). A dead origin now takes 50 to 62 min to give up (5 drops x goto backoff). Live run of the fixed code: 3 rounds 12/12, 36 validations, 3 rankings, 0 warnings.
- 2026-11-22: deep analysis (workflow, 9 agents), grill session (18 decisions in `docs/decisions/2026-11-22-stopotsbot-fix.md`), dictionary clean, extension minimum, app.py rewrite, first live session. Branch `fix/bot-game-loop`, nothing committed yet.
