#!/usr/bin/env python3
"""
Dates every automatic video that isn't in Buffer yet (and, given a file, adds new battles and quizzes first).

ONE video a day (since 23 Nov 2026), the same video at the same minute on Instagram, TikTok and YouTube, in the
US evening (19:30-20:10 US Eastern = 02:30-03:10 Israel the next day). The types rotate: artist countdown ->
list video -> album battle -> music quiz (a type that runs out drops out). Two a day (20-23 Nov) broke on
YouTube: Buffer's free plan allows only 2 YouTube posts in any rolling 24 hours, and the US-evening post was
always the third, so it failed ("The daily posting limit for this channel has been reached").

Posts already in Buffer keep their time (the apps that aren't in Buffer yet follow it); paused posts are never
touched. Running it twice changes nothing more.

Usage (repo root):  python3 tools/rotation.py [new_videos.json]
new_videos.json: [{"kind": "battle"|"quiz", "slug": "...", "url": "https://...mp4", "title": "...",
                   "ig": "...", "tt": "...", "yt_title": "...", "yt": "..."}]
"""
import datetime as dt, json, random, sys
from zoneinfo import ZoneInfo

TZ, ET = ZoneInfo("Asia/Jerusalem"), ZoneInfo("America/New_York")
IG, TT, YT = "6adb5ec6778b240e2f9d4ea5", "6adb5f07778b240e2f9d51b0", "6adb5f1d778b240e2f9d52af"
ORDER = ["countdown", "list", "battle", "quiz"]
SLOTS = {"afternoon": (15 * 60 + 30, 16 * 60 + 10), "evening": (19 * 60 + 30, 20 * 60 + 10)}   # US Eastern


def kind_of(base):
    return "list" if base.startswith("cd-list-") else "battle" if base.startswith("cd-battle-") else \
           "quiz" if base.startswith("cd-quiz-") else "countdown"



def base_of(iid):
    for p in ("yt-reel-", "yt-ttv-", "yt-"):
        if iid.startswith(p): return iid[len(p):]
    return iid


def due(i):
    return dt.datetime.fromisoformat(i["post"]["dueAt"])


def us_day(when):
    return when.astimezone(ET).date()


def slot_of(when):
    return "afternoon" if when.astimezone(ET).hour < 18 else "evening"


def slot_time(day, slot):
    """A fixed minute inside the slot for that date (the same answer every run)."""
    m = random.Random(f"{day} {slot}").randint(*SLOTS[slot])
    return dt.datetime.combine(day, dt.time(m // 60, m % 60), ET).astimezone(TZ)



def automatic(b):
    return [i for i in b["items"] if i["post"].get("schedulingType") == "automatic" and not i.get("paused")]


def add_new(b, pk, new):
    have = {i["id"] for i in b["items"]}
    for v in new:                                              # 3 posts per new video
        base = f"cd-{v['kind']}-{v['slug']}"
        if f"yt-reel-{base}" in have: continue
        video = [{"video": {"url": v["url"]}}]
        for pre, ch, text, meta in (("yt-reel-", IG, v["ig"], {"instagram": {"type": "reel", "shouldShareToFeed": True}}),
                                    ("yt-ttv-", TT, v["tt"], {"tiktok": {"title": v["title"]}}),
                                    ("yt-", YT, v["yt"], {"youtube": {"title": v["yt_title"], "categoryId": "10", "privacy": "public", "madeForKids": False}})):
            b["items"].append({"id": pre + base, "scheduled": False, "post": {"channelId": ch, "schedulingType": "automatic",
                               "mode": "customScheduled", "dueAt": "2099-01-01T00:00:00+02:00", "text": text, "assets": video, "metadata": meta}})
        if not any(p["id"] == base for p in pk["posts"]):
            pk["posts"].append({"id": base, "platform": "Video", "section": v["kind"], "hook": v["title"], "caption": v["ig"],
                                "ttTitle": v["title"], "ytTitle": v["yt_title"], "ytDesc": v["yt"], "slides": [], "video": v["url"]})


def date_all(b, now=None, redate_buffer=False, keep=()):
    """Gives every automatic post that isn't in Buffer its time: one video a day, the same minute on all three
    apps, in the US evening. With redate_buffer, posts already in Buffer that haven't gone out yet are re-dated
    too (except the item ids in keep). Returns the plan lines."""
    now = now or dt.datetime.now(dt.timezone.utc)
    tomorrow = us_day(now) + dt.timedelta(days=1)
    auto = automatic(b)
    fixed = lambda i: i["id"] in keep or (i.get("scheduled") and (not redate_buffer or due(i) <= now))
    fixed_at = {}                                              # base -> its time in Buffer (evening slot only)
    taken = {}                                                 # US date -> kind, from what keeps its time
    for i in auto:
        if fixed(i) and slot_of(due(i)) == "evening":
            fixed_at.setdefault(base_of(i["id"]), due(i))
            if due(i) > now: taken[us_day(due(i))] = kind_of(base_of(i["id"]))
    queue = {k: [] for k in ORDER}
    for i in sorted(auto, key=due):
        if fixed(i): continue
        base = base_of(i["id"])
        if base in fixed_at:                                   # one app keeps its time: the others follow it
            i["post"]["dueAt"] = fixed_at[base].isoformat()
        elif base not in queue[kind_of(base)]:
            queue[kind_of(base)].append(base)
    last = [k for d, k in sorted(taken.items())] or [kind_of(base_of(i["id"])) for i in sorted(auto, key=due) if due(i) <= now]
    turn = ORDER.index(last[-1]) + 1 if last else 0           # the format after the last one that keeps its time
    plan, day = [], tomorrow
    while any(queue.values()):
        while day in taken: day += dt.timedelta(days=1)
        while not queue[ORDER[turn % len(ORDER)]]: turn += 1
        base = queue[ORDER[turn % len(ORDER)]].pop(0); turn += 1
        when = slot_time(day, "evening")
        for i in auto:
            if base_of(i["id"]) == base and not fixed(i): i["post"]["dueAt"] = when.isoformat()
        plan.append((when, kind_of(base), base))
        day += dt.timedelta(days=1)
    b["items"].sort(key=lambda i: i["post"]["dueAt"])
    return [f"{w.astimezone(ET):%a %d %b %H:%M} US Eastern = {w:%a %H:%M} Israel  {kind:9} {base}" for w, kind, base in plan]


if __name__ == "__main__":
    b = json.load(open("backlog.json")); pk = json.load(open("pack.json"))
    if len(sys.argv) > 1: add_new(b, pk, json.load(open(sys.argv[1])))
    lines = date_all(b)
    json.dump(b, open("backlog.json", "w"), indent=1, ensure_ascii=False)
    json.dump(pk, open("pack.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lines))
