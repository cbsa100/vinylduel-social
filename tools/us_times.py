# One-off (31 Oct 2026): every post still to come is timed for a US audience (US Eastern time; written in
# Asia/Jerusalem as before, DST handled by zoneinfo).
# - Countdowns (automatic): 31 Oct..7 Nov two a day, US lunch (12:30-13:10 ET) and US evening (19:30-20:10 ET),
#   in the order they were already in; from 8 Nov one a day in the US evening slot.
# - Every other post (notification: published by hand from Israel): same day, morning posts at ET 2 h before their
#   old Israel clock time (about 9:00-12:30 ET = 16:00-19:30 Israel), evening posts at ET 5 h before (about
#   13:00-16:45 ET = 20:00-23:45 Israel). Order within a day stays the same.
# Prints the countdown groups that are already in Buffer, so their Buffer posts can be moved to the new times.
import json, datetime as dt, collections
from zoneinfo import ZoneInfo
ET, IL = ZoneInfo('America/New_York'), ZoneInfo('Asia/Jerusalem')
NOW = dt.datetime(2026, 10, 31, 11, 0, tzinfo=IL)
JITTER = [7, 23, 14, 31, 3, 38, 19, 27, 11, 35, 5, 29, 17, 40, 9, 25]
order = {'yt-reel': 0, 'yt-ttv': 1, 'yt': 2}
b = json.load(open('backlog.json'))
todo = [i for i in b['items'] if dt.datetime.fromisoformat(i['post']['dueAt']) >= NOW]

groups = collections.OrderedDict()
for i in sorted((i for i in todo if '-cd-' in i['id']), key=lambda i: i['post']['dueAt']):
    groups.setdefault(i['id'].split('-cd-')[1], []).append(i)
for n, (slug, items) in enumerate(groups.items()):
    if n < 16:
        day, evening = dt.date(2026, 10, 31) + dt.timedelta(days=n // 2), n % 2 == 1
    else:
        day, evening = dt.date(2026, 11, 8) + dt.timedelta(days=n - 16), True
    start = dt.datetime(day.year, day.month, day.day, 19 if evening else 12, 30, tzinfo=ET) \
        + dt.timedelta(minutes=JITTER[n % len(JITTER)])
    for i in items:
        t = start + dt.timedelta(minutes=20 * order[i['id'].split('-cd-')[0]])
        i['post']['dueAt'] = t.astimezone(IL).isoformat()
    if n < 16:
        print(start.astimezone(ET).strftime('%a %d %b %H:%M ET'), '=', start.astimezone(IL).strftime('%H:%M Israel'),
              slug, ['%s:%s' % (i['id'].split('-cd-')[0], i.get('bufferId', '?') if i['scheduled'] else '-') for i in items])

for i in todo:
    if '-cd-' in i['id']:
        continue
    old = dt.datetime.fromisoformat(i['post']['dueAt']).astimezone(IL)
    back = 2 if old.hour < 16 else 5
    t = dt.datetime(old.year, old.month, old.day, old.hour - back, old.minute, tzinfo=ET)
    i['post']['dueAt'] = t.astimezone(IL).isoformat()
json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
