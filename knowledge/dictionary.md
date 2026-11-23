# StopotsBOT: dictionary

Snapshot: `fix/bot-game-loop` @ `ceb80c9` plus uncommitted work (2026-11-22). Numbers measured with a one-off Python script on the working tree and on `git show HEAD:dictionary.json`.

## Format
- `dictionary.json` is the source of truth: `{"a": {"animal": ["anta", ...]}}`. Letter keys are lowercase. Category keys are the game label lowercased with accents removed (the README example is wrong about this).
- The bot folds the label with `unidecode`, the extension with NFD strip. An unfolded key (the old "tem na farmácia") can never be found.
- A slot may be an empty list: both surfaces then leave the field blank.

## Extension copy
- `stopots-autofill/dictionary.js` = generated data + a marker line `// END GENERATED DATA` + the lookup functions. Regenerate with `npm run build:dict` inside stopots-autofill. Never edit the data there.
- jest fails if the two files differ or if an answer is not playable (wrong first letter, shorter than 2, longer than 20, unfolded key).

## Cleaning applied on 2026-11-22
```
{'before': 7924, 'short': 458, 'wrong': 1713, 'dup': 6, 'long': 7, 'fragment': 58, 'moved': 4, 'after': 5686, 'slots': 2989, 'empty_slots': 270, 'categories': 115}
violations after 0
```
- 1700 of the wrong letter answers came from 3 categories whose same list had been pasted under all 26 letters (animal aquatico, tem no circo, tem na floresta).
- Fragments dropped by a fixed list, only in the 50 categories added by the uncommitted expansion: qu, ki, yi, xi and similar. Kept: fé, nó, pé, ré, rã, dj.
- Not cleaned: filler words reused across unrelated categories of one letter (jing, damasco, kiwi). They pass the rule because the letter is right.
