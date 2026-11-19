# One-off (19 Nov 2026): Instagram and YouTube go from one video a day to two (a countdown plus another format,
# see rotation.py). The Instagram and YouTube posts that were already in Buffer, one a day from 20 Nov, are
# paired up: the countdowns in their order from 20 Nov, the other formats in their order from 20 Nov. A post
# that keeps its date and slot keeps its minute. TikTok is not touched.
# Writes backlog.json and prints the Buffer posts that moved (JSON lines: postId, dueAt, id); rotation.py then
# dates everything that is not in Buffer yet.
import datetime as dt, json, sys
sys.path.insert(0, "tools")
from rotation import ET, IG, YT, automatic, base_of, due, group_of, slot_for, slot_of, slot_time, us_day

b = json.load(open("backlog.json"))
now = dt.datetime.now(dt.timezone.utc)
first = us_day(now) + dt.timedelta(days=1)
posts = [i for i in automatic(b) if i["post"]["channelId"] in (IG, YT) and i.get("scheduled") and us_day(due(i)) >= first]
order = {"countdown": [], "other": []}
for i in sorted(posts, key=due):
    base = base_of(i["id"])
    if base not in order[group_of(base)]: order[group_of(base)].append(base)
for group, bases in order.items():
    for n, base in enumerate(bases):
        day = first + dt.timedelta(days=n)
        slot = slot_for(group, day)
        for i in posts:
            if base_of(i["id"]) != base: continue
            old = due(i)
            when = old if (us_day(old), slot_of(old)) == (day, slot) else slot_time(day, slot)
            if when != old:
                i["post"]["dueAt"] = when.isoformat()
                print(json.dumps({"postId": i["bufferId"], "dueAt": when.isoformat(), "id": i["id"],
                                  "us": when.astimezone(ET).strftime("%a %d %b %H:%M")}))
json.dump(b, open("backlog.json", "w"), indent=1, ensure_ascii=False)
