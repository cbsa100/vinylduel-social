#!/usr/bin/env python3
"""
Dates every automatic video that isn't in Buffer yet (and, given a file, adds new battles and quizzes first).

Instagram and YouTube: TWO videos a day (since 20 Nov 2026): an artist countdown plus one of the other formats
(list video -> album battle -> music quiz, in turn), each at the same minute on both apps. One goes out in the
US afternoon (15:30-16:10 US Eastern = 22:30-23:10 Israel) and one in the US evening (19:30-20:10 US Eastern =
02:30-03:10 Israel the next day). Which of the two gets the evening alternates by day, so the numbers can tell
the time of day and the format apart. When the countdowns or the other formats run out, the days carry on with
one video, in the evening. Two is also the most Buffer accepts for YouTube on one calendar day ("maximum number
of posts YouTube allows in a day (2)"); these two slots give two a day in Israel, UTC and US time alike, so
don't add a third slot or move one across midnight.

TikTok: still ONE video a day, in the US evening, in the order the videos go out on the other two apps (its
posts get next to no views, so it was left out of the doubling).

Posts already in Buffer keep their time; paused posts are never touched. Running it twice changes nothing more.

Usage (repo root):  python3 tools/rotation.py [new_videos.json]
new_videos.json: [{"kind": "battle"|"quiz", "slug": "...", "url": "https://...mp4", "title": "...",
                   "ig": "...", "tt": "...", "yt_title": "...", "yt": "..."}]
"""
import datetime as dt, json, random, sys
from zoneinfo import ZoneInfo

TZ, ET = ZoneInfo("Asia/Jerusalem"), ZoneInfo("America/New_York")
IG, TT, YT = "6adb5ec6778b240e2f9d4ea5", "6adb5f07778b240e2f9d51b0", "6adb5f1d778b240e2f9d52af"
OTHERS = ["list", "battle", "quiz"]
SLOTS = {"afternoon": (15 * 60 + 30, 16 * 60 + 10), "evening": (19 * 60 + 30, 20 * 60 + 10)}   # US Eastern
FIRST_DAY = dt.date(2026, 11, 20)                              # the first two-a-day date (US Eastern)


def kind_of(base):
    return "list" if base.startswith("cd-list-") else "battle" if base.startswith("cd-battle-") else \
           "quiz" if base.startswith("cd-quiz-") else "countdown"


def group_of(base):
    return "countdown" if kind_of(base) == "countdown" else "other"


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


def slot_for(group, day):
    """The countdown has the afternoon on FIRST_DAY, the evening the day after, and so on; the other format
    has whichever is left."""
    countdown = "afternoon" if (day - FIRST_DAY).days % 2 == 0 else "evening"
    return countdown if group == "countdown" else ("evening" if countdown == "afternoon" else "afternoon")


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


def date_all(b, now=None):
    """Gives every automatic post that isn't in Buffer its time. Returns the plan lines."""
    now = now or dt.datetime.now(dt.timezone.utc)
    tomorrow = us_day(now) + dt.timedelta(days=1)
    auto = automatic(b)
    main = [i for i in auto if i["post"]["channelId"] in (IG, YT)]
    tiktok = [i for i in auto if i["post"]["channelId"] == TT]
    plan = []

    # --- Instagram + YouTube: a countdown and one other format a day ---
    in_buffer = {}                                             # base -> its time in Buffer
    for i in main:
        if i.get("scheduled"): in_buffer[base_of(i["id"])] = due(i)
    taken = {}                                                 # US date -> {slot: group}, from what Buffer holds
    for base, when in in_buffer.items():
        if when > now: taken.setdefault(us_day(when), {})[slot_of(when)] = group_of(base)
    queue = {"countdown": [], "list": [], "battle": [], "quiz": []}
    for i in sorted(main, key=due):
        base = base_of(i["id"])
        if base in in_buffer:                                  # one app is in Buffer already: the other follows it
            if not i.get("scheduled"): i["post"]["dueAt"] = in_buffer[base].isoformat()
        elif base not in queue[kind_of(base)]:
            queue[kind_of(base)].append(base)
    sent_others = sorted((when, kind_of(base)) for base, when in in_buffer.items() if group_of(base) == "other")
    turn = (OTHERS.index(sent_others[-1][1]) + 1) if sent_others else 0   # the format after the last one in Buffer

    def waiting(group):
        return bool(queue["countdown"]) if group == "countdown" else any(queue[k] for k in OTHERS)

    def take(group):
        nonlocal turn
        if group == "countdown": return queue["countdown"].pop(0)
        while not queue[OTHERS[turn % 3]]: turn += 1
        turn += 1
        return queue[OTHERS[(turn - 1) % 3]].pop(0)

    day = tomorrow
    while waiting("countdown") or waiting("other"):
        have = dict(taken.get(day, {}))
        todo = [g for g in ("countdown", "other") if g not in have.values() and waiting(g)]
        alone = len(todo) + len(have) == 1                     # nothing to pair it with: the evening
        for group in todo:
            free = [s for s in ("evening", "afternoon") if s not in have]
            if not free: break
            want = "evening" if alone else slot_for(group, day)
            slot = want if want in free else free[0]
            base, when = take(group), slot_time(day, slot)
            have[slot] = group
            for i in main:
                if base_of(i["id"]) == base: i["post"]["dueAt"] = when.isoformat()
            plan.append((when, "IG+YT ", kind_of(base), base))
        day += dt.timedelta(days=1)

    # --- TikTok: one a day, US evening, in the order of the other two apps ---
    order = {base_of(i["id"]): due(i) for i in main}
    busy = {us_day(due(i)) for i in tiktok if i.get("scheduled") and due(i) > now}
    day = tomorrow
    for i in sorted((i for i in tiktok if not i.get("scheduled")), key=lambda i: order.get(base_of(i["id"]), due(i))):
        while day in busy: day += dt.timedelta(days=1)
        when = slot_time(day, "evening")
        i["post"]["dueAt"] = when.isoformat()
        plan.append((when, "TikTok", kind_of(base_of(i["id"])), base_of(i["id"])))
        day += dt.timedelta(days=1)

    b["items"].sort(key=lambda i: i["post"]["dueAt"])
    return [f"{w.astimezone(ET):%a %d %b %H:%M} US Eastern = {w:%a %H:%M} Israel  {app}  {kind:9} {base}"
            for w, app, kind, base in sorted(plan, key=lambda p: (p[1], p[0]))]


if __name__ == "__main__":
    b = json.load(open("backlog.json")); pk = json.load(open("pack.json"))
    if len(sys.argv) > 1: add_new(b, pk, json.load(open(sys.argv[1])))
    lines = date_all(b)
    json.dump(b, open("backlog.json", "w"), indent=1, ensure_ascii=False)
    json.dump(pk, open("pack.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lines))
