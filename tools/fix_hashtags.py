# Keeps every caption at 5 hashtags or fewer (the platforms count "#1" in "takes #1" as a hashtag too).
#   1. "#<number>" in the text becomes "No. <number>" ("at #1" -> "at No. 1").
#   2. If a caption still has more than 5 hashtags, the generic ones go first (#reels, #fyp, #shorts,
#      #musicranking, ...), then the last ones, until 5 are left.
# Usage (repo root): python3 tools/fix_hashtags.py [--dry-run]    -> fixes backlog.json and pack.json
# Also importable: fix(text) -> new text.
import json, re, sys

LIMIT = 5
GENERIC = ['#reels', '#fyp', '#shorts', '#musicranking', '#albumranking', '#musicfacts', '#top10', '#tierlist']
TAG = re.compile(r'(?<![\w&/])#[^\s#.,!?:;()"\']+')


def tags(text):
    return TAG.findall(text)


def fix(text):
    text = re.sub(r'(?<![\w&/])#(\d+)\b', r'No. \1', text)
    found = tags(text)
    drop = []
    for g in GENERIC + list(reversed(found)):
        if len(found) - len(drop) <= LIMIT: break
        if g in found and g not in drop: drop.append(g)
    for g in drop:
        text = re.sub(r'[ \t]?' + re.escape(g) + r'(?![\w])', '', text, count=1)
    return re.sub(r'[ \t]+\n', '\n', text).rstrip()


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    b = json.load(open('backlog.json')); pk = json.load(open('pack.json'))
    changed = []
    for i in b['items']:
        t = i['post'].get('text', '')
        n = fix(t)
        if n != t:
            changed.append((i['id'], len(tags(t)), len(tags(n)), i.get('scheduled'), i.get('bufferId')))
            i['post']['text'] = n
    for p in pk['posts']:
        for k in ('caption', 'ytDesc'):
            if p.get(k): p[k] = fix(p[k])
    print(len(changed), 'captions fixed;', sum(1 for c in changed if c[3]), 'of them already in Buffer')
    if not dry:
        json.dump(b, open('backlog.json', 'w'), indent=1, ensure_ascii=False)
        json.dump(pk, open('pack.json', 'w'), indent=1, ensure_ascii=False)
    json.dump([c for c in changed if c[3]], open('/dev/stdout', 'w'))
