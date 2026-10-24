"""Collecte la bibliothèque de memes visuels du jeu MDR.

Sources (API publiques, sans clé, prévues pour être utilisées par des applications) :
  - Imgflip       https://api.imgflip.com/get_memes        (100 modèles les plus populaires)
  - memegen.link  https://api.memegen.link/templates       (catalogue complet)
  - Memeboat      https://memebo.at/api/templates?search=  (recherche dans 25 000+ modèles)

Pour chaque image retenue, le script vérifie réellement le fichier servi (statut HTTP, type,
décodage, dimensions), calcule une empreinte SHA-256 et une empreinte perceptuelle (pHash)
pour écarter les doublons (y compris la même image sous deux noms), puis produit :
  - jeu/data/memes.json                  la bibliothèque utilisée par le jeu
  - server/memes/report/rapport.json     le bilan chiffré, sources et rejets
  - server/memes/report/planche-XX.jpg   des planches contact numérotées pour la vérification visuelle

Usage : python server/memes/collect.py   (réseau requis ; exécuté par .github/workflows/memes-import.yml)
"""
import difflib
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import imagehash
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
REPORT = HERE / "report"
OUT = ROOT / "jeu" / "data" / "memes.json"
UA = {"User-Agent": "MDR-jeu-de-memes/1.0 (+https://lenarofe25-coder.github.io/jeu/)"}
session = requests.Session()
session.headers.update(UA)

PRIORITY = {"imgflip": 0, "memegen": 1, "memeboat": 2}
SOURCE_INFO = {
    "imgflip": {"name": "Imgflip", "api": "https://api.imgflip.com/get_memes", "terms": "https://imgflip.com/terms"},
    "memegen": {"name": "memegen.link", "api": "https://api.memegen.link/templates", "terms": "https://github.com/jacebrowning/memegen"},
    "memeboat": {"name": "Memeboat", "api": "https://memebo.at/api/templates", "terms": "https://memebo.at/terms"},
}
PHASH_DUP = 8  # distance de Hamming en dessous de laquelle deux images sont la même image


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(meme|template|the|a|an)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def similarity(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    cover = len(ta & tb) / max(1, len(ta))  # part des mots recherchés présents
    return max(ratio, 0.9 * cover if len(ta) > 1 else 0)


def get_json(url, **kw):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=30, **kw)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {err}")


def first_list(data):
    if isinstance(data, list):
        return data
    for key in ("templates", "data", "results", "items"):
        v = data.get(key) if isinstance(data, dict) else None
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            inner = first_list(v)
            if inner:
                return inner
    return []


def pick(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k):
            return d[k]
    return None


def load_catalogs(log):
    cands = []
    data = get_json("https://api.imgflip.com/get_memes")
    for m in data["data"]["memes"]:
        cands.append({"src": "imgflip", "name": m["name"], "image": m["url"], "page": f"https://imgflip.com/meme/{m['id']}", "key": f"imgflip:{m['id']}"})
    log["imgflip"] = len(data["data"]["memes"])
    rows = get_json("https://api.memegen.link/templates")
    for t in rows:
        image = t.get("blank") or f"https://api.memegen.link/images/{t['id']}.png"
        cands.append({"src": "memegen", "name": t["name"], "image": image, "page": t.get("source") or f"https://memegen.link/#{t['id']}", "key": f"memegen:{t['id']}"})
    log["memegen"] = len(rows)
    return cands


def memeboat_search(query, log):
    try:
        data = get_json("https://memebo.at/api/templates", params={"search": query, "limit": 5, "page": 1})
    except RuntimeError as e:
        log.setdefault("memeboat_errors", []).append(str(e)[:200])
        return []
    if "memeboat_sample" not in log:
        log["memeboat_sample"] = json.dumps(data)[:1500]
    out = []
    for t in first_list(data):
        name = pick(t, "name", "title")
        image = pick(t, "imageUrl", "image_url", "image", "url", "templateUrl", "src")
        slug = pick(t, "slug", "id")
        if isinstance(image, dict):
            image = pick(image, "url", "src")
        if not (name and image and isinstance(image, str)):
            continue
        if image.startswith("/"):
            image = "https://memebo.at" + image
        out.append({"src": "memeboat", "name": name, "image": image, "page": f"https://memebo.at/templates/{slug}" if slug else "https://memebo.at/templates", "key": f"memeboat:{slug or image}"})
    return out


def fetch_image(url):
    r = session.get(url, timeout=40)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    ctype = r.headers.get("content-type", "")
    if not ctype.startswith("image/"):
        return None, f"type {ctype or 'inconnu'}"
    try:
        img = Image.open(io.BytesIO(r.content))
        img.load()
    except Exception as e:  # noqa: BLE001
        return None, f"illisible ({e.__class__.__name__})"
    if min(img.size) < 150:
        return None, f"trop petite {img.size}"
    return (r.content, img), None


def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(name) or "meme")).strip("-")[:48]


def contact_sheets(items):
    REPORT.mkdir(parents=True, exist_ok=True)
    for f in REPORT.glob("planche-*.jpg"):
        f.unlink()
    per, cols, cell, label = 30, 6, 210, 34
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    for s in range(0, len(items), per):
        chunk = items[s : s + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, rows * (cell + label)), "white")
        draw = ImageDraw.Draw(sheet)
        for i, it in enumerate(chunk):
            x, y = (i % cols) * cell, (i // cols) * (cell + label)
            th = it["_img"].convert("RGB")
            th.thumbnail((cell - 10, cell - 10))
            sheet.paste(th, (x + (cell - th.width) // 2, y + (cell - th.height) // 2))
            draw.text((x + 4, y + cell + 2), f"{s + i + 1}. {it['name'][:26]}", fill="black", font=font)
        sheet.save(REPORT / f"planche-{s // per + 1:02d}.jpg", quality=72)


def main():
    log = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    wanted = [l.strip() for l in (HERE / "wanted.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    rejected_ids = {l.split("#")[0].strip() for l in (HERE / "rejected.txt").read_text().splitlines()} if (HERE / "rejected.txt").exists() else set()
    rejected_ids.discard("")
    catalog = load_catalogs(log)

    # 1. Candidats : tout Imgflip et memegen (catalogues de modèles de memes), plus la meilleure
    #    correspondance de chaque nom recherché (Memeboat si les deux premiers ne l'ont pas).
    chosen = {c["key"]: dict(c, wanted=None) for c in catalog}
    misses = []
    for w in wanted:
        best = max(catalog, key=lambda c: similarity(w, c["name"]))
        if similarity(w, best["name"]) >= 0.86:
            chosen[best["key"]]["wanted"] = w
            continue
        results = memeboat_search(w, log)
        time.sleep(0.35)
        scored = sorted(results, key=lambda c: -similarity(w, c["name"]))
        if scored and similarity(w, scored[0]["name"]) >= 0.6:
            c = scored[0]
            chosen.setdefault(c["key"], dict(c, wanted=w))
        else:
            misses.append({"wanted": w, "best": scored[0]["name"] if scored else None})

    # 2. Vérification réelle de chaque image et déduplication (identique ou quasi identique).
    ordered = sorted(chosen.values(), key=lambda c: PRIORITY[c["src"]])
    kept, rejects = [], []
    for c in ordered:
        res, err = fetch_image(c["image"])
        time.sleep(0.15)
        if err:
            rejects.append({"name": c["name"], "source": c["src"], "image": c["image"], "reason": err})
            continue
        content, img = res
        sha = hashlib.sha256(content).hexdigest()
        ph = imagehash.phash(img.convert("RGB"))
        dup = next((k for k in kept if k["sha256"] == sha or (k["_ph"] - ph) <= PHASH_DUP), None)
        if dup:
            dup["aka"].append(c["name"])
            rejects.append({"name": c["name"], "source": c["src"], "image": c["image"], "reason": f"doublon de « {dup['name']} »"})
            continue
        kept.append({**c, "sha256": sha, "_ph": ph, "_img": img, "width": img.width, "height": img.height, "aka": []})

    # 3. Identifiants stables (conservés d'une collecte à l'autre) et rejets manuels.
    previous = {m["sourceKey"]: m["id"] for m in json.loads(OUT.read_text())["memes"]} if OUT.exists() else {}
    used = set(previous.values())
    memes = []
    for k in kept:
        mid = previous.get(k["key"])
        if not mid:
            base = "m-" + slugify(k["name"])
            mid, n = base, 2
            while mid in used:
                mid, n = f"{base}-{n}", n + 1
            used.add(mid)
        k["id"] = mid
        info = SOURCE_INFO[k["src"]]
        memes.append({
            "id": mid,
            "name": k["name"],
            "image": k["image"],
            "width": k["width"],
            "height": k["height"],
            "aka": k["aka"],
            "source": {"name": info["name"], "page": k["page"], "api": info["api"], "terms": info["terms"]},
            "rights": "Image protégée par le droit d'auteur de ses ayants droit ; affichée depuis le serveur de la source via son API publique, sans copie ni redistribution par MDR.",
            "sha256": k["sha256"],
            "phash": str(k["_ph"]),
            "sourceKey": k["key"],
            "active": mid not in rejected_ids,
        })
    contact_sheets([dict(k, name=m["id"] if m["active"] else f"[REJETÉ] {m['id']}") for k, m in zip(kept, memes)])

    active = [m for m in memes if m["active"]]
    OUT.write_text(json.dumps({"version": time.strftime("%Y-%m-%d"), "count": len(active), "memes": memes}, ensure_ascii=False, indent=1) + "\n")
    summary = {
        **log,
        "wanted": len(wanted),
        "candidates": len(chosen),
        "verified_unique": len(memes),
        "active": len(active),
        "manually_rejected": len(memes) - len(active),
        "by_source": {s: sum(1 for m in active if m["sourceKey"].startswith(s)) for s in PRIORITY},
        "rejected": rejects,
        "not_found": misses,
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "rapport.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("rejected", "not_found", "memeboat_sample")}, ensure_ascii=False, indent=1))
    print(f"Images rejetées : {len(rejects)} ; noms introuvables : {len(misses)}")


if __name__ == "__main__":
    sys.exit(main())
