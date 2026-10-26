import json, random, datetime as dt
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Jerusalem')
B='social/backlog.json'
b=json.load(open(B))
buf={  # bufferId -> current due (UTC), from list_posts
}
now=dt.datetime.now(dt.timezone.utc)
ids=set(json.load(open("sched/buf_now.json")))
ch={'6adb5ec6778b240e2f9d4ea5':'IG','6adb5f07778b240e2f9d51b0':'TT','6adb5f1d778b240e2f9d52af':'YT'}
def due(it): return dt.datetime.fromisoformat(it['post']['dueAt'])
def isvid(it): return it['post']['assets'][0].get('video') is not None
pending=[it for it in b['items'] if (not it['scheduled'] and due(it)>now) or (it.get('bufferId') in ids and due(it)>now)]
missing=ids-{it.get('bufferId') for it in b['items']}
assert not missing, missing
edits=[]
rnd=random.Random(2024)
today=now.astimezone(TZ).date()
for cid,name in ch.items():
    items=sorted([i for i in pending if i['post']['channelId']==cid],key=due)
    # today: keep up to 2 already-set times that are still ahead
    keep=[i for i in items if due(i).astimezone(TZ).date()==today][:2]
    rest=[i for i in items if i not in keep]
    car=[i for i in rest if not isvid(i)]; vid=[i for i in rest if isvid(i)]
    day=today+dt.timedelta(days=1); k=0
    while car or vid:
        if name=='YT': pick=[vid.pop(0) for _ in range(min(2,len(vid)))]
        else:
            pick=[]
            if car: pick.append(car.pop(0))
            if vid: pick.append(vid.pop(0))
            if len(pick)<2 and (car or vid): pick.append((car or vid).pop(0))
            if k%2: pick.reverse()
        slots=[(rnd.randint(11*60,14*60+30)),(rnd.randint(18*60,21*60+45))]
        for it,m in zip(pick,slots):
            t=dt.datetime.combine(day,dt.time(m//60,m%60),TZ)
            new=t.isoformat()
            if it['post']['dueAt']!=new:
                it['post']['dueAt']=new
                if it.get('bufferId') in ids: edits.append({'postId':it['bufferId'],'id':it['id'],'dueAt':new})
        day+=dt.timedelta(days=1); k+=1
    print(name,'last day',day-dt.timedelta(days=1),'pending',len(items))
json.dump(edits,open('sched/edits2.json','w'),indent=1)
json.dump(b,open(B,'w'),indent=1,ensure_ascii=False)
print(len(edits),'buffer edits')
for it in sorted(pending,key=due): print(ch[it['post']['channelId']],it['post']['dueAt'],'B' if it.get('bufferId') in ids else '-', 'vid' if isvid(it) else 'car', it['id'])
