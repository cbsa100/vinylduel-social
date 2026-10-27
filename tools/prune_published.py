# Removes video files from the site once every post that uses them has been published, so the GitHub Pages
# site stays under its 1 GB limit. The posts already live on Instagram/TikTok/YouTube; the Post Pack shows
# "Published. The video file was removed" for them (pack.removedVideos).
#
# Usage (from the repo root):  python3 tools/prune_published.py [--dry-run] [--keep file1.mp4 file2.mp4 ...]
# --keep: files Buffer still has queued under an older name (check list_posts first: a post that is in Buffer
# keeps the URL it was created with, even if backlog.json now points at a newer file).
import json, os, sys, datetime as dt

MARGIN = dt.timedelta(hours=12)        # Buffer and the apps have long since fetched the file by then
args = sys.argv[1:]
dry = '--dry-run' in args
keep = set(args[args.index('--keep') + 1:]) if '--keep' in args else set()

b = json.load(open('backlog.json')); pk = json.load(open('pack.json'))
now = dt.datetime.now(dt.timezone.utc)
last_use, published = {}, set()
for i in b['items']:
    t = dt.datetime.fromisoformat(i['post']['dueAt'])
    for a in i['post'].get('assets', []):
        u = (a.get('video') or {}).get('url', '')
        if '/video/' in u:
            f = u.split('/video/')[1]
            last_use[f] = max(last_use.get(f, t), t)
for base, path in (pk.get('videoFiles') or {}).items():          # posted before Buffer took over
    if any(k.endswith(base) and k != base for k in pk.get('posted', {})):
        published.add(path.split('/')[-1])

gone, freed = [], 0
for f in sorted(os.listdir('video')):
    if f in keep: continue
    if f in last_use: ok = last_use[f] < now - MARGIN
    else: ok = f in published                                     # never touch a file nothing points to
    if ok:
        freed += os.path.getsize('video/' + f); gone.append(f)
        if not dry: os.remove('video/' + f)
if not dry:
    pk['removedVideos'] = sorted(set(pk.get('removedVideos', [])) | set(gone))
    json.dump(pk, open('pack.json', 'w'), indent=1, ensure_ascii=False)
print(('would remove' if dry else 'removed'), len(gone), 'files,', round(freed / 1e6), 'MB')
for f in gone: print(' ', f)
