#!/usr/bin/env python3
"""
Adds new baked-sound videos (album battles, music quizzes) to the schedule and re-dates every automatic video
that isn't in Buffer yet so the TYPES ROTATE: artist countdown -> list video -> album battle -> music quiz -> ...
(a type that runs out drops out of the rotation). One video a day, all three apps at the same minute, in the
US-evening slot (19:30-20:10 US Eastern = 02:30-03:10 Israel the next day). Posts already in Buffer keep their
time; paused posts are never touched.

Usage (repo root):  python3 tools/rotation.py new_videos.json
new_videos.json: [{"kind": "battle"|"quiz", "slug": "...", "url": "https://...mp4", "title": "...",
                   "ig": "...", "tt": "...", "yt_title": "...", "yt": "..."}]
"""
import datetime as dt, json, random, sys
from zoneinfo import ZoneInfo

TZ, ET = ZoneInfo("Asia/Jerusalem"), ZoneInfo("America/New_York")
IG, TT, YT = "6adb5ec6778b240e2f9d4ea5", "6adb5f07778b240e2f9d51b0", "6adb5f1d778b240e2f9d52af"
ORDER = ["countdown", "list", "battle", "quiz"]
PREFIX = {"yt-reel-": IG, "yt-ttv-": TT, "yt-": YT}


def kind_of(base):
    return "list" if base.startswith("cd-list-") else "battle" if base.startswith("cd-battle-") else \
           "quiz" if base.startswith("cd-quiz-") else "countdown"


def base_of(iid):
    for p in ("yt-reel-", "yt-ttv-", "yt-"):
        if iid.startswith(p): return iid[len(p):]
    return iid


b = json.load(open("backlog.json")); pk = json.load(open("pack.json"))
new = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else []
have = {i["id"] for i in b["items"]}
for v in new:                                                  # 3 posts per new video
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

auto = [i for i in b["items"] if i["post"].get("schedulingType") == "automatic" and not i.get("paused")]
in_buffer_days = [dt.datetime.fromisoformat(i["post"]["dueAt"]).astimezone(ET).date() for i in auto if i.get("scheduled")]
start = max(in_buffer_days) + dt.timedelta(days=1)            # first US date with nothing in Buffer yet
todo = {}                                                      # kind -> [base, ...] in their current order
for i in sorted([i for i in auto if not i.get("scheduled")], key=lambda i: i["post"]["dueAt"]):
    base = base_of(i["id"])
    todo.setdefault(kind_of(base), [])
    if base not in todo[kind_of(base)]: todo[kind_of(base)].append(base)
rnd, day, plan, k = random.Random(2611), start, [], 0
while any(todo.values()):
    kind = ORDER[k % len(ORDER)]; k += 1
    if not todo.get(kind): continue
    base = todo[kind].pop(0)
    m = rnd.randint(19 * 60 + 30, 20 * 60 + 10)                # US Eastern evening
    when = dt.datetime.combine(day, dt.time(m // 60, m % 60), ET).astimezone(TZ)
    for i in auto:
        if not i.get("scheduled") and base_of(i["id"]) == base:
            i["post"]["dueAt"] = when.isoformat()
    plan.append((when, kind, base)); day += dt.timedelta(days=1)
b["items"].sort(key=lambda i: i["post"]["dueAt"])
json.dump(b, open("backlog.json", "w"), indent=1, ensure_ascii=False)
json.dump(pk, open("pack.json", "w"), indent=1, ensure_ascii=False)
for when, kind, base in plan:
    print(when.strftime("%a %d %b %H:%M Israel"), f"{kind:9}", base)
