# Adds every Post Pack post that hasn't gone out (and isn't in the backlog) to backlog.json,
# 2 a day per channel after each channel's last planned post. Run from the scratchpad.
import json, random, datetime as dt
from zoneinfo import ZoneInfo
TZ = ZoneInfo('Asia/Jerusalem'); BASE = 'https://cbsa100.github.io/vinylduel-social/'
IG, TT, YT = '6adb5ec6778b240e2f9d4ea5', '6adb5f07778b240e2f9d51b0', '6adb5f1d778b240e2f9d52af'
B = 'social/backlog.json'; b = json.load(open(B)); pk = json.load(open('social/pack.json'))
have = {i['id'] for i in b['items']} | set(pk['posted'])
def interleave(posts):  # alternate VinylDuel posts and music stories, keeping pack order inside each
    a = [p for p in posts if p['section'] == 'main']; s = [p for p in posts if p['section'] != 'main']; out = []
    while a or s:
        if a: out.append(a.pop(0))
        if s: out.append(s.pop(0))
    return out
def slides(p): return [{'image': {'url': BASE + u, 'metadata': {'altText': 'VinylDuel slide'}}} for u in p['slides']]
new = {IG: [], TT: [], YT: []}
for p in interleave([p for p in pk['posts'] if p['platform'] == 'Instagram' and p['id'] not in have]):
    new[IG].append((p['id'], {'text': p['caption'], 'assets': slides(p), 'metadata': {'instagram': {'type': 'post', 'shouldShareToFeed': True}}}))
for p in interleave([p for p in pk['posts'] if p['platform'] == 'TikTok' and p['id'] not in have]):
    new[TT].append((p['id'], {'text': p['caption'], 'assets': slides(p), 'metadata': {'tiktok': {'title': (p.get('ttTitle') or p['hook'])[:90]}}}))
for p in interleave([p for p in pk['posts'] if p.get('ytTitle') and 'yt-' + p['id'] not in have]):
    new[YT].append(('yt-' + p['id'], {'text': p.get('ytDesc') or p['caption'], 'assets': [{'video': {'url': f"{BASE}video/{p['id']}-v2.mp4"}}],
        'metadata': {'youtube': {'title': p['ytTitle'].rstrip('.')[:100], 'categoryId': '10', 'privacy': 'public', 'madeForKids': False}}}))
# The new videos also go to TikTok (video) and Instagram (Reel). A post's video uses the same slides as its
# slideshow, so the video queue starts halfway through: the two versions of one post land weeks apart.
import re
vid_ids = [x['post'] for x in json.load(open('sched/plan_v3.json'))]
byid = {p['id']: p for p in pk['posts']}
def with_cta(text, tag):
    lines = text.rstrip().split('\n'); last = lines[-1]
    if last.startswith('#'):
        tags = [t for t in last.split() if t not in ('#shorts', '#fyp')] + [tag]
        body = '\n'.join(lines[:-1]).rstrip()
    else:
        tags, body = [tag], text.rstrip()
    if 'vinylduel app' not in body.lower() and 'vinylduel.app' not in body.lower():
        body += '\n\nRank any album, two songs at a time, on the VinylDuel app: free on iPhone and Android, link in bio.'
    return body + '\n\n' + ' '.join(tags)
reels, ttv = [], []
for pid in vid_ids:
    p = byid[pid]; v = [{'video': {'url': f"{BASE}video/{pid}-v2.mp4"}}]
    if 'yt-reel-' + pid not in have:
        reels.append(('yt-reel-' + pid, {'text': with_cta(p['caption'], '#reels'), 'assets': v, 'metadata': {'instagram': {'type': 'reel', 'shouldShareToFeed': True}}}))
    if 'yt-ttv-' + pid not in have:
        ttv.append(('yt-ttv-' + pid, {'text': p['caption'], 'assets': v, 'metadata': {'tiktok': {'title': (p.get('ttTitle') or p['hook'])[:90]}}}))
half = lambda L: L[len(L) // 2:] + L[:len(L) // 2]
videos = {IG: half(reels), TT: half(ttv), YT: []}
rnd = random.Random(1025)
for ch, items in new.items():
    last = max(dt.datetime.fromisoformat(i['post']['dueAt']) for i in b['items'] if i['post']['channelId'] == ch)
    day = last.astimezone(TZ).date() + dt.timedelta(days=1)
    a, v = list(items), list(videos[ch]); k = 0; n = len(a) + len(v)
    while a or v:
        pick = []
        if ch == YT: pick = [a.pop(0) for _ in range(min(2, len(a)))]
        else:
            if a: pick.append(a.pop(0))
            if v: pick.append(v.pop(0))
            if len(pick) < 2 and (a or v): pick.append((a or v).pop(0))
            if k % 2: pick.reverse()
        slots = [rnd.randint(11 * 60, 14 * 60 + 30), rnd.randint(18 * 60, 21 * 60 + 45)]
        for (pid, body), m in zip(pick, slots):
            due = dt.datetime.combine(day, dt.time(m // 60, m % 60), TZ).isoformat()
            b['items'].append({'id': pid, 'scheduled': False, 'post': {'channelId': ch, 'schedulingType': 'notification', 'mode': 'customScheduled', 'dueAt': due, **body}})
        day += dt.timedelta(days=1); k += 1
    print({IG: 'IG', TT: 'TT', YT: 'YT'}[ch], n, 'added, last', day - dt.timedelta(days=1))
for i in b['items']:
    t = i['post']['text']; assert len(t) <= 2200, (i['id'], len(t))
json.dump(b, open(B, 'w'), indent=1, ensure_ascii=False)
print('backlog now', len(b['items']))
