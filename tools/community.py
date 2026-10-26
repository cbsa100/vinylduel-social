"""Community song order for an album from the live VinylDuel API (public endpoint, no login)."""
import json, sys, time, urllib.parse, urllib.request

def community(artist, title):
    q = urllib.parse.urlencode({"artist": artist, "title": title})
    req = urllib.request.Request(f"https://vinylduel.app/api/pages/album?{q}", headers={"User-Agent": "vinylduel-social-tools"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
    except Exception as e:
        return None
    return [i["title"] for i in d.get("community", {}).get("items", [])]

if __name__ == "__main__":
    albums = json.load(open(sys.argv[1]))          # {key: [artist, title]}
    out = {}
    for k, (a, t) in albums.items():
        out[k] = community(a, t); time.sleep(0.6)
        print(k, (out[k] or [None])[0], '|', (out[k] or [None])[-1], flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
