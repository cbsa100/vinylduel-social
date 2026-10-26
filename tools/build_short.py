#!/usr/bin/env python3
"""
Builds a 9:16 Short/Reel/TikTok video (1080x1920, 30 fps, silent H.264) from a post's TikTok slides,
with the fixes from the YouTube retention review (2026-10-27):

  * verdict card: rankings, tier lists and receipts open on one big line with the verdict
    ("Shy Away isn't even S tier"), not on "X: The Tier List".
  * fact card: stories and reviews show the title slide, then one big line with the most surprising fact.
  * beats: slides with a paragraph are shown a couple of lines at a time; the other lines fade into the
    background, so there's never a wall of small text.
  * pick one: after each "A or B?" slide, the same slide again with the community's pick.
  * at most 58 s, so music added in the YouTube app can't trip the 60 s copyright block.

Usage:  python3 build_short.py <video id> <slides dir> <ocr json> <hooks.json> <out.mp4> [community.json]
The ocr json is one ocr_lines.swift record per slide ({"path","w","h","lines":[{"t","x","y","w","h"}]}).
Needs ffmpeg, Pillow.
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, FADE, MAX_TOTAL = 1080, 1920, 30, 0.3, 58.0
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "countdown-shorts", "fonts", "Inter-ExtraBold.otf")
YELLOW, WHITE = (255, 238, 0, 255), (255, 255, 255, 255)
CHROME = re.compile(r"^(vinylduel|photo:|\d\d / \d\d|thank you|ranked by|album receipt|tracklist|in album order|"
                    r"free on iphone|google play|app store|rank .* yourself)", re.I)
norm = lambda s: re.sub(r"[^a-z0-9]+", "", s.lower())


def words(text): return len([w for w in re.split(r"\s+", text) if w])


def read_time(n, lo=2.2, hi=6.5): return round(min(hi, max(lo, 1.0 + max(0, n - 6) / 6)), 2)


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + ([cur] if cur else [])


def text_card(bg, text, label=None):
    """Big centred line over a blurred, darkened version of bg (the title slide)."""
    img = bg.convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(28))
    img = Image.blend(img, Image.new("RGB", (W, H), (8, 7, 15)), 0.55).convert("RGBA")
    d = ImageDraw.Draw(img)
    size = 104
    while size > 60:
        f = ImageFont.truetype(FONT, size)
        lines = wrap(d, text, f, W - 140)
        if len(lines) <= 5: break
        size -= 6
    lh = int(size * 1.18); top = int(H * 0.42 - lh * len(lines) / 2)
    if label:
        lf = ImageFont.truetype(FONT, 46)
        d.text((W // 2, top - 70), label, font=lf, fill=YELLOW, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, 255))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        sd.text((W // 2 + 5, top + i * lh + 6), ln, font=f, fill=(0, 0, 0, 190), anchor="mt", stroke_width=7, stroke_fill=(0, 0, 0, 190))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        d.text((W // 2, top + i * lh), ln, font=f, fill=WHITE, anchor="mt", stroke_width=7, stroke_fill=(0, 0, 0, 255))
    return img.convert("RGB"), words(text)


def body_lines(rec):
    """Paragraph lines: normal-size text (not headings, chrome or tiny credits), in reading order."""
    out = [l for l in rec["lines"] if 40 <= l["h"] <= 74 and l["w"] > 220 and not CHROME.match(l["t"])]
    if len(out) >= 3:                       # the heading is set larger than the paragraph: keep it bright
        hs = sorted(l["h"] for l in out); med = hs[len(hs) // 2]
        out = [l for l in out if l["h"] <= med * 1.15]
    return sorted(out, key=lambda l: (l["y"], l["x"]))


def bg_colour(img, box):
    """Colour just around a text line, to fade it into the background."""
    x, y, w, h = box
    px = []
    for (sx, sy) in ((x - 14, y + h // 2), (x + w + 14, y + h // 2), (x + w // 2, y - 10), (x + w // 2, y + h + 10)):
        if 0 <= sx < img.width and 0 <= sy < img.height:
            px.append(img.getpixel((sx, sy))[:3])
    if not px: return (0, 0, 0)
    return tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))


def beats(img, rec):
    """Split a paragraph slide into beats of 2 lines; lines outside the beat fade to 22%."""
    lines = body_lines(rec)
    if sum(words(l["t"]) for l in lines) < 25 or len(lines) < 4:   # only real walls of text
        return None
    groups, i = [], 0
    while i < len(lines):
        n = 3 if len(lines) - i == 3 else 2
        groups.append(lines[i:i + n]); i += n
    out = []
    for g in groups:
        frame = img.convert("RGBA")
        ov = Image.new("RGBA", frame.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for l in lines:
            if l in g: continue
            box = (l["x"] - 8, l["y"] - 8, l["w"] + 16, l["h"] + 16)
            od.rectangle([box[0], box[1], box[0] + box[2], box[1] + box[3]], fill=bg_colour(img, box) + (225,))
        frame.alpha_composite(ov)
        out.append((frame.convert("RGB"), max(1.6, round(0.6 + words(" ".join(l["t"] for l in g)) / 4.5, 2))))
    return out


def pair_of(rec):
    t = " ".join(l["t"] for l in sorted(rec["lines"], key=lambda l: (l["y"], l["x"])) if l["h"] >= 38 and not CHROME.match(l["t"]))
    m = re.search(r"(.+?)\s+or\s+(.+?)\?", t)
    return (m.group(1).strip(" •"), m.group(2).strip()) if m else None


def winner(pair, order):
    def pos(name):
        n = norm(name)
        for i, s in enumerate(order):
            k = norm(s)
            if len(k) >= 3 and (k in n or n in k or k.startswith(n[:14])): return i
        return None
    a, b = pos(pair[0]), pos(pair[1])
    if a is None or b is None: return None
    return re.sub(r"\s*[\(\[](feat|with)[^\)\]]*[\)\]]", "", order[min(a, b)]).strip()   # the clean name


def answer_card(img, name):
    frame = img.convert("RGBA"); d = ImageDraw.Draw(frame)
    f = ImageFont.truetype(FONT, 64); lf = ImageFont.truetype(FONT, 40)
    lines = wrap(d, name, f, W - 220)
    ph = 110 + 76 * len(lines); top = int(H * 0.30)   # over the photo, clear of the question
    d.rounded_rectangle([70, top, W - 70, top + ph], radius=40, fill=(20, 16, 40, 235))
    d.text((W // 2, top + 30), "THE COMMUNITY PICKED", font=lf, fill=YELLOW, anchor="mt")
    for i, ln in enumerate(lines):
        d.text((W // 2, top + 86 + i * 76), ln, font=f, fill=WHITE, anchor="mt")
    return frame.convert("RGB")


def build(vid, slides_dir, ocr, hooks, community=None):
    files = sorted(f for f in os.listdir(slides_dir) if re.match(r"\d\d\.jpg$", f))
    imgs = [Image.open(os.path.join(slides_dir, f)).convert("RGB").resize((W, H)) for f in files]
    recs = [ocr[f] for f in files]
    h = hooks.get(vid, {})
    cards = []
    for i, (img, rec) in enumerate(zip(imgs, recs)):
        n = words(" ".join(l["t"] for l in rec["lines"]))
        if i == 0 and h.get("verdict"):
            c, nw = text_card(img, h["verdict"]); cards.append((c, read_time(nw + 4, 2.4, 3.6)))
        first_or_last = i == 0 or i == len(imgs) - 1
        bt = None if first_or_last else beats(img, rec)
        if bt:
            heading_time = 1.2
            cards.append((bt[0][0], bt[0][1] + heading_time)); cards += bt[1:]
        else:
            lo, hi = (2.0, 3.0) if i == 0 and h.get("fact") else (2.2, 6.5)
            cards.append((img, read_time(n, lo, hi) if i else min(read_time(n, 2.2, 4.0), 3.0)))
        if i == 0 and h.get("fact"):
            c, nw = text_card(img, h["fact"]); cards.append((c, read_time(nw + 5, 2.6, 3.8)))
        if h.get("duel") and community and 0 < i < len(imgs) - 1:
            p = pair_of(rec)
            order = community.get(vid) if isinstance(community.get(vid), list) else None
            if p and order:
                wname = winner(p, order)
                if wname:
                    cards[-1] = (cards[-1][0], min(cards[-1][1], 2.6))
                    cards.append((answer_card(img, wname), 1.8))
    total = sum(d for _, d in cards) + FADE
    if total > MAX_TOTAL:
        k = (MAX_TOTAL - FADE) / (total - FADE)
        cards = [(c, max(1.3, round(d * k, 2))) for c, d in cards]
    return cards


def render(cards, out):
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for i, (img, d) in enumerate(cards):
            p = os.path.join(tmp, f"c{i:02d}.png"); img.save(p)
            cmd += ["-loop", "1", "-t", f"{d + FADE:.3f}", "-framerate", str(FPS), "-i", p]
        # Each card is shown for its duration; card i fades in over the last FADE s of card i-1, so the
        # transition offset is simply the sum of the durations before it.
        fc, t = [f"[{i}:v]format=yuv420p,setsar=1[v{i}]" for i in range(len(cards))], 0.0
        prev = "[v0]"
        for i in range(1, len(cards)):
            t += cards[i - 1][1]
            fc.append(f"{prev}[v{i}]xfade=transition=fade:duration={FADE}:offset={t:.3f}[x{i}]")
            prev = f"[x{i}]"
        cmd += ["-filter_complex", ";".join(fc), "-map", prev, "-r", str(FPS), "-c:v", "libx264", "-crf", "27",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr[-2000:])


if __name__ == "__main__":
    vid, slides_dir, ocr_path, hooks_path, out = sys.argv[1:6]
    community = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else None
    ocr = {os.path.basename(r["path"]): r for r in (json.loads(l) for l in open(ocr_path)) if r["path"].split("/")[-2] == vid}
    cards = build(vid, slides_dir, ocr, json.load(open(hooks_path)), community)
    render(cards, out)
    print(vid, len(cards), "cards", round(sum(d for _, d in cards) + FADE, 1), "s")
