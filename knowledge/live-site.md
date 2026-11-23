# StopotsBOT: stopots.com as observed

Snapshot: `fix/bot-game-loop` @ `ceb80c9` plus uncommitted work (2026-11-22). Observed with headless Chromium on 2026-11-22: 2 passive sessions in public rooms, 3 test rooms created and closed. Class names below ignore the `jsx-<hash>` classes, which change per build.

## Screens of one round
1. Fill: `.headerGame .letter p` holds the letter. Fields are `.answers .answer` rows with `legend p` (label) and `input#inputText-N` (0 based, maxlength 20). Bottom button is STOP!, disabled until every field has text.
2. Validation, one screen per category (12 in public rooms): `.validation h2` is the category, `.validation .answer label p` the answers, bottom button AVALIAR. A new screen mounts its button disabled for 800 ms.
3. Ranking: the letter `<p>` is replaced by `<figure class="icTrophy">`, bottom button ESTOU PRONTO. This button is a toggle: a second click undoes the first.
4. Lobby before the next round: the letter is "?".
- The bottom button lives in `.game > .bottom`. During a swap the old one sits in `.page-exit` and the new one in `.page-enter`.
- Inactivity popup: `.popupSystem` with h4 INATIVIDADE and `button.btPopup` (OK). An idle player is sent back to the landing page after it.
- Own player row has class `you`: `.players .list .player.you`.

## Entering a room
- Landing: `.start .input input` (maxlength 15) and the JOGAR button in `.start .action`. JOGAR asks `/api/server?direct=1&lang=pt` for any public room, then the URL becomes `/pt/game`.
- A room has its own URL `https://stopots.com/pt/<digits>`, which shows the join page: `.join-content .user .input input` and the ENTRAR button in `.join-content .user .button`.
- CRIAR SALA opens `.popupSystem.privacy` with radios `#private` (default, needs a password) and `#public`. The owner lands on a settings screen and must click INICIAR.
- A guest of a private room gets `.popupSystem.popupPassword` after ENTRAR.

## Socket
- `wss://sv-NN.stopots.com/socket.io/?EIO=4&transport=websocket`. Frames are socket.io arrays `42[top, code, payload]`. The bot only reads them for the feed; the DOM still drives the play.
- Mapped by correlating frames with the screen in 2 probes (received frames, top "9" = room event):
  - `8` `[letter, bool, n]` next letter drawn. `9` `[[labels]]` round categories; a label can be `SHORT|Long description`.
  - `3` `null` answer time is over (arrives right before the first validation). `10` `[index, answers, valid flags]` one validation screen.
  - `4` `[player id]` that player confirmed the validation screen. `11` `[[id, name, avatar, points], ...]` ranking.
  - `6` `[id, bool]` ready toggle. `7` `[id, n]` emoji n. `14` `[[id, name, avatar]]` joined. `15` `[id]` left.
  - Unknown, shown raw: `13` `[id, id, 1, 4]`, `22` `null`, `37` `[id, bool]`.
- Top "10" is the room state sent on join: `[room id, settings, round, players, ...]`. Top "8" with a number means the server removed the player (seen with 3 after inactivity).
- Sent by the client: `["1",0,name,avatar,null]` login, `["4","pt"]` join any public room, `["6",roomId,null]` join one room, `["9","2",index,ANSWER]` an answer, `["9","4",[bools]]` validation, `["9","6",true]` ready.

## What the extension gets wrong
- content.js looks for classes `category` and `modal`, which the site does not ship, so it never fills anything. Left undone on purpose (decision 8).
