#!/usr/bin/env python3
"""
build_artifact.py - makes a single-file copy of the game with every recorded voice clip embedded,
for publishing where separate files are not possible (the claude.ai artifact viewer).

  python build_artifact.py                # writes remi-bubble-club-voiced.html next to index.html
  python build_artifact.py out.html       # custom output path

index.html stays the hosted version (GitHub Pages) and keeps loading clips from voices/.
"""
import base64, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "index.html")
vdir = os.path.join(HERE, "voices")
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "remi-bubble-club-voiced.html")

html = open(src, encoding="utf-8").read()
# strip the document skeleton: the artifact tool adds its own
m = re.search(r"<body[^>]*>", html)
if m:
    html = html[m.end():]
html = re.sub(r"\s*</body>\s*</html>\s*$", "\n", html)

manifest = json.load(open(os.path.join(vdir, "manifest.json"), encoding="utf-8"))
inline, total = {}, 0
for char, bank in manifest.items():
    inline[char] = {}
    for key, rel in bank.items():
        path = os.path.join(vdir, rel)
        if not os.path.exists(path):
            print("missing clip, skipped:", rel)
            continue
        data = open(path, "rb").read(); total += len(data)
        inline[char][key] = "data:audio/mpeg;base64," + base64.b64encode(data).decode()

tag = "<script>window.VOICES_INLINE=" + json.dumps(inline, ensure_ascii=False, separators=(",", ":")) + ";</script>\n"
marker = "<script>\n(function(){"
if marker not in html:
    sys.exit("Could not find the game's main script in index.html; the marker '<script>\\n(function(){' is missing.")
html = html.replace(marker, tag + marker, 1)
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out}: {os.path.getsize(out)/1e6:.1f} MB, {sum(len(b) for b in inline.values())} clips ({total/1e6:.1f} MB of audio)")
