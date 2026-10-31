# One-off (31 Oct 2026): countdowns only from now to 7 Nov. Every non-countdown post still to come moves 8 days
# later (same order, times and spacing), and the ones already in Buffer are marked unscheduled (they were deleted
# from Buffer by hand), so the top-up routine adds them again when their new day comes.
import json, datetime as dt
NOW = dt.datetime(2026, 10, 31, 10, 30, tzinfo=dt.timezone(dt.timedelta(hours=2)))
b = json.load(open('backlog.json'))
moved = unscheduled = 0
for i in b['items']:
    if '-cd-' in i['id']:
        continue
    t = dt.datetime.fromisoformat(i['post']['dueAt'])
    if t < NOW:
        continue
    i['post']['dueAt'] = (t + dt.timedelta(days=8)).isoformat()
    moved += 1
    if i['scheduled']:
        i['scheduled'] = False
        unscheduled += 1
json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
print('moved', moved, 'unscheduled', unscheduled)
