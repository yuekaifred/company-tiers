import csv
import io
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from PIL import Image

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
UA = {"User-Agent": "company-tier-logo-fetcher/1.0 (personal project; fyang151@gmail.com)"}
s = requests.Session()
s.headers.update(UA)


def load():
    with open(ROOT / "companies.tsv") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def get(url, **kw):
    for i in range(4):
        try:
            r = s.get(url, timeout=20, **kw)
            if r.status_code == 429:
                time.sleep(2 + i * 3)
                continue
            return r
        except requests.RequestException:
            time.sleep(1 + i)
    return None


def qids(rows):
    out = {}
    titles = [r["wiki"] for r in rows]
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        r = get("https://en.wikipedia.org/w/api.php", params={
            "action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
            "redirects": 1, "format": "json", "titles": "|".join(chunk)})
        q = r.json()["query"]
        alias = {}
        for n in q.get("normalized", []) + q.get("redirects", []):
            alias[n["from"]] = n["to"]
        found = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in q["pages"].values()}
        for t in chunk:
            u = t
            while u in alias:
                u = alias[u]
            out[t] = found.get(u)
    return out


def claims(ids):
    out = {}
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 50):
        r = get("https://www.wikidata.org/w/api.php", params={
            "action": "wbgetentities", "ids": "|".join(ids[i:i + 50]),
            "props": "claims", "format": "json"})
        for k, e in r.json()["entities"].items():
            c = e.get("claims", {})
            def files(p):
                vals = []
                for st in c.get(p, []):
                    if st.get("rank") == "deprecated":
                        continue
                    v = st["mainsnak"].get("datavalue", {}).get("value")
                    if v:
                        vals.append((st.get("rank") == "preferred", v))
                vals.sort(key=lambda x: not x[0])
                return [v for _, v in vals]
            out[k] = {"icon": files("P8972"), "logo": files("P154")}
    return out


def save_img(data, path):
    try:
        im = Image.open(io.BytesIO(data))
        if getattr(im, "n_frames", 1) > 1 and im.format == "ICO":
            im = max((im.ico.getimage(sz) for sz in im.ico.sizes()), key=lambda x: x.width)
        im.load()
        im = im.convert("RGBA")
        im.save(path)
        return im.size
    except Exception:
        return None


def commons(fname, path):
    r = get("https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(fname.replace(" ", "_")) + "?width=640")
    if r is None or r.status_code != 200:
        return None
    return save_img(r.content, path)


def site_icons(domain):
    r = get("https://" + domain, allow_redirects=True)
    if r is None or r.status_code >= 400:
        return []
    html = r.text[:400000]
    cands = []
    for tag in re.findall(r"<link\b[^>]*>", html, re.I):
        rel = re.search(r'rel=["\']?([^"\'>]+)', tag, re.I)
        href = re.search(r'href=["\']?([^"\'\s>]+)', tag, re.I)
        if not rel or not href:
            continue
        rel = rel.group(1).lower()
        if "icon" not in rel:
            continue
        h = href.group(1).replace("&amp;", "&")
        if h.lower().split("?")[0].endswith(".svg") or h.startswith("data:"):
            continue
        sz = re.search(r'sizes=["\']?(\d+)x', tag, re.I)
        score = int(sz.group(1)) if sz else (180 if "apple" in rel else 32)
        cands.append((score, urljoin(r.url, h)))
    cands.sort(reverse=True)
    return [u for _, u in cands[:3]]


def fetch_one(row, info):
    d = RAW / row["id"]
    d.mkdir(parents=True, exist_ok=True)
    meta = {}
    if info:
        for kind in ("icon", "logo"):
            for j, f in enumerate(info[kind][:2]):
                p = d / f"wd_{kind}{j}.png"
                sz = commons(f, p)
                if sz:
                    meta[p.name] = {"src": "commons:" + f, "size": sz}
    try:
        for j, u in enumerate(site_icons(row["domain"])):
            r = get(u)
            if r is not None and r.status_code == 200:
                p = d / f"site{j}.png"
                sz = save_img(r.content, p)
                if sz:
                    meta[p.name] = {"src": u, "size": sz}
    except Exception:
        pass
    r = get(f"https://www.google.com/s2/favicons?domain={row['domain']}&sz=256")
    if r is not None and r.status_code == 200:
        p = d / "gfav.png"
        sz = save_img(r.content, p)
        if sz:
            meta[p.name] = {"src": "google-s2", "size": sz}
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    return row["id"], len(meta)


def main():
    rows = load()
    only = set(sys.argv[1:])
    if only:
        rows = [r for r in rows if r["id"] in only]
    q = qids(rows)
    c = claims(list(q.values()))
    (ROOT / "wikidata.json").write_text(json.dumps({r["id"]: {"qid": q.get(r["wiki"]), **c.get(q.get(r["wiki"]), {})} for r in rows}, indent=1))
    with ThreadPoolExecutor(8) as ex:
        for cid, n in ex.map(lambda r: fetch_one(r, c.get(q.get(r["wiki"]))), rows):
            print(cid, n, flush=True)


if __name__ == "__main__":
    main()
