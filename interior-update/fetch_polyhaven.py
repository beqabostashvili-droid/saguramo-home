"""Download the CC0 Poly Haven assets used by the realistic interior.

  python interior-update/fetch_polyhaven.py

Files go to assets/polyhaven/<asset>/ (git-ignored). Already present files
are skipped. Licence: CC0 (https://polyhaven.com/license).
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "polyhaven")
UA = {"User-Agent": "saguramo-home-render/1.0"}

HDRIS = {"alps_field": "4k"}
TEXTURES = {  # asset: resolution
    "laminate_floor_02": "2k", "beige_wall_001": "2k", "white_oak_veneer": "2k",
    "oak_veneer_01": "2k", "marble_01": "2k", "rough_linen": "2k", "wool_boucle": "2k",
    "plastered_wall_04": "2k",
}
TEX_MAPS = ["Diffuse", "nor_gl", "Rough"]
MODELS = {
    "modern_arm_chair_01": "2k", "potted_plant_02": "2k", "modern_wooden_cabinet": "2k",
    "ceramic_vase_01": "1k", "ceramic_vase_03": "1k", "coffee_table_round_01": "2k",
    "modern_ceiling_lamp_01": "1k",
}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return 0
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dest)
    return os.path.getsize(dest)


total = 0
for a, res in HDRIS.items():
    info = get_json(f"https://api.polyhaven.com/files/{a}")
    total += fetch(info["hdri"][res]["hdr"]["url"], os.path.join(ROOT, a, f"{a}_{res}.hdr"))
for a, res in TEXTURES.items():
    info = get_json(f"https://api.polyhaven.com/files/{a}")
    for m in TEX_MAPS:
        if m in info:
            u = info[m][res]["jpg"]["url"] if "jpg" in info[m][res] else info[m][res]["png"]["url"]
            total += fetch(u, os.path.join(ROOT, a, os.path.basename(u)))
for a, res in MODELS.items():
    info = get_json(f"https://api.polyhaven.com/files/{a}")
    g = info["gltf"][res]["gltf"]
    total += fetch(g["url"], os.path.join(ROOT, a, os.path.basename(g["url"])))
    for rel, inc in g.get("include", {}).items():
        total += fetch(inc["url"], os.path.join(ROOT, a, rel))
    print("model", a, flush=True)
print(f"DONE {total / 1e6:.1f} MB downloaded into {ROOT}")
sys.exit(0)
