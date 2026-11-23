# One-off (23 Nov 2026): back to ONE video a day, the same video at the same minute on all three apps (see
# rotation.py for why). Catch-up first: YouTube's "Defined the 90s" failed, so it goes out with TikTok's copy
# tonight; TikTok was behind by Imagine Dragons and Paramore, which go out on TikTok alone in the US-afternoon
# slot on 24 and 25 Nov. Everything else that hasn't gone out, in Buffer or not, is re-dated by rotation.py.
# Writes backlog.json and prints the Buffer posts that moved (JSON lines: postId, dueAt, id).
import datetime as dt, json, sys
sys.path.insert(0, "tools")
from rotation import ET, automatic, date_all, due, slot_time

b = json.load(open("backlog.json"))
now = dt.datetime.now(dt.timezone.utc)
by_id = {i["id"]: i for i in b["items"]}
before = {i["id"]: i["post"]["dueAt"] for i in automatic(b) if i.get("scheduled")}
tonight = by_id["yt-ttv-cd-list-defined-90s"]["post"]["dueAt"]
by_id["yt-cd-list-defined-90s"]["post"]["dueAt"] = tonight
by_id["yt-ttv-cd-imaginedragons"]["post"]["dueAt"] = slot_time(dt.date(2026, 11, 24), "afternoon").isoformat()
by_id["yt-ttv-cd-paramore"]["post"]["dueAt"] = slot_time(dt.date(2026, 11, 25), "afternoon").isoformat()
keep = {"yt-cd-list-defined-90s", "yt-ttv-cd-list-defined-90s", "yt-ttv-cd-imaginedragons", "yt-ttv-cd-paramore"}
for line in date_all(b, now, redate_buffer=True, keep=keep)[:12]: print("#", line)
for iid, old in before.items():
    i = by_id[iid]
    if i["post"]["dueAt"] != old:
        print(json.dumps({"postId": i["bufferId"], "dueAt": i["post"]["dueAt"], "id": iid,
                          "us": due(i).astimezone(ET).strftime("%a %d %b %H:%M")}))
json.dump(b, open("backlog.json", "w"), indent=1, ensure_ascii=False)
