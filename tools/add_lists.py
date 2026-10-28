# Adds the multi-artist countdowns ("The 10 Worst Songs of the 80s", ...) to the Post Pack and the schedule:
# one a day after the last countdown, same afternoon slots, publishing automatically.
# Their videos live on the repo's "media" branch (not the GitHub Pages site, which must stay under 1 GB) and
# are linked through raw.githubusercontent.com, which Buffer accepts.
# Run from the scratchpad after the videos are on the media branch as list-<key>.mp4.
import json, random, datetime as dt, sys
from zoneinfo import ZoneInfo
TZ = ZoneInfo('Asia/Jerusalem')
RAW = 'https://raw.githubusercontent.com/cbsa100/vinylduel-social/media/'
IG, TT, YT = '6adb5ec6778b240e2f9d4ea5', '6adb5f07778b240e2f9d51b0', '6adb5f1d778b240e2f9d52af'
ORDER = ["worst-80s", "changed-rock", "defined-90s", "most-annoying", "worst-2000s", "changed-pop", "defined-2010s",
         "worst-duets", "worst-90s", "changed-hiphop", "defined-80s", "cringiest", "worst-2010s", "one-hit-wonders",
         "defined-2000s", "great-artists-terrible-songs"]
ONLY = sys.argv[1:]

L = json.load(open('countdown/countdown-shorts/lists.json'))
pk = json.load(open('social/pack.json')); b = json.load(open('social/backlog.json'))
have = {i['id'] for i in b['items']}
on_branch = set(open('media_files.txt').read().split()) if __import__('os').path.exists('media_files.txt') else set()
cd_days = [dt.date.fromisoformat(i['post']['dueAt'][:10]) for i in b['items'] if '-cd-' in i['id']]
next_day = max(cd_days) + dt.timedelta(days=1)
rnd = random.Random(1612)
for key in ORDER:
    if ONLY and key not in ONLY: continue
    pid = f'cd-list-{key}'
    if f'yt-reel-{pid}' in have or f'list-{key}.mp4' not in on_branch: continue
    s = L[key]
    title = f"{s['title']} {s['highlight']}"                       # "The 10 Worst Songs of the 80s"
    rows = [[p.strip() for p in x.split('|')] for x in s['items']]   # #10 first
    ranked = '\n'.join(f"{10 - i}. {r[1]} ({r[2] if len(r) > 2 else r[0]})" for i, r in enumerate(rows))
    top = rows[-1]
    tags = s['tags']
    video = [{'video': {'url': f'{RAW}list-{key}.mp4'}}]
    ig_text = (f"{title} 🎧\n\n{ranked}\n\nDisagree with this order? Rank your own favourites on the VinylDuel app, "
               f"free on iPhone and Android. Link in bio.\n\nClips from the official music videos.\n\n{tags} #top10 #musicranking #reels")
    tt_text = f"{title.lower()}. {top[1].lower()} at #1. what would you put there? 👇\n\n{tags} #top10 #fyp"
    yt_title = title if title.startswith('Great Artists') else f"{title}, Ranked"
    yt_text = (f"{title}, from #10 to #1. what would you put at #1?\n\n{ranked}\n\n"
               f"Rank any album, two songs at a time: vinylduel.app (free on iPhone and Android)\n\n"
               f"Clips from the official music videos.\n\n{tags} #top10 #shorts")
    if not any(p['id'] == pid for p in pk['posts']):
        pk['posts'].append({'id': pid, 'platform': 'Video', 'section': 'countdown', 'hook': title, 'caption': ig_text,
                            'ttTitle': title, 'ytTitle': yt_title, 'ytDesc': yt_text, 'slides': [], 'video': video[0]['video']['url']})
    day = next_day; next_day += dt.timedelta(days=1)
    m = rnd.randint(15 * 60 + 30, 17 * 60)
    for k, (ch, iid, text, meta) in enumerate([
            (IG, 'yt-reel-' + pid, ig_text, {'instagram': {'type': 'reel', 'shouldShareToFeed': True}}),
            (TT, 'yt-ttv-' + pid, tt_text, {'tiktok': {'title': title}}),
            (YT, 'yt-' + pid, yt_text, {'youtube': {'title': yt_title, 'categoryId': '10', 'privacy': 'public', 'madeForKids': False}})]):
        mm = m + 20 * k
        due = dt.datetime.combine(day, dt.time(mm // 60, mm % 60), TZ).isoformat()
        b['items'].append({'id': iid, 'scheduled': False, 'post': {'channelId': ch, 'schedulingType': 'automatic',
                           'mode': 'customScheduled', 'dueAt': due, 'text': text, 'assets': video, 'metadata': meta}})
    print(day, title, '#1', top[1])
json.dump(pk, open('social/pack.json', 'w'), indent=1, ensure_ascii=False)
json.dump(b, open('social/backlog.json', 'w'), indent=1, ensure_ascii=False)
print('backlog', len(b['items']))
