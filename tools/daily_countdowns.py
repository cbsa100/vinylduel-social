# One-off: moves the not-yet-scheduled countdowns from every 2 days to one a day, from 28 Oct, same order and times.
import json, datetime as dt, collections
b = json.load(open('social/backlog.json'))
groups = collections.OrderedDict()
for i in sorted((i for i in b['items'] if '-cd-' in i['id'] and not i['scheduled']), key=lambda i: i['post']['dueAt']):
    groups.setdefault(i['id'].split('-cd-')[1], []).append(i)
day = dt.date(2026, 10, 28)
for slug, items in groups.items():
    for i in items:
        t = dt.datetime.fromisoformat(i['post']['dueAt'])
        i['post']['dueAt'] = t.replace(year=day.year, month=day.month, day=day.day).isoformat()
    print(day, slug); day += dt.timedelta(days=1)
json.dump(b, open('social/backlog.json', 'w'), indent=1, ensure_ascii=False)
