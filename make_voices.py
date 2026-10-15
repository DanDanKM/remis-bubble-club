#!/usr/bin/env python3
"""
make_voices.py - records every line that Remi's Bubble Club speaks, one small mp3 per line,
using ElevenLabs, and writes voices/manifest.json so the game plays the recordings instead of
the device voice. Run it from the folder that holds index.html.

  python make_voices.py --list                 show every line per character, no API calls
  python make_voices.py --voices               list the voices on your ElevenLabs account (name + id)
  python make_voices.py                        record anything not recorded yet, then write the manifest
  python make_voices.py --only katy            one character only
  python make_voices.py --country Wurundjeri   also record Uncle Archie's Acknowledgement naming this Country

Before running: set your key in the shell
  PowerShell:  $env:ELEVENLABS_API_KEY = "your key"
  Mac/Linux:   export ELEVENLABS_API_KEY="your key"

Pick the voices below from elevenlabs.io (Voices -> copy the voice ID). The defaults are ElevenLabs
premade voices; swap any you like. Re-running only records lines whose mp3 is missing, so you can
change one voice, delete that character's folder, and run again.

The free plan (about 10,000 credits a month) covers the whole set on the Flash model, which costs
half a credit per character. The script prints the character count first so you can check.
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error

VOICE_IDS = {
    # bright, bouncy pop star
    "katy":   "cgSgspJ2msm6clMCkdW9",   # Jessica
    # smooth, glam
    "gaga":   "XB0fDUnXU5powFXDhCwa",   # Charlotte
    # HUNTR/X: Rumi is the main voice; Mira and Zoey only say their own hello lines
    "huntrx": "9BWtsMINqrJLrRacOk9x",   # Aria (Rumi)
    "mira":   "pFZP5JQG7iQjIQuC4Bku",   # Lily
    "zoey":   "XrExE9yKIg1WjnnlVkGX",   # Matilda
    # warm Australian uncle, slow and kind
    "archie": "IKne3meq5aSn9XLyUdCD",   # Charlie (Australian)
    # deep, relaxed sloth host
    "irie":   "nPczCjzI2devNBz1zQrb",   # Brian
}
SETTINGS = {
    "katy":   {"stability": 0.45, "similarity_boost": 0.8, "style": 0.45, "speed": 1.0},
    "gaga":   {"stability": 0.5,  "similarity_boost": 0.8, "style": 0.35, "speed": 0.95},
    "huntrx": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.4,  "speed": 1.0},
    "mira":   {"stability": 0.45, "similarity_boost": 0.8, "style": 0.4,  "speed": 1.0},
    "zoey":   {"stability": 0.45, "similarity_boost": 0.8, "style": 0.4,  "speed": 1.05},
    "archie": {"stability": 0.6,  "similarity_boost": 0.8, "style": 0.2,  "speed": 0.88},
    "irie":   {"stability": 0.6,  "similarity_boost": 0.8, "style": 0.3,  "speed": 0.85},
}
MODEL = "eleven_flash_v2_5"
API = "https://api.elevenlabs.io/v1"

# ---------- the lines, mirroring index.html ----------
NUMS = [str(n) for n in range(1, 21)]
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LET = {"A": ("ah", "apple"), "B": ("buh", "banana"), "C": ("kuh", "cat"), "D": ("duh", "dog"), "E": ("eh", "egg"),
       "F": ("fff", "fish"), "G": ("guh", "guitar"), "H": ("huh", "hat"), "I": ("ih", "ice cream"), "J": ("juh", "jelly"),
       "K": ("kuh", "kangaroo"), "L": ("lll", "lion"), "M": ("mmm", "moon"), "N": ("nnn", "nose"), "O": ("oh", "octopus"),
       "P": ("puh", "purple"), "Q": ("kwuh", "queen"), "R": ("rrr", "Remi"), "S": ("sss", "star"), "T": ("tuh", "tiger"),
       "U": ("uh", "umbrella"), "V": ("vvv", "violin"), "W": ("wuh", "whale"), "X": ("ks", "box"), "Y": ("yuh", "yo-yo"),
       "Z": ("zzz", "zebra")}
WORDS = ["Remi", "cat", "dog", "sun", "egg", "ham", "mum", "dad", "bug", "hat", "pop", "bus", "pig", "bee", "car",
         "roar", "star", "moon", "fish", "bird", "cake", "frog", "boat", "duck", "kite", "ball",
         "apple", "tiger", "happy", "music", "dance", "pizza", "train", "heart", "smile", "zebra", "sloth"]
STORIES = {
    "CAT": ["Little Cat sat on the warm red rock.", "The sun went down and the stars came out.", "Cat purred, and dreamed of fish."],
    "DOG": ["Old Dog waited by the river for his friend.", "His friend came home with a big smile.", "Dog wagged his tail all the way back to camp."],
    "SUN": ["The sun woke up slow over the hills.", "It warmed the kangaroos and the sleepy wombats.", "Everyone said good morning, sun."],
    "EGG": ["Mother Emu kept her eggs warm in the grass.", "One egg wobbled.", "Then a tiny chick said hello to the world."],
    "BEE": ["Busy Bee visited every yellow flower.", "She carried the sweet nectar home to share.", "That is how the honey got made."],
    "BUS": ["The big bus rolled down the long dusty road.", "It stopped for Nana, and it stopped for the kids.", "Everyone waved to the driver."],
    "PIG": ["Pig loved the mud more than anything.", "She rolled and rolled till she was shiny and brown.", "Then she had a long cool drink."],
    "CAR": ["Our old car hummed along by the sea.", "The windows were down and the wind sang.", "We counted the pelicans on the way."],
    "HAT": ["Uncle wore his big black hat every day.", "One windy day it flew off, high as a kite.", "A cheeky cockatoo brought it back."],
    "BUG": ["A tiny bug climbed a tall green stalk.", "It was a long way up, but she did not give up.", "At the top, she opened her wings and flew."],
    "STAR": ["One little star was the first out every night.", "It winked at the kids by the campfire.", "They made a wish, and said thank you."],
    "MOON": ["The moon followed us all the way home.", "Round and bright, like a silver plate.", "Nana said it was watching over everybody."],
    "FISH": ["Grandad showed me how to sit still by the water.", "A silver fish jumped, splash, and we laughed.", "We let the little one go."],
    "BIRD": ["A magpie bird sang on the gum tree every morning.", "Its song was like water over stones.", "We sang back, a little bit out of tune."],
    "FROG": ["Frog sat on a lily pad and waited for rain.", "Drip, drop, the rain came.", "Frog sang his big happy song all night."],
    "DUCK": ["Mother Duck led her ducklings across the road.", "The cars stopped and waited, nice and kind.", "One, two, three, four, all safely across."],
    "BOAT": ["Our little boat rocked on the gentle waves.", "We paddled past the mangroves, quiet as can be.", "A turtle poked up its head to say hello."],
    "KITE": ["Remi's kite went up and up in the blue sky.", "It danced with the wind like a bird.", "We held the string tight and laughed."],
}
TRY = ["Not that one. Have another look!", "Oops! Try again, Remi.", "Nearly! Look carefully.", "Hmm, not quite. You can do it!"]
LEVELS = ["Level up, Remi! You're a", "now.", "Bigger ones coming!", "That's the top!", "Let's try some easier ones for a bit.",
          "Bubble", "Star", "Rainbow", "Rocket", "Crown", "Sound on!"]
SOUNDS = sorted({s for s, _ in LET.values()})
LETTER_WORDS = sorted({w for _, w in LET.values()})


def letter_lines():
    return [f"{L}." for L in LETTERS]


def lines(country=None):
    L = {}
    L["katy"] = NUMS + TRY + LEVELS + [
        "Hi Remi! I'm Katy. Let's pop bubbles and count. Roar!",
        "Welcome to the jungle, Remi! Would you pop them? Could you pop them?",
        "Pop the bubbles, count them up, and hear the tiger cub roar!",
        "ROAR! You did it, Remi!", "Hear you roar! Amazing!", "Louder than a lion! Brilliant!",
        "Stripes and sparkles! That's right!", "You're a champion, Remi!",
        "Pop", "bubbles! Let's count together.", "bubbles!", "ROAR!", "Tap a bubble to pop it!",
        "How many", "tigers", "parrots", "monkeys", "butterflies", "flowers", "frogs",
        "Tap each one to count, then pick the number.", "Tap each one to count it.", "You counted", "Tap the number",
        "Tap each one and count. One, two, three.", "Find the number", "Where is", "That's", "We want", "Look for",
        "It looks like this.", "You found",
        "Roar like a lion! As loud as you can! Musicians call loud, forte.", "Loud is forte!",
        "Now whisper, quiet like a mouse. Musicians call quiet, piano.", "Big roar! Rooooar!", "Tiny whisper. Laaa.",
        "Loud is forte, quiet is piano. You did both!",
    ]
    L["gaga"] = letter_lines() + SOUNDS + LETTER_WORDS + TRY + LEVELS + [
        "Hello Remi, it's Gaga. Let's find some letters, superstar!",
        "A letter's hiding, big or small.", "Can you find it? You find them all!",
        "Superstar! That's the one!", "Bravo, Remi! Fabulous!", "You were born to shine!", "Dazzling! Let's do another!",
        "Applause for Remi!",
        "Find the letter", "Find little", "says", "Like", "is for", "That's", "We want", "Look for", "It looks like this.",
        "Which letter says", "starts with",
    ]
    L["huntrx"] = NUMS + TRY + LEVELS + [
        "We're HUNTR/X!",
        "Golden! Team Remi wins!", "Hunters high five! Yes!", "Shining bright, Remi!", "Boom! You counted it!",
        "Rumi, Mira and Zoey say: perfect!",
        "Green eggs here, and green eggs there.", "Add them up with golden flair!",
        "Golden voices, high and low.", "Sing with us, Remi. Here we go!",
        "and", "makes", "take away", "leaves", "green eggs", "green egg", "then",
        "more hop in. Count them all up, let's begin!", "sat in a row", "more came. How many? Let's go!",
        "Would you count them, here and there?", "how many are there?", "on a plate. Sam-I-Am ate",
        "Count the ones that are left.", "Tap each egg to count it.", "That's", "Tap the number",
        "Tap every egg, both groups, and count them all.", "Count only the eggs Sam didn't eat.",
        "Listen to my tune, then tap it back.", "Almost! Listen again.", "Your turn! Tap the same keys.", "Tap",
        "do", "re", "mi", "fa", "so", "la", "ti", "What an echo!",
        "Listen. Is it high like a bird, or low like a whale?", "That one is high, like a bird up in the sky.",
        "That one is low, like a whale down deep.", "High like a bird! Musicians say high pitch.",
        "Low like a whale! Musicians say low pitch.",
        "Tap the drum on every tick. Ready? Press start!", "Nearly! Listen for the tick, then tap on each one.",
        "Press start, then tap the drum on every tick.", "beats on time! You kept the beat!", "You danced to the beat!",
        "Listen to the note, then sing it back. Laaa! Keep the bird in the gold bubble.",
        "Two notes: do, then so. Listen, then sing each one.",
        "Let's sing Twinkle Twinkle! One note at a time. Listen, then sing it.",
        "Listen again, then sing it with me. Laaa.",
        "Nearly! Sing a bit higher or lower till the bird sits in the gold bubble.", "Sing laaa, nice and long.",
        "You sang Twinkle Twinkle in tune!", "do and so, in tune! Golden!", "right in tune!",
        "I'm Rumi.",
    ]
    L["mira"] = ["I'm Mira."]
    L["zoey"] = ["And I'm Zoey! Let's add green eggs and sing, Remi!"]
    story_lines = [s for story in STORIES.values() for s in story]
    L["archie"] = letter_lines() + WORDS + TRY + LEVELS + story_lines + [
        "G'day Remi. I'm Uncle Archie. Let's spell some words together, nice and slow.",
        "Letter by letter, slow and true.", "Let's spell a word, just me and you.",
        "Deadly, Remi. That's it.", "Beautiful, little one.", "You spelt it. Good on you.", "Slow and steady, you got it.",
        "That's my clever girl.",
        "Now find", "Let's spell your name, Remi!", "Find the letter", "Let's spell", "That spells", "Can you spell",
        "We acknowledge the Traditional Owners of the land we're playing on, and pay our respects to Elders past and present.",
    ]
    if country:
        L["archie"].append(f"We acknowledge the Traditional Owners of the land we're playing on, the {country} people, and pay our respects to Elders past and present.")
    L["irie"] = NUMS + letter_lines() + SOUNDS + LETTER_WORDS + TRY + LEVELS + [
        "Irie, Remi! I'm Irie the sloth. Welcome to the Bubble Club. Take your time, no rush.",
        "Easy now, Remi. Tap a letter, hear it sing.", "Tap a number, count each thing. Irie!",
        "Irie! Nice one.", "Big up yourself, Remi!", "Easy does it. Lovely.", "Sweet, sweet, Remi.",
        "Irie, Remi! Welcome to the Bubble Club.", "Tap a window to play, no rush.",
        "says", "is for", "stars.", "You have", "stickers, Remi. Irie!", "sticker, Remi. Irie!",
        "Earn 5 stars to get your first sticker!",
    ]
    # de-duplicate while keeping order
    for k, v in L.items():
        seen, out = set(), []
        for t in v:
            if norm(t) not in seen:
                seen.add(norm(t)); out.append(t)
        L[k] = out
    return L


def norm(s):
    """Must match Clips.norm in index.html."""
    s = s.lower().replace("’", "").replace("'", "")
    s = re.sub(r"[^a-z0-9/ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:48] or "x"


def api(path, data=None, key=None, raw=False):
    req = urllib.request.Request(API + path, data=json.dumps(data).encode() if data else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json",
                                          "Accept": "audio/mpeg" if raw else "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read() if raw else json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--voices", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--country")
    ap.add_argument("--out", default="voices")
    a = ap.parse_args()
    all_lines = lines(a.country)
    chars = sum(len(t) for v in all_lines.values() for t in v)
    if a.list:
        for k, v in all_lines.items():
            print(f"\n== {k} ({len(v)} lines) ==")
            for t in v:
                print("  " + t)
        print(f"\n{sum(len(v) for v in all_lines.values())} lines, {chars} characters (about {chars // 2} credits on {MODEL})")
        return
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY first (see the top of this file).")
    if a.voices:
        for v in api("/voices", key=key)["voices"]:
            print(f"{v['voice_id']}  {v['name']}  ({', '.join(f'{k}={x}' for k, x in (v.get('labels') or {}).items())})")
        return
    available = {v["voice_id"] for v in api("/voices", key=key)["voices"]}
    todo = {k: v for k, v in all_lines.items() if not a.only or k == a.only}
    for k in todo:
        if VOICE_IDS[k] not in available:
            sys.exit(f"Voice id for '{k}' ({VOICE_IDS[k]}) is not on your account. Run --voices and paste one into VOICE_IDS.")
    print(f"{sum(len(v) for v in todo.values())} lines, {chars} characters in total. Recording the missing ones...")
    manifest_path = os.path.join(a.out, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    for k, texts in todo.items():
        folder = "huntrx" if k in ("mira", "zoey") else k
        os.makedirs(os.path.join(a.out, folder), exist_ok=True)
        bank = manifest.setdefault(folder, {})
        for t in texts:
            fname = f"{folder}/{slug(t)}.mp3"
            path = os.path.join(a.out, fname)
            if not os.path.exists(path):
                for attempt in range(3):
                    try:
                        audio = api(f"/text-to-speech/{VOICE_IDS[k]}?output_format=mp3_22050_32",
                                    {"text": t, "model_id": MODEL, "voice_settings": SETTINGS[k]}, key=key, raw=True)
                        with open(path, "wb") as f:
                            f.write(audio)
                        print(f"  {k}: {t}")
                        break
                    except urllib.error.HTTPError as e:
                        body = e.read().decode(errors="ignore")[:200]
                        if e.code == 429 or e.code >= 500:
                            print(f"  waiting ({e.code})..."); time.sleep(8 * (attempt + 1)); continue
                        sys.exit(f"ElevenLabs refused '{t}': {e.code} {body}")
                else:
                    sys.exit("Gave up after three tries. Run the script again later; finished lines are kept.")
                time.sleep(0.25)
            bank[norm(t)] = fname
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=0, ensure_ascii=False)
    print(f"Done. {sum(len(b) for b in manifest.values())} clips listed in {manifest_path}. Upload the voices folder next to index.html.")


if __name__ == "__main__":
    main()
