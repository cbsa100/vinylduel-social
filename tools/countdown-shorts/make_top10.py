#!/usr/bin/env python3
"""
One command, artist in -> countdown Short out.

    python3 make_top10.py "Drake"                      # picks the 10 most-watched official videos
    python3 make_top10.py "The Beatles" --songs "Help!" "Let It Be" ...   # your own list, #10 first
    python3 make_top10.py "Drake" --out ~/Desktop/drake.mp4 --title "10 Songs That Defined"

Needs: everything make_countdown.py needs, plus yt-dlp (`brew install yt-dlp`).
Videos are cached in clips/<artist>/ next to this script, so a re-run doesn't download again.
How it picks videos: it searches YouTube for "<artist> <song> official music video" and prefers
uploads from the artist's own channel (or their VEVO); audio-only "art track" uploads are skipped,
because a still cover image makes a dull Short.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def ytdlp(*args):
    r = subprocess.run(["yt-dlp", "--no-warnings", *args], capture_output=True, text=True)
    return r.stdout


def search(query, n):
    """Up to n results as dicts (id, title, channel, duration, views), without downloading."""
    out = ytdlp("--skip-download", "--flat-playlist", "--print",
                "%(id)s\t%(title)s\t%(channel)s\t%(duration)s\t%(view_count)s", f"ytsearch{n}:{query}")
    rows = []
    for line in out.splitlines():
        p = line.split("\t")
        if len(p) == 5:
            rows.append({"id": p[0], "title": p[1], "channel": p[2],
                         "duration": float(p[3]) if p[3] not in ("NA", "None", "") else 0,
                         "views": int(p[4]) if p[4].isdigit() else 0})
    return rows


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def is_artist_channel(channel, artist, title=""):
    """The artist's own channel (incl. "Official X", "XVEVO", "EminemMusic"), or a label upload
    titled "<artist> - ... (Official Video)"."""
    c, a = norm(channel), norm(artist)
    core = a[3:] if a.startswith("the") and len(a) > 6 else a
    if core and core in c:
        return True
    t = title.lower()
    return norm(title).startswith(a) and ("official video" in t or "official music video" in t)


def looks_like_video(r):
    t = r["title"].lower()
    bad = ("lyric", "audio", "visualizer", "visualiser", "live", "reaction", "cover", "karaoke",
           "instrumental", "8d", "slowed", "nsfw", "behind the scenes", "teaser", "trailer")
    return 90 <= r["duration"] <= 600 and not any(b in t for b in bad)


def song_name(title, artist):
    """'Drake, Kanye West - Forever (Official Music Video) ft. X' -> 'Forever'."""
    parts = [p.strip() for p in re.split(r"\s[-–—|]\s", title)]
    while len(parts) > 1 and norm(artist) in norm(parts[0]):
        parts.pop(0)                                  # "<artist>, guests - " prefix
    while len(parts) > 1 and norm(artist) in norm(parts[-1]):
        parts.pop()                                   # " - <artist>" suffix
    t = " - ".join(parts)
    t = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", t)      # every (...) and [...]
    t = re.split(r"\s(?:ft\.?|feat\.?|featuring)\s", t, flags=re.I)[0]
    return t.strip(" -–—|:\"'").strip()


def best_video(artist, song):
    rows = [r for r in search(f"{artist} {song} official music video", 8) if looks_like_video(r)]
    wanted = norm(song)
    rows = [r for r in rows if wanted[:12] in norm(r["title"])] or rows
    own = [r for r in rows if is_artist_channel(r["channel"], artist, r["title"])]
    return (own or rows or [None])[0]


def top_videos(artist, k=10):
    """The artist's k most-watched official music videos, one per song, least-watched first."""
    seen, picked = set(), []
    for q in (f"{artist} official music video", f"{artist} official video", f"{artist} music video"):
        for r in search(q, 40):
            if not (is_artist_channel(r["channel"], artist, r["title"]) and looks_like_video(r)):
                continue
            name = song_name(r["title"], artist)
            if not name or norm(name) in seen:
                continue
            seen.add(norm(name)); picked.append(dict(r, song=name))
    picked.sort(key=lambda r: r["views"], reverse=True)
    return list(reversed(picked[:k]))       # countdown plays #10 first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artist")
    ap.add_argument("--songs", nargs="+", help="your own 10 songs, #10 first")
    ap.add_argument("--title", default="10 Songs That Defined")
    ap.add_argument("--out")
    a = ap.parse_args()

    slug = norm(a.artist) or "artist"
    clipdir = os.path.join(HERE, "clips", slug)
    os.makedirs(clipdir, exist_ok=True)

    if a.songs:
        vids = []
        for s in a.songs:
            r = best_video(a.artist, s)
            if not r:
                sys.exit(f"No video found for {s!r}")
            vids.append(dict(r, song=s))
    else:
        vids = top_videos(a.artist)
    if len(vids) < 3:
        sys.exit("Found too few official videos; pass --songs to choose them.")

    items = []
    for i, r in enumerate(vids):
        path = os.path.join(clipdir, r["id"] + ".mp4")
        print(f"#{len(vids) - i}: {r['song']}  <- {r['title']} ({r['channel']})", flush=True)
        if not os.path.exists(path):
            subprocess.run(["yt-dlp", "--no-warnings", "-q", "-f",
                            "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                            "--merge-output-format", "mp4", "--sleep-requests", "1.5",
                            "--sleep-interval", "15", "--max-sleep-interval", "40",   # go easy on YouTube
                            "-o", path, "https://www.youtube.com/watch?v=" + r["id"]], check=True)
        items.append({"name": r["song"], "clip": path})

    # 5.35 s a song = 58.5 s in all: YouTube blocks Shorts over 60 s that use claimed music
    cfg = {"title": a.title, "highlight": a.artist, "seconds_per_item": 5.35, "items": items,
           "outro": {"seconds": 5, "headline": "Disagree with this order?",
                     "highlight": f"Rank {a.artist} yourself",
                     "icon": os.path.join(HERE, "brand", "vinylduel-icon.png"), "brand": "VinylDuel",
                     "tagline": "Rank any album or playlist, song by song", "url": "vinylduel.app"}}
    cfg_path = os.path.join(clipdir, "config.json")
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    out = a.out or os.path.join(HERE, f"{slug}_top10_vinylduel.mp4")
    subprocess.run([sys.executable, os.path.join(HERE, "make_countdown.py"), cfg_path, out], check=True)


if __name__ == "__main__":
    main()
