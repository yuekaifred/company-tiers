import csv
import hashlib
import json
import subprocess
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
WEB = ROOT.parent / "web" / "public"
OUT = WEB / "logos"
SHEETS = ROOT / "sheets"
SIZE = 256
PAD = 0.1


def rank(name, w, h):
    big = min(w, h) >= 120
    sq = max(w, h) / max(1, min(w, h)) <= 1.4
    if name.startswith("wd_icon"):
        return 0 if big else 6
    if name.startswith("site"):
        return 1 if big and sq else 7
    if name == "gfav.png":
        return 2 if min(w, h) >= 128 else 8
    if name.startswith("wd_logo"):
        return 3 if sq else 4
    return 9


def load_rgba(p):
    return np.array(Image.open(p).convert("RGBA")).astype(np.int16)


def strip_bg(a):
    h, w = a.shape[:2]
    if (a[..., 3] < 250).mean() > 0.01:
        return a, False
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])[:, :3]
    ref = np.median(edge, axis=0)
    if np.abs(edge - ref).max(axis=1).mean() > 12 or ref.min() < 225:
        return a, True
    diff = np.abs(a[..., :3] - ref).max(axis=2) <= 24
    seen = np.zeros((h, w), bool)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if diff[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if diff[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and diff[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    b = a.copy()
    b[seen, 3] = 0
    return b, False


def normalize(p):
    a, filled = strip_bg(load_rgba(p))
    m = a[..., 3] > 16
    if not m.any():
        return None, filled
    ys, xs = np.where(m)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    w, h = im.size
    inner = SIZE if filled and abs(w - h) <= max(w, h) * 0.05 else int(SIZE * (1 - 2 * PAD))
    s = inner / max(w, h)
    im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    c = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    c.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2))
    return c, filled


def analyze(im):
    a = np.array(im).astype(np.float32) / 255
    al = a[..., 3]
    vis = al > 0.5
    cov = vis.mean()
    lum = a[..., :3].min(axis=2)[vis]
    light = float((lum > 0.88).mean()) if lum.size else 0
    colors = len(np.unique((a[..., :3][vis] * 15).astype(np.uint8), axis=0)) if lum.size else 0
    return cov, light, colors


def manual_file(cid):
    m = ROOT / "manual"
    svg = m / f"{cid}.svg"
    if svg.exists():
        out = m / ".render" / f"{cid}.png"
        out.parent.mkdir(exist_ok=True)
        if not out.exists() or out.stat().st_mtime < svg.stat().st_mtime:
            subprocess.run(["node", str(ROOT / "svg2png.mjs"), str(svg), str(out), "640"], check=True)
        return out
    for ext in ("png", "webp", "jpg", "jpeg"):
        if (m / f"{cid}.{ext}").exists():
            return m / f"{cid}.{ext}"
    return None


def main():
    rows = list(csv.DictReader(open(ROOT / "companies.tsv"), delimiter="\t"))
    over = {}
    for f in sorted(ROOT.glob("overrides*.json")):
        over.update(json.loads(f.read_text()))
    OUT.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(exist_ok=True)
    data, report, hashes = [], {}, {}
    for r in rows:
        cid = r["id"]
        d = RAW / cid
        meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        o = over.get(cid, {})
        if o.get("drop"):
            continue
        manual = manual_file(cid)
        if manual:
            d, cands = manual.parent, [manual.name]
        elif o.get("pick"):
            cands = [o["pick"]]
        else:
            cands = sorted(meta, key=lambda n: rank(n, *meta[n]["size"]))
        issues, chosen = [], None
        for n in cands:
            im, filled = normalize(d / n)
            if im is None:
                continue
            cov, light, colors = analyze(im)
            if cov < 0.01 or colors < 1:
                continue
            chosen = (n, im, filled, cov, light, colors)
            break
        if not chosen:
            report[cid] = {"issues": ["no usable logo"]}
            continue
        n, im, filled, cov, light, colors = chosen
        src = meta.get(n) or {"src": "manual:" + n, "size": Image.open(d / n).size}
        w, h = src.get("size", (0, 0))
        if min(w, h) < 64:
            issues.append(f"lowres {w}x{h}")
        if cov < 0.04:
            issues.append(f"sparse {cov:.3f}")
        if colors <= 1 and not filled:
            issues.append("single flat color")
        bg = o.get("bg") or ("dark" if light > 0.75 and not filled else "light")
        im.save(OUT / f"{cid}.webp", "WEBP", quality=90, method=6)
        hsh = hashlib.md5(im.tobytes()).hexdigest()
        if hsh in hashes:
            issues.append(f"duplicate of {hashes[hsh]}")
        hashes[hsh] = cid
        report[cid] = {"pick": n, "src": src.get("src"), "size": [w, h], "coverage": round(cov, 3), "light": round(light, 3), "bg": bg, "issues": issues}
        data.append({"id": cid, "name": r["name"], "category": r["category"], "logo": f"logos/{cid}.webp", "bg": bg})
    keep = {e["id"] for e in data}
    for f in OUT.glob("*.webp"):
        if f.stem not in keep:
            f.unlink()
    (WEB / "companies.json").write_text(json.dumps(data, separators=(",", ":")))
    (ROOT / "report.json").write_text(json.dumps(report, indent=1))
    for f in SHEETS.glob("*.png"):
        f.unlink()
    per, cell = 30, 160
    for i in range(0, len(data), per):
        chunk = data[i:i + per]
        sheet = Image.new("RGB", (6 * cell, 5 * cell), (60, 60, 70))
        dr = ImageDraw.Draw(sheet)
        for j, e in enumerate(chunk):
            x, y = (j % 6) * cell, (j // 6) * cell
            tile = Image.new("RGBA", (128, 128), (255, 255, 255, 255) if e["bg"] == "light" else (26, 26, 26, 255))
            lg = Image.open(OUT / f"{e['id']}.webp").convert("RGBA").resize((128, 128), Image.LANCZOS)
            tile.alpha_composite(lg)
            sheet.paste(tile.convert("RGB"), (x + 16, y + 6))
            dr.text((x + 8, y + 140), f"{e['id']} | {e['name']}"[:26], fill=(255, 255, 255))
        sheet.save(SHEETS / f"sheet_{i // per:02d}.png")
    bad = {k: v["issues"] for k, v in report.items() if v["issues"]}
    print(len(data), "logos;", len(bad), "flagged")
    for k, v in bad.items():
        print(" ", k, v)


if __name__ == "__main__":
    main()
