import json, datetime as dt
b = json.load(open('social/backlog.json'))
for i in b['items']:
    if '-cd-' in i['id'] and not i['scheduled']:
        t = dt.datetime.fromisoformat(i['post']['dueAt']) - dt.timedelta(days=1)
        i['post']['dueAt'] = t.isoformat()
json.dump(b, open('social/backlog.json', 'w'), indent=1, ensure_ascii=False)
for i in b['items']:
    if i['id'].endswith('cd-eminem'): print(json.dumps(i, ensure_ascii=False))
