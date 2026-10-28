#!/usr/bin/env python3
"""
Multi-artist countdowns ("The 10 Worst Songs of the 80s") from lists.json.

    python3 make_list.py worst-80s --pick       # search YouTube only, write clips/<key>/picks.json, print them
    python3 make_list.py worst-80s              # download what picks.json says (or pick first), then render
Items in lists.json are "Artist | Song" or "Artist | Song | Shorter artist to show", #10 first.
Videos come from the same search as make_top10.py (official video, artist's own channel preferred).
"""
import json, os, subprocess, sys, time
import make_top10 as t

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    key = sys.argv[1]; pick_only = "--pick" in sys.argv
    spec = json.load(open(os.path.join(HERE, "lists.json")))[key]
    d = os.path.join(HERE, "clips", key); os.makedirs(d, exist_ok=True)
    pf = os.path.join(d, "picks.json")
    picks = json.load(open(pf)) if os.path.exists(pf) else {}
    for it in spec["items"]:
        artist, song = [p.strip() for p in it.split("|")[:2]]
        if it in picks: continue
        r = t.best_video(artist, song)
        if not r: sys.exit(f"No video found for {it!r}")
        picks[it] = r; time.sleep(4)          # go easy on YouTube
        json.dump(picks, open(pf, "w"), indent=1, ensure_ascii=False)
    n = len(spec["items"])
    for i, it in enumerate(spec["items"]):
        r = picks[it]; print(f"#{n - i}: {it}  <- {r['title']} ({r['channel']}, {r['views'] // 1000000}M)", flush=True)
    if pick_only: return
    items = []
    for it in spec["items"]:
        parts = [p.strip() for p in it.split("|")]
        r = picks[it]; path = os.path.join(d, r["id"] + ".mp4")
        if not os.path.exists(path):
            subprocess.run(["yt-dlp", "--no-warnings", *t.COOKIES, "-q", "-f",
                            "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b", "--merge-output-format", "mp4",
                            "--sleep-requests", "1.5", "--sleep-interval", "15", "--max-sleep-interval", "40",
                            "-o", path, "https://www.youtube.com/watch?v=" + r["id"]], check=True)
        items.append({"name": parts[1], "artist": parts[2] if len(parts) > 2 else parts[0], "clip": path})
    cfg = {"title": spec["title"], "highlight": spec["highlight"], "seconds_per_item": 5.35, "items": items,
           "outro": {"seconds": 5, "headline": "Disagree with this order?", "highlight": "Rank your own favourites",
                     "icon": os.path.join(HERE, "brand", "vinylduel-icon.png"), "brand": "VinylDuel",
                     "tagline": "Rank any album or playlist, song by song", "url": "vinylduel.app"}}
    cp = os.path.join(d, "config.json"); json.dump(cfg, open(cp, "w"), indent=2, ensure_ascii=False)
    subprocess.run([sys.executable, os.path.join(HERE, "make_countdown.py"), cp, os.path.join(HERE, f"list_{key}.mp4")], check=True)


if __name__ == "__main__":
    main()
