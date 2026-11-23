# StopotsBot

A bot that plays [Stopots](https://stopots.com/pt/) (Stop, Adedanha, Adedonha) for you. It opens the site in a Chromium browser driven by Playwright, joins a room, and fills every category of every round with an answer from `dictionary.json`.

https://github.com/user-attachments/assets/7987a2d1-1daf-4620-86d8-2fc647aead91

## What it does in a room

- Reads the letter of the round and fills each empty category that has an answer in the dictionary. A category with no answer stays blank.
- Confirms every validation screen (AVALIAR) and marks itself ready after each ranking (ESTOU PRONTO).
- Never presses STOP. The round ends when another player stops it or the time runs out.
- Closes the inactivity popup, and joins again by itself if the site sends it back to the start page. After 5 drops in a row it gives up.
- Prints what happens in the room in real time: who joined or left, the answers under validation, the ranking.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
git clone https://github.com/iklobato/StopotsBOT.git
cd StopotsBOT
uv sync
uv run playwright install chromium
```

## Run

Join a random public room, with no browser window:

```bash
uv run python app.py --headless
```

Stop the bot with Ctrl-C.

| Option | What it does | Default |
|--------|--------------|---------|
| `--headless` | Run without opening a browser window. Leave it out to watch the bot play | window is shown |
| `--username NAME` | Name shown in the room, cut at 15 characters (site limit) | a random Brazilian username |
| `--room ID` | Join one specific room. The id is the number at the end of the room link, for example `06719` in `https://stopots.com/pt/06719` | a random public room |
| `--log-file PATH` | Where the full log is written. The file is replaced on every start | `stopots.log` |

Examples:

```bash
# watch the bot play in a visible browser, with your own name
uv run python app.py --username Maria

# play in the room of a friend
uv run python app.py --headless --room 06719
```

Rooms protected by a password are not supported: the bot logs an error and exits.

## What you see

The terminal shows the game. The log file also keeps the debug detail (every HTTP request, every raw WebSocket frame, every validation screen).

```text
23:04:27 - INFO - Bot started as [maria] (headless: True)
23:04:34 - INFO - Feed | Room 07817 has 10 players: ana, joao, ..., maria
23:04:34 - INFO - Joined a room from https://stopots.com/pt/ as [maria]
23:04:34 - INFO - Game loop started
23:04:44 - INFO - Feed | Validation 4: ROSA
23:04:46 - INFO - Feed | ana left the room
23:07:10 - INFO - Feed | Next letter drawn: A
23:07:12 - INFO - Feed | Round categories: Esporte, Instrumento Musical, Game, ...
23:07:12 - INFO - Round 1 [A] 12/12 filled: Esporte=atletismo | Instrumento Musical=agogo | Game=asphalt | ...
23:09:33 - INFO - Feed | Ranking: joao 120, ana 110, maria 100, ...
23:09:33 - INFO - Ranking after round 1: 100 pts, position 4 of 5
23:10:56 - INFO - Left blank for lack of an answer in dictionary.json: 0
23:10:56 - INFO - Bot stopped by user
```

How to read it:

- `Round N [L] x/y filled`: the answers the bot typed for letter L. A second line lists the categories left blank, if any.
- `Ranking after round N`: your points and position. `round 0` means the bot joined in the middle of a ranking.
- `Feed | ...`: events sent by the site. An event the bot does not know yet is printed raw as `Room event <code>`.
- When the bot stops, it lists every letter and category that had no answer, so you know what to add to the dictionary.

Exit codes: `0` after Ctrl-C, `1` after a crash (a screenshot `error_<time>.png` is saved in the current folder), `2` for a wrong option.

## Dictionary

`dictionary.json` holds the answers. Letters are lowercase. Category keys are the label shown in the game, in lowercase and without accents:

```json
{
  "a": {
    "animal": ["andorinha", "anta"],
    "meio de transporte": ["aviao"],
    "paf": ["alecrim"]
  }
}
```

To add answers, edit `dictionary.json` and follow these rules, which the tests check:

- the answer starts with the letter it is filed under and has 2 letters or more
- the answer has 20 characters at most (the site cuts longer text)
- the category key has no accents and no capital letters, for example `"tem na farmacia"`

Then refresh the copy used by the browser extension and run its tests:

```bash
cd stopots-autofill
npm install
npm run build:dict
npm test
```

## Chrome extension

`stopots-autofill/` holds a Chrome extension with the same idea. It does not work with the current layout of the site yet: its page selectors are out of date. Use the Python bot.

## Docker

The `Dockerfile` and `compose.yaml` in this repo were not updated or tested with this version of the bot. Use the `uv` steps above.

## Troubleshooting

- `Executable does not exist` on start: run `uv run playwright install chromium` again. Each Playwright version needs its own browser build.
- The bot joins but never fills anything: the site layout probably changed. The selectors live in the `Selector` class at the top of `app.py`.
- `Bot crashed: out of the room 5 times in a row`: the site kept refusing the bot, or was down. Wait a few minutes and start it again.
