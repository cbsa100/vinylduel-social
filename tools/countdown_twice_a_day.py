# One-off (31 Oct 2026): two countdowns a day from 1 to 7 Nov. The 7 countdowns after Queen (7 Nov) get a midday
# slot on 1..7 Nov (Reel, TikTok 20 min later, Short 20 min after that), and every countdown after them moves 7 days
# earlier (same order and times), so they carry on one a day from 8 Nov without a gap.
import json, datetime as dt, collections
TZ = dt.timezone(dt.timedelta(hours=2))
MIDDAY = [(12, 7), (12, 41), (12, 23), (12, 52), (12, 14), (12, 36), (12, 3)]  # uneven minutes
b = json.load(open('backlog.json'))
groups = collections.OrderedDict()
for i in sorted((i for i in b['items'] if '-cd-' in i['id'] and not i['scheduled']
                 and i['post']['dueAt'] >= '2026-11-08'), key=lambda i: i['post']['dueAt']):
    groups.setdefault(i['id'].split('-cd-')[1], []).append(i)
slugs = list(groups)
order = {'yt-reel': 0, 'yt-ttv': 1, 'yt': 2}
for n, slug in enumerate(slugs):
    for i in groups[slug]:
        if n < 7:
            h, m = MIDDAY[n]
            start = dt.datetime(2026, 11, 1 + n, h, m, tzinfo=TZ)
            t = start + dt.timedelta(minutes=20 * order[i['id'].split('-cd-')[0]])
        else:
            t = dt.datetime.fromisoformat(i['post']['dueAt']) - dt.timedelta(days=7)
        i['post']['dueAt'] = t.isoformat()
    print(groups[slug][0]['post']['dueAt'][:16], slug)
json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
