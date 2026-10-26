# Tools behind the VinylDuel social posts

Kept here (not in /tmp) so they survive. Python 3 with Pillow + numpy, ffmpeg, yt-dlp (Homebrew).

- `build_short.py`: turns a post's TikTok slides into a Short/Reel/TikTok video with the retention fixes
  (verdict or fact card from `hooks.json`, paragraphs in beats, "Pick one" answers from `duel_answers.json`,
  58 s cap). `render_v3.sh <ids.json> <ocr.jsonl>` renders many, 4 at a time, to `video/<id>-v3.mp4`.
- `ocr_lines.swift`: macOS text recognition with line positions (needed by build_short.py).
  Build with `swiftc -O ocr_lines.swift -o ocr_lines`; run on slide JPGs, one JSON line per slide.
- `community.py`: an album's community song order from the public VinylDuel API.
- `countdown-shorts/`: the "The 10 Best Songs by X" generator. `make_top10.py "Artist"` finds, downloads
  and renders (58.5 s: YouTube blocks Shorts over 60 s that use claimed music).
- `add_countdowns.py`, `add_pack_to_backlog.py`, `two_a_day.py`: put posts into `backlog.json` with times.
