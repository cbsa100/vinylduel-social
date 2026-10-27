# Adds the "10 Best Songs" countdown videos to the Post Pack (pack.json) and the schedule (backlog.json):
# one countdown a day, posted to Instagram (Reel), TikTok and YouTube (Short) the same afternoon,
# on top of the regular 2 posts a day. They publish automatically (their audio is already in the video).
# Run from the scratchpad after the videos are in social/video/cd-<slug>.mp4.
import json, random, datetime as dt, re
from zoneinfo import ZoneInfo
TZ = ZoneInfo('Asia/Jerusalem'); BASE = 'https://cbsa100.github.io/vinylduel-social/'
IG, TT, YT = '6adb5ec6778b240e2f9d4ea5', '6adb5f07778b240e2f9d51b0', '6adb5f1d778b240e2f9d52af'
ORDER = ["Drake", "The Beatles", "Alice in Chains", "Taylor Swift", "Eminem", "Arctic Monkeys", "Lady Gaga", "Linkin Park", "The Weeknd",
         "Olivia Rodrigo", "Kendrick Lamar", "Queen", "Billie Eilish",
         "Michael Jackson", "Rihanna", "Nirvana", "Ariana Grande", "Metallica", "Coldplay", "Bruno Mars",
         "Lana Del Rey", "Red Hot Chili Peppers", "Green Day",
         "Beyoncé", "Ed Sheeran", "Dua Lipa", "Harry Styles", "Justin Bieber", "Post Malone", "SZA", "Travis Scott",
         "Imagine Dragons", "Paramore",
         "Soundgarden", "Pearl Jam", "System of a Down", "Foo Fighters", "Deftones", "The Smashing Pumpkins",
         "Rage Against the Machine", "Tool", "Stone Temple Pilots", "Radiohead"]
TAGS = {"Soundgarden": "#soundgarden #chriscornell #grunge", "Pearl Jam": "#pearljam #eddievedder #grunge",
        "System of a Down": "#systemofadown #soad #metal", "Foo Fighters": "#foofighters #davegrohl #rock",
        "Deftones": "#deftones #chinomoreno #alternative", "The Smashing Pumpkins": "#smashingpumpkins #billycorgan #90smusic",
        "Rage Against the Machine": "#rageagainstthemachine #ratm #rock", "Tool": "#tool #maynardjameskeenan #progmetal",
        "Stone Temple Pilots": "#stonetemplepilots #scottweiland #grunge", "Radiohead": "#radiohead #thomyorke #alternative",
        "Beyoncé": "#beyonce #beyhive #rnb", "Ed Sheeran": "#edsheeran #pop #sheerios",
        "Dua Lipa": "#dualipa #pop #dance", "Harry Styles": "#harrystyles #harries #pop", "Justin Bieber": "#justinbieber #beliebers #pop",
        "Post Malone": "#postmalone #posty #hiphop", "SZA": "#sza #rnb #sos", "Travis Scott": "#travisscott #utopia #rap",
        "Imagine Dragons": "#imaginedragons #rock #alternative", "Paramore": "#paramore #hayleywilliams #poppunk",
        "Michael Jackson": "#michaeljackson #mj #kingofpop", "Rihanna": "#rihanna #navy #pop",
        "Nirvana": "#nirvana #kurtcobain #grunge", "Ariana Grande": "#arianagrande #arianators #pop",
        "Metallica": "#metallica #metal #heavymetal", "Coldplay": "#coldplay #chrismartin #britpop",
        "Bruno Mars": "#brunomars #pop #funk", "Lana Del Rey": "#lanadelrey #lana #alternative",
        "Red Hot Chili Peppers": "#redhotchilipeppers #rhcp #rock", "Green Day": "#greenday #poppunk #punk",
        "Drake": "#drake #ovo #rap", "The Beatles": "#thebeatles #beatles #classicrock",
        "Alice in Chains": "#aliceinchains #grunge #90smusic", "Taylor Swift": "#taylorswift #swifties #pop", "Olivia Rodrigo": "#oliviarodrigo #guts #sour",
        "Linkin Park": "#linkinpark #numetal #rock", "Eminem": "#eminem #slimshady #rap",
        "Kendrick Lamar": "#kendricklamar #hiphop #rap", "Arctic Monkeys": "#arcticmonkeys #indierock #alexturner",
        "Billie Eilish": "#billieeilish #finneas #pop", "The Weeknd": "#theweeknd #xo #rnb",
        "Lady Gaga": "#ladygaga #littlemonsters #pop", "Queen": "#queen #freddiemercury #classicrock"}
START = dt.date(2026, 10, 27)
norm = lambda s: re.sub(r'[^a-z0-9]+', '', s.lower())

pk = json.load(open('social/pack.json')); b = json.load(open('social/backlog.json'))
have = {i['id'] for i in b['items']}
rnd = random.Random(2810)
import os, sys
ONLY = sys.argv[1:]          # optional: only these artists
cd_days = [dt.date.fromisoformat(i['post']['dueAt'][:10]) for i in b['items'] if '-cd-' in i['id']]
next_day = max([START] + [d + dt.timedelta(days=1) for d in cd_days])   # the day after the last countdown
for artist in ORDER:
    slug = norm(artist)
    if ONLY and artist not in ONLY: continue
    if not os.path.exists(f'social/video/cd-{slug}.mp4') or f'yt-reel-cd-{slug}' in have:
        continue                                                   # not rendered yet, or already in
    cfg = json.load(open(f'countdown/countdown-shorts/clips/{slug}/config.json'))
    songs = [it['name'] for it in cfg['items']]                 # #10 first
    ranked = '\n'.join(f'{10 - i}. {s}' for i, s in enumerate(songs))
    top, tags = songs[-1], TAGS[artist]
    pid = f'cd-{slug}'
    video = [{'video': {'url': f'{BASE}video/{pid}.mp4'}}]
    ig_text = (f"The 10 best songs by {artist}, ranked 🎧\n\n{ranked}\n\n"
               f"Disagree with this order? Rank {artist} yourself on the VinylDuel app, free on iPhone and Android. Link in bio.\n\n"
               f"Clips from the official music videos.\n\n{tags} #top10 #musicranking #reels")
    tt_text = (f"the 10 best songs by {artist.lower()}. {top.lower()} at #1, {songs[0].lower()} at #10. what's your #1? 👇\n\n"
               f"{tags} #top10 #musicranking #fyp")
    yt_title = f"The 10 Best Songs by {artist}, Ranked"
    poss = artist + ("'" if artist.endswith("s") else "'s")
    yt_text = (f"{poss} 10 best songs, from #10 to #1. what's your #1?\n\n{ranked}\n\n"
               f"Rank any album, two songs at a time: vinylduel.app (free on iPhone and Android)\n\n"
               f"Clips from the official music videos.\n\n{tags} #top10 #shorts")
    if not any(p['id'] == pid for p in pk['posts']):
        pk['posts'].append({'id': pid, 'platform': 'Video', 'section': 'countdown', 'hook': f'The 10 Best Songs by {artist}',
                            'caption': ig_text, 'ttTitle': f'The 10 best songs by {artist}', 'ytTitle': yt_title, 'ytDesc': yt_text,
                            'slides': [], 'video': f'video/{pid}.mp4'})
    day = next_day; next_day += dt.timedelta(days=1)
    m = rnd.randint(15 * 60 + 30, 17 * 60)                      # mid-afternoon, between the regular two slots
    for k, (ch, iid, text, meta) in enumerate([
            (IG, 'yt-reel-' + pid, ig_text, {'instagram': {'type': 'reel', 'shouldShareToFeed': True}}),
            (TT, 'yt-ttv-' + pid, tt_text, {'tiktok': {'title': f'The 10 best songs by {artist}'}}),
            (YT, 'yt-' + pid, yt_text, {'youtube': {'title': yt_title, 'categoryId': '10', 'privacy': 'public', 'madeForKids': False}})]):
        if iid in have: continue
        mm = m + 20 * k
        due = dt.datetime.combine(day, dt.time(mm // 60, mm % 60), TZ).isoformat()
        b['items'].append({'id': iid, 'scheduled': False, 'post': {'channelId': ch, 'schedulingType': 'automatic',
                           'mode': 'customScheduled', 'dueAt': due, 'text': text, 'assets': video, 'metadata': meta}})
    print(day, artist, '#1', top)
b['about'] = ("VinylDuel Buffer backlog. Each item is a Buffer create_post payload. 'scheduled': true once it is in Buffer. "
              "schedulingType is 'notification' (Buffer pings the phone so audio can be added) for every post except the "
              "'cd-' countdown videos, which are 'automatic' because they already have their audio.")
json.dump(pk, open('social/pack.json', 'w'), indent=1, ensure_ascii=False)
json.dump(b, open('social/backlog.json', 'w'), indent=1, ensure_ascii=False)
print('backlog', len(b['items']))
