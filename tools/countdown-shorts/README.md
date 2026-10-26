# Countdown Shorts generator

Makes a 9:16 "Top 10" countdown Short: a title, a yellow highlight line, and a numbered
list that fills in from #10 to #1 while each video plays for 6 seconds, with an optional
end screen (VinylDuel by default) while the last song keeps playing.

## Setup (Mac)
    brew install ffmpeg
    pip3 install pillow numpy

## Run
    python3 make_countdown.py examples/alice_in_chains.json out.mp4

`examples/alice_in_chains.json` points at the videos in ~/Desktop/test-vids.
`examples/preview_no_clips.json` renders with placeholder backgrounds (no videos needed).

## Making a new one
Copy a config, change `title`, `highlight`, the 10 `items` (name + clip path), and the
outro's `highlight` line. Leave out `start` and the script uses the loudest 6 seconds of
each song (usually the chorus). Clips can be any shape: wide videos are cropped to fill.

What it does automatically: 1080x1920 at 30fps, volume leveled across songs (-14 LUFS),
bitrate capped at 8 Mbps, about 2–3 minutes to render on a laptop.

## Fully automatic: artist in, Short out
    brew install yt-dlp
    python3 make_top10.py "Drake"                    # the artist's 10 most-watched official videos
    python3 make_top10.py "The Beatles" --songs "Help!" "Let It Be" ...   # or your own 10, #10 first

It searches YouTube for each song's official video (the artist's own channel or VEVO first,
skipping lyric, audio-only and live uploads), downloads it once into clips/<artist>/, writes
the config there and renders <artist>_top10_vinylduel.mp4 with the VinylDuel end card.
make_countdown.py now also crops black bars that are burned into a video, so widescreen
videos fill the screen.
