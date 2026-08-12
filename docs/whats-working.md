# Feature status

This is a community work in progress. The wrapper has only been tested with a
Nintendo DSi, macOS, and Pokemon White 2.

Working in that setup:

- Game Sync from a physical DSi, including tuck-in and wake-up
- Loading Dream World as that save
- Persistent berries and items

Not working:

- Pokemon Bistro and Blow Out Candles
- Making a wish at the Tree of Dreams
- Sending newly befriended Dream World Pokemon to the Entralink or Entree
  Forest
- Dream Catalogue. Its server endpoint is missing, so the blank panel can
  leave the room blurred until the projector is reopened.
- C-Gear skins, Pokedex skins, and Musical shows. Their files are bundled, but
  the restored Customize page cannot save a selection and the download-content
  handler does not return the selected file.
- Dream Point progression and the tucked-in Pokemon level-up. On the original
  service, earning 500 Dream Points during one sleep session awarded one level
  when the Pokemon woke. This restoration currently sends zero levels gained.
- **Exit and continue sleeping** in the standalone projector. It cannot return
  to the original browser wrapper and may load forever. Close and reopen the
  projector URL to continue with the Pokemon still asleep.
- Share Shelf

The tucked-in Pokemon can return to the save. The broken path is the reward
transfer for newly befriended Pokemon. A disposable test Pokemon is still
safest while the project is unfinished. The two missing minigames are absent
from known public asset dumps.

New accounts currently start with 99 of all 64 berry types. This is an upstream
development placeholder. The original first-visit tutorial awarded five of one
randomly selected damage-reducing Berry type, so the current inventory does not
represent normal progression.
