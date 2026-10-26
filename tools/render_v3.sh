#!/bin/sh
# Re-renders every future video with build_short.py into video/<id>-v3.mp4 (4 at a time).
cd "$(dirname "$0")"
PY=${PY:-../../venv/bin/python}
python3 -c "import json;print('\n'.join(json.load(open('$1'))))" | xargs -P 4 -I{} sh -c "$PY build_short.py {} ../tiktok/{} $2 hooks.json ../video/{}-v3.mp4 duel_answers.json || echo FAILED {}"
echo RENDER V3 DONE
