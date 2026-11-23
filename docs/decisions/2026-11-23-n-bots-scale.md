# StopotsBOT: run N bots on minimal hardware

Date: 2026-11-23. Source: grill session after measuring the browser bot on this Mac. Follows [2026-11-22-stopotsbot-fix.md](2026-11-22-stopotsbot-fix.md).

## Facts measured before deciding

| Fact | Value | How |
|---|---|---|
| This Mac | i9-9980HK, 16 threads, 64 GB | `sysctl hw.ncpu hw.memsize` |
| 1 browser per bot (today) | about 720 MB RSS, 0.66 core | headless shell, 1 context on the landing page, process tree sampled 5 times |
| 1 shared browser, 10 contexts | 3728 MB RSS, 2.4 cores (about 370 MB and 0.25 core per bot) | same method |
| Blocking every third party host | 3430 MB for 10, and the page broke in 4 of 10 contexts | same method, so not a usable lever |
| Site protocol | plain socket.io v4 over websocket, no token: `emit(login, 0, name, avatar, uid)` on connect | read in the site bundle `_app-*.js` |
| reCAPTCHA | only on the contact form (`/api/contact`) | same bundle |
| DigitalOcean | account active, droplet limit 25. 512 MB/1 vCPU US$4, 1 GB/1 vCPU US$6, 2 GB/1 vCPU US$12 per month | `doctl account get`, `doctl compute size list` |

Not measured yet: the browser bot inside a room, and anything about the socket client (memory per bot, CPU, how the server treats 50 connections from one IP).

## Decisions

| # | Decision | Chosen | Why | Depends on |
|---|----------|--------|-----|------------|
| 1 | Where the N bots play | Public rooms, at most 1 bot per room | Chosen by the user. Several bots in the same public room take seats from real people and approve each other, so that case is not built | none |
| 2 | N | 10 to 50 at the same time | Chosen by the user | none |
| 3 | Hardware | Cheap VPS, 1 to 2 vCPU, 1 to 4 GB | Chosen by the user | none |
| 4 | Engine | No browser: talk socket.io directly with python-socketio (new dependency, with its asyncio extra that brings aiohttp) | With a browser a 4 GB / 2 vCPU VPS holds about 8 bots (measured 370 MB and 0.25 core each), below N | 2, 3 |
| 5 | Running on the VPS | Docker | Chosen by the user. The image needs no browser now, so it is small | 3, 4 |
| 6 | Watching the bots | Web status page | Chosen by the user | 2 |
| 7 | Browser bot (app.py) | Kept until the socket bot plays 3 full rounds live with several bots, then deleted | Fallback while the new engine is unproven | 4 |
| 8 | Who can open the status page | Listens on 127.0.0.1 only, opened from outside with `ssh -L` | Nobody on the internet finds it | 6 |
| 9 | Who creates the VPS | Claude, in the DigitalOcean account of the user | Chosen by the user. Claude still asks for an explicit OK at the exact create and destroy commands | 3 |
| 10 | Live ramp | Straight to 50 bots | Chosen by the user | 2 |
| 11 | VPS size cap | 1 GB / 1 vCPU, US$6 per month. Created only after the local measurement shows 50 bots fit; if they do not, Claude comes back with the number before anything bigger | Cheapest size with margin, if the estimate holds | 3, 4 |
| 12 | Where the 50 bot live test runs | From the VPS | An IP ban then hits the VPS, not the home IP of the user | 9, 10 |
| 13 | VPS after the test | Destroyed right after the test | Chosen by the user. Billing is hourly, so the test costs cents | 9 |
| 14 | Status page content | One summary table: one line per bot (name, room, round, points, position, state, drops), totals on top, refresh every 5 s without JavaScript | Smallest page that answers "is every bot playing" | 6 |

Assumptions made by Claude (cheap to undo, say so if wrong):
- Developing the socket client means live runs of 1 or 2 bots from this Mac, the same as on 2026-11-22. Only the 50 bot run goes from the VPS.
- The local measurement of 50 bots uses a fake socket.io server on this Mac that replays the frames recorded on 2026-11-22. It touches stopots.com 0 times.
- Region nyc1 (stopots.com sits behind Cloudflare, so the region barely changes latency).
- One Python process runs all N bots with asyncio and shares one dictionary in memory. Each bot keeps its own log file.
- Two bots that land in the same room: the newer one leaves and joins again, up to 3 tries, then stops with an error line on the page.

## Plan

1. Socket client spike, 1 bot from this Mac: login, join a public room, answer, validate, ready, rejoin, reusing DictionaryService and the feed translator. Done when it plays 3 rounds 12/12 live. About 2 to 3 hours.
2. N bots in one process: a runner that starts N bot engines, keeps the room id of each one to enforce one bot per room, one log file per bot. About 1 hour.
3. Status page on 127.0.0.1 (aiohttp, already pulled in by the socket library). About 30 min.
4. Local load proof: fake server replaying recorded frames, 50 clients inside `docker run --memory 1g --cpus 1`, RSS and CPU sampled. Output: measured MB per bot and the max N for 1 GB, shown before any VPS exists. About 1 hour.
5. Dockerfile for the socket bot (python 3.13 slim, no browser). About 20 min.
6. VPS: show the exact `doctl compute droplet create` command, wait for the OK, create it, deploy the image, run 50 bots, watch the page through `ssh -L`. Stop at the first sign of a block (refused connections, mass kicks, HTTP 429). About 1 hour including a few rounds.
7. Show the exact destroy command, wait for the OK, destroy the VPS.
8. If step 6 played 3 full rounds with several bots, delete the browser bot and update README and knowledge/.

## Open risks

- The site can ban the VPS IP at any N. The straight to 50 ramp (decision 10) means that if it happens, the number where it started is unknown.
- The protocol is undocumented. A change on the site breaks the socket bot, and after step 8 there is no browser fallback.
- The python-socketio memory per bot is an estimate until step 4. If 50 do not fit in 1 GB, decision 11 is reopened.
- Fifty public rooms each get one bot that confirms every answer as valid. That is the same behaviour as the single bot of 2026-11-22, but spread over 50 rooms.
