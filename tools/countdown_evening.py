# One-off (31 Oct 2026), replaces the midday slot of countdown_twice_a_day.py: the second countdown of each day goes
# out in the evening (about 20:30-21:30 Israel = US afternoon + European evening) instead of at midday, starting
# tonight. Michael Jackson .. Lana Del Rey take the evening slots of 31 Oct .. 7 Nov (Reel, TikTok 20 min later,
# Short 20 min after that); every countdown after Lana Del Rey moves one more day earlier so there is no gap.
import json, datetime as dt, collections
TZ = dt.timezone(dt.timedelta(hours=2))
EVENING = [(20, 47), (20, 33), (21, 8), (20, 41), (21, 14), (20, 52), (21, 3), (20, 38)]  # uneven minutes
SLUGS = ['michaeljackson', 'rihanna', 'nirvana', 'arianagrande', 'metallica', 'coldplay', 'brunomars', 'lanadelrey']
order = {'yt-reel': 0, 'yt-ttv': 1, 'yt': 2}
b = json.load(open('backlog.json'))
later = collections.OrderedDict()
for i in b['items']:
    if '-cd-' not in i['id'] or i['scheduled']:
        continue
    kind, slug = i['id'].split('-cd-')
    if slug in SLUGS:
        n = SLUGS.index(slug)
        h, m = EVENING[n]
        t = dt.datetime(2026, 10, 31, h, m, tzinfo=TZ) + dt.timedelta(days=n, minutes=20 * order[kind])
        i['post']['dueAt'] = t.isoformat()
    elif i['post']['dueAt'] >= '2026-11-09':
        i['post']['dueAt'] = (dt.datetime.fromisoformat(i['post']['dueAt']) - dt.timedelta(days=1)).isoformat()
json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
