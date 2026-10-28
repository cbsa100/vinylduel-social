#!/usr/bin/env python3
"""
Top-10 countdown Short generator (9:16, 1080x1920, H.264/AAC).

Usage:  python3 make_countdown.py config.json out.mp4
Needs:  Python 3, ffmpeg + ffprobe on PATH, `pip install pillow numpy`

config.json (paths are relative to the json file):
{
  "title": "10 Songs That Defined",
  "highlight": "Alice in Chains",        # the yellow line
  "seconds_per_item": 6,
  "darken": 0.0,                         # optional 0..1 extra dimming of the footage
  "items": [                             # play order: #10 first, #1 last
    {"name": "Check My Brain",
     "clip": "clips/check-my-brain.mp4", # any video; cropped to fill 9:16, uses its audio
     "start": 51.3},                     # optional; omit -> loudest stretch of the song
    ...                                  # optional per item: "audio" + "audio_start"
  ],
  "outro": {                             # optional end card; last song keeps playing under it
    "seconds": 5,
    "headline": "Disagree with this order?",
    "highlight": "Rank Alice in Chains yourself",
    "icon": "brand/vinylduel-icon.png",
    "brand": "VinylDuel",
    "tagline": "Rank any album or playlist, song by song",
    "url": "vinylduel.app"
  }
}
Items without a clip get a placeholder animated background (handy for quick previews).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features as _pil_features

HERE = os.path.dirname(os.path.abspath(__file__))
HAS_RAQM = _pil_features.check("raqm")   # needed for tabular digits; falls back gracefully

W, H, FPS = 1080, 1920, 30
FONT_DIR = os.path.join(HERE, "fonts")
TITLE_FONT = os.path.join(FONT_DIR, "Inter-ExtraBold.otf")
LIST_FONT = os.path.join(FONT_DIR, "Inter-Bold.otf")
YELLOW = (255, 238, 0, 255)
WHITE = (255, 255, 255, 255)

# layout (measured from the reference video, scaled 720 -> 1080)
TITLE_Y, HIGHLIGHT_Y = 255, 375
LIST_TOP, ROW_H = 552, 91
NUM_RIGHT = 160            # x where the "N." dots line up
TEXT_X = 178
MAX_TEXT_W = W - TEXT_X - 50

PLACEHOLDER_PALETTES = [
    ("0x3a0d06", "0xc2541b"), ("0x062a2e", "0x2fa39a"), ("0x1a0630", "0x7b3fd1"),
    ("0x2b1a08", "0xd19b3f"), ("0x0b0b0b", "0x6b6b6b"), ("0x2e0616", "0xd13f72"),
    ("0x081a33", "0x3f7bd1"), ("0x1f2608", "0x9bb52f"), ("0x261008", "0xe07a2f"),
    ("0x2a1f05", "0xf2c14e"),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(" ".join(cmd) + "\n" + r.stderr[-3000:])
        raise SystemExit(1)
    return r.stdout


def styled_text(layer, xy, text, font, fill, anchor, stroke=6, shadow=(5, 6), features=None):
    """Bold text with black outline + soft drop shadow, like the reference."""
    if not HAS_RAQM:
        features = None
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + shadow[0], xy[1] + shadow[1]), text, font=font,
                            fill=(0, 0, 0, 200), anchor=anchor, features=features,
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    layer.alpha_composite(sh)
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=fill, anchor=anchor,
                               features=features,
                               stroke_width=stroke, stroke_fill=(0, 0, 0, 255))


def fit_font(path, size, text, max_w):
    while size > 30:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(path, size)


def header_layer(cfg):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    styled_text(img, (W // 2, TITLE_Y), cfg["title"],
                fit_font(TITLE_FONT, 84, cfg["title"], W - 100), WHITE, "mm", stroke=6)
    styled_text(img, (W // 2, HIGHLIGHT_Y), cfg["highlight"],
                fit_font(TITLE_FONT, 84, cfg["highlight"], W - 100), YELLOW, "mm", stroke=6)
    return img


def row_layer(rank, row, name, artist=None):
    """One list row. name=None -> number only (empty slot). artist: shown smaller and dimmer after the song
    (multi-artist lists); it shrinks first, then gets trimmed, so the song name stays big."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = LIST_TOP + row * ROW_H
    nf = ImageFont.truetype(LIST_FONT, 62)
    styled_text(img, (NUM_RIGHT, y), f"{rank}.", nf, WHITE, "rm", stroke=5, shadow=(4, 5),
                features=["tnum"])
    if name and artist:
        gap = 18
        sf = fit_font(LIST_FONT, 58, name, MAX_TEXT_W * 0.72)
        song_w = sf.getlength(name)
        if song_w > MAX_TEXT_W * 0.72:        # very long song title: trim it
            while sf.getlength(name + "…") > MAX_TEXT_W * 0.72 and len(name) > 4:
                name = name[:-1]
            name = name.rstrip() + "…"; song_w = sf.getlength(name)
        room = MAX_TEXT_W - song_w - gap
        af = fit_font(LIST_FONT, 40, artist, room)
        if af.getlength(artist) > room:
            af = ImageFont.truetype(LIST_FONT, 32)
            while af.getlength(artist + "…") > room and len(artist) > 3:
                artist = artist[:-1]
            artist = artist.rstrip() + "…"
        styled_text(img, (TEXT_X, y), name, sf, WHITE, "lm", stroke=5, shadow=(4, 5))
        styled_text(img, (TEXT_X + song_w + gap, y + 4), artist, af, (255, 255, 255, 200), "lm", stroke=4, shadow=(3, 4))
    elif name:
        tf = fit_font(LIST_FONT, 62, name, MAX_TEXT_W)
        if tf.size < 46:                      # too long: keep it readable, trim instead
            tf = ImageFont.truetype(LIST_FONT, 46)
            while tf.getlength(name + "…") > MAX_TEXT_W and len(name) > 4:
                name = name[:-1]
            name = name.rstrip() + "…"
        styled_text(img, (TEXT_X, y), name, tf, WHITE, "lm", stroke=5, shadow=(4, 5))
    return img


def build_overlays(cfg, tmp):
    n = len(cfg["items"])
    header = header_layer(cfg)
    empties = [row_layer(n - i, i, None) for i in range(n)]
    fulls = [row_layer(n - i, i, cfg["items"][i]["name"], cfg["items"][i].get("artist")) for i in range(n)]
    paths = []
    for seg in range(n):
        base = header.copy()
        for i in range(n):
            if i < seg:
                base.alpha_composite(fulls[i])
            elif i > seg:
                base.alpha_composite(empties[i])
            else:
                base.alpha_composite(empties[i])  # number shows under the fade-in
        newrow = fulls[seg]
        bp, npth = os.path.join(tmp, f"base{seg}.png"), os.path.join(tmp, f"new{seg}.png")
        base.save(bp)
        newrow.save(npth)
        paths.append((bp, npth))
    return paths


def bars_crop(path, start, T):
    """Crop for black bars burned into the video (letterbox/pillarbox), or None."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-ss", str(start), "-t", str(T), "-i", path,
                        "-vf", "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"],
                       capture_output=True, text=True)
    found = [l.split("crop=")[-1].strip() for l in r.stderr.splitlines() if "crop=" in l]
    if not found:
        return None
    w, h, x, y = (int(v) for v in found[-1].split(":"))
    sw, sh = (int(v) for v in run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", path]).strip().split(","))
    if w < sw * 0.4 or h < sh * 0.4 or (w >= sw - 8 and h >= sh - 8):
        return None                      # nothing to remove, or a mostly black scene
    return f"{w}:{h}:{x}:{y}"


def has_audio(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
               "stream=index", "-of", "csv=p=0", path])
    return bool(out.strip())


def outro_layer(o):
    """End card: hook line, app icon, name, tagline and URL pill."""
    bdir = o.get("brand_dir", os.path.join(HERE, "brand"))
    gf = lambda w: (os.path.join(bdir, f"Geist-{w}.ttf") if os.path.exists(os.path.join(bdir, f"Geist-{w}.ttf"))
                    else LIST_FONT)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # hook, in the same style as the countdown title
    y = 470
    if o.get("headline"):
        styled_text(img, (W // 2, y), o["headline"], fit_font(TITLE_FONT, 72, o["headline"], W - 120),
                    WHITE, "mm", stroke=6)
        y += 100
    if o.get("highlight"):
        styled_text(img, (W // 2, y), o["highlight"], fit_font(TITLE_FONT, 72, o["highlight"], W - 120),
                    YELLOW, "mm", stroke=6)
    # icon with a soft purple glow
    size, cy = 300, 880
    if o.get("icon"):
        icon = Image.open(o["icon"]).convert("RGBA").resize((size, size), Image.LANCZOS)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gl = Image.new("RGBA", (size, size), (110, 90, 255, 0))
        gl.putalpha(icon.getchannel("A").point(lambda a: int(a * 0.85)))
        glow.paste(gl, (W // 2 - size // 2, cy - size // 2 + 10))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(38)))
        img.alpha_composite(icon, (W // 2 - size // 2, cy - size // 2))
    # name + tagline
    ny = cy + size // 2 + 95
    styled_text(img, (W // 2, ny), o.get("brand", ""), ImageFont.truetype(gf("Black"), 112),
                WHITE, "mm", stroke=0, shadow=(0, 6))
    if o.get("tagline"):
        styled_text(img, (W // 2, ny + 92), o["tagline"],
                    fit_font(gf("Medium"), 44, o["tagline"], W - 140),
                    (232, 228, 255, 255), "mm", stroke=0, shadow=(0, 3))
    # URL pill in the brand gradient
    if o.get("url"):
        f = ImageFont.truetype(gf("Bold"), 62)
        tw = int(f.getlength(o["url"]))
        pw, ph = tw + 140, 124
        px, py = W // 2 - pw // 2, ny + 200
        c0, c1 = o.get("colors", ["#8f7dff", "#4a35e8"])
        c0 = tuple(int(c0[i:i + 2], 16) for i in (1, 3, 5)); c1 = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
        grad = Image.new("RGBA", (pw, ph))
        gd = ImageDraw.Draw(grad)
        for x in range(pw):
            t = x / max(1, pw - 1)
            gd.line([(x, 0), (x, ph)], fill=tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(3)) + (255,))
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2, fill=255)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([px, py + 10, px + pw, py + ph + 10], radius=ph // 2,
                                             fill=(20, 10, 60, 170))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
        img.paste(grad, (px, py), mask)
        ImageDraw.Draw(img).text((W // 2, py + ph // 2), o["url"], font=f, fill=WHITE, anchor="mm")
    return img


def render_segment(cfg, idx, overlays, out):
    item = cfg["items"][idx]
    D = float(cfg.get("seconds_per_item", 6))
    darken = float(cfg.get("darken", 0))
    outro = cfg.get("outro") if idx == len(cfg["items"]) - 1 else None
    O = float(outro.get("seconds", 5)) if outro else 0.0
    T = D + O                                   # last song keeps playing under the end card
    base_png, new_png = overlays
    cmd = ["ffmpeg", "-y", "-v", "error"]

    clip = item.get("clip")
    if clip:
        cmd += ["-ss", str(item.get("start", 0)), "-t", str(T), "-i", clip]
        bars = bars_crop(clip, item.get("start", 0), T)
        bg = ((f"[0:v]crop={bars}," if bars else "[0:v]") + f"scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},setsar=1,fps={FPS}")
    else:
        c0, c1 = PLACEHOLDER_PALETTES[idx % len(PLACEHOLDER_PALETTES)]
        cmd += ["-f", "lavfi", "-t", str(T), "-i",
                f"gradients=s={W // 4}x{H // 4}:c0={c0}:c1={c1}:c2={c0}:n=3:speed=0.015:r={FPS}:seed={idx * 7 + 3}"]
        bg = (f"[0:v]format=yuv420p,noise=alls=14:allf=t+u,"
              f"scale={W}:{H}:flags=bicubic,vignette=PI/4,setsar=1")
    if darken > 0:
        bg += f",eq=brightness={-darken * 0.3}"

    cmd += ["-loop", "1", "-t", str(T), "-i", base_png,
            "-loop", "1", "-t", str(T), "-i", new_png]
    n_in = 3
    if outro:
        cmd += ["-loop", "1", "-t", str(T), "-i", outro["_png"]]
        n_in = 4

    # audio source
    a_idx = None
    if item.get("audio"):
        cmd += ["-ss", str(item.get("audio_start", 0)), "-t", str(T), "-i", item["audio"]]
        a_idx = n_in
    elif clip and has_audio(clip):
        a_idx = 0
    if a_idx is None:
        cmd += ["-f", "lavfi", "-t", str(T), "-i", "anullsrc=r=44100:cl=stereo"]
        a_idx = n_in
    # optional spoken title over the first song: the music dips while the voice talks
    voice = cfg.get("_voice_file") if idx == 0 else None
    if voice:
        cmd += ["-i", voice]
        v_idx = len([c for c in cmd if c == "-i"]) - 1

    if outro:
        fc = (f"{bg},split[bgA][bgB];"
              f"[bgB]boxblur=26:2,eq=brightness=-0.16:saturation=0.75,format=yuva420p,"
              f"fade=in:st={D}:d=0.6:alpha=1[blur];[bgA][blur]overlay=0:0,format=yuva420p[bg];"
              f"[1:v]format=rgba,fade=out:st={D - 0.05}:d=0.4:alpha=1[l1];"
              f"[2:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1,fade=out:st={D - 0.05}:d=0.4:alpha=1[nr];"
              f"[3:v]format=rgba,fade=in:st={D + 0.15}:d=0.55:alpha=1[oc];"
              f"[bg][l1]overlay=0:0[b1];[b1][nr]overlay=0:0[b2];"
              f"[b2][oc]overlay=x=0:y='if(lt(t,{D + 0.15}),46,max(0,46-46*(t-{D + 0.15})/0.55))':eval=frame,"
              f"format=yuv420p[v];")
        afade_out = f"afade=out:st={T - 1.6}:d=1.6"
    else:
        fc = (f"{bg},format=yuva420p[bg];[2:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[nr];"
              f"[bg][1:v]overlay=0:0[b1];[b1][nr]overlay=0:0,format=yuv420p[v];")
        afade_out = f"afade=out:st={D - 0.2}:d=0.2"
    fc += (f"[{a_idx}:a]aformat=channel_layouts=stereo,"
           f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,"   # even out song volumes
           f"afade=in:st=0:d=0.12,{afade_out},apad" + ("[m0];" if voice else "[a]"))
    if voice:
        vlen = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice]).strip())
        duck = vlen + 0.6
        fc += (f"[m0]volume='if(lt(t,{duck:.2f}),0.22,if(lt(t,{duck + 0.6:.2f}),0.22+0.78*(t-{duck:.2f})/0.6,1))':eval=frame[m1];"
               f"[{v_idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=300|300,volume=1.8,apad[vo];"
               f"[m1][vo]amix=inputs=2:duration=first:normalize=0[a]")
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(T),
            "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-maxrate", "8M", "-bufsize", "16M",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", out]
    run(cmd)


def loudest_window(path, D, skip_frac=0.12):
    """Start time (s) of the loudest D-second stretch (usually the chorus)."""
    sr, hop = 8000, 0.25
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True).stdout
    import numpy as np
    x = np.frombuffer(raw, np.int16).astype(np.float32)
    n = int(sr * hop)
    if len(x) < n * 4:
        return 0.0
    rms = np.sqrt((x[: len(x) // n * n].reshape(-1, n) ** 2).mean(axis=1))
    win = max(1, int(D / hop))
    if len(rms) <= win:
        return 0.0
    sums = np.convolve(rms, np.ones(win), "valid")
    lo = int(len(rms) * skip_frac)                     # skip intros
    hi = max(lo + 1, len(sums) - int(len(rms) * 0.05)) # and fade-outs
    best = lo + int(np.argmax(sums[lo:hi]))
    return round(best * hop, 2)


def main():
    cfg_path, out = sys.argv[1], sys.argv[2]
    with open(cfg_path) as f:
        cfg = json.load(f)
    base_dir = os.path.dirname(os.path.abspath(cfg_path))
    D = float(cfg.get("seconds_per_item", 6))
    for it in cfg["items"]:
        for k in ("clip", "audio"):
            if it.get(k) and not os.path.isabs(it[k]):
                it[k] = os.path.join(base_dir, it[k])
        # no start given -> jump to the loudest part (the chorus, most of the time)
        if it.get("audio") and "audio_start" not in it:
            it["audio_start"] = loudest_window(it["audio"], D)
        if it.get("clip") and "start" not in it:
            if it.get("audio"):
                it["start"] = it["audio_start"]
            elif has_audio(it["clip"]):
                it["start"] = loudest_window(it["clip"], D)
            print(f"{it['name']}: using {it.get('start', 0)}s", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        overlays = build_overlays(cfg, tmp)
        if cfg.get("voice"):                    # {"text": ..., "name": "Samantha"}: macOS `say`
            aiff = os.path.join(tmp, "voice.aiff")
            subprocess.run(["say", "-v", cfg["voice"].get("name", "Samantha"), "-r", "175", "-o", aiff,
                            cfg["voice"]["text"]], check=True)
            cfg["_voice_file"] = aiff
        if cfg.get("outro"):
            o = cfg["outro"]
            if o.get("icon") and not os.path.isabs(o["icon"]):
                o["icon"] = os.path.join(base_dir, o["icon"])
            o["_png"] = os.path.join(tmp, "outro.png")
            outro_layer(o).save(o["_png"])
        segs = []
        for i in range(len(cfg["items"])):
            p = os.path.join(tmp, f"seg{i:02d}.mp4")
            render_segment(cfg, i, overlays[i], p)
            segs.append(p)
            print(f"segment {i + 1}/{len(segs) if False else len(cfg['items'])} done", flush=True)
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{s}'\n" for s in segs)
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", "-movflags", "+faststart", out])
    print("wrote", out)


if __name__ == "__main__":
    main()
