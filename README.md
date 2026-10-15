# Remi's Bubble Club

A counting, letters, spelling and music game for Remi, hosted by Irie the sloth, Katy, Gaga, HUNTR/X and Uncle Archie.

- `index.html` is the whole game. Open it, or visit the GitHub Pages address for this repository.
- `voices/` holds optional recorded character voices. Without it the game uses the device's built-in voices.
- `make_voices.py` records every line the game speaks with ElevenLabs and fills `voices/`.

## Playing on the iPad

Open the Pages address in Safari, tap Share, then "Add to Home Screen". The first tap unlocks sound.
Singing in tune and the roar meter use the microphone. Safari asks once; allow it.

## Adding real character voices

1. Make a free account at elevenlabs.io and copy your API key (profile menu, API keys).
2. On a computer with Python 3, open a terminal in this folder and set the key:
   - PowerShell: `$env:ELEVENLABS_API_KEY = "your key"`
   - Mac: `export ELEVENLABS_API_KEY="your key"`
3. `python make_voices.py --list` shows every line and the credit cost. `python make_voices.py --voices` lists the voices on your account; paste any you prefer into `VOICE_IDS` at the top of the script.
4. `python make_voices.py` records the lines into `voices/` and writes `voices/manifest.json`. It only records what is missing, so it is safe to re-run.
5. Commit and push the `voices` folder (or upload it next to `index.html`). Reload the game. The grown-ups panel (hold the gear) shows how many clips were found and lists any line still spoken by the device voice.

To name your Country in Uncle Archie's Acknowledgement, type it in the grown-ups panel and record that line with `python make_voices.py --country Wurundjeri` (use your Country's name).

## Changing voices later

Delete that character's folder inside `voices/`, change its id in `VOICE_IDS`, and run the script again.
