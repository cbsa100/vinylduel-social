# One-off (31 Oct 2026): a countdown's Reel, TikTok and Short go out at the same minute (the earliest of the three),
# instead of 20 minutes apart, so all three land on the peak hour. Prints the ones already in Buffer that moved.
import json, collections
b = json.load(open('backlog.json'))
groups = collections.defaultdict(list)
for i in b['items']:
    if '-cd-' in i['id'] and i['post']['dueAt'] >= '2026-10-31T11':
        groups[i['id'].split('-cd-')[1]].append(i)
for items in groups.values():
    start = min(i['post']['dueAt'] for i in items)
    for i in items:
        if i['post']['dueAt'] != start:
            i['post']['dueAt'] = start
            if i['scheduled']:
                print(json.dumps({'postId': i['bufferId'], 'dueAt': start, 'id': i['id'], 'metadata': i['post']['metadata'],
                                  'video': i['post']['assets'][0]['video']['url']}, ensure_ascii=False))
json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
