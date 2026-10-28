"""Genplan (sheet 2 of the client's PDF) -> site plan in metres.

    tools/ab/py tools/mi/genplan.py          # -> build/genplan.json, build/genplan_classes.png

The sheet is an Archicad vector drawing: every area is a filled path of its legend colour, so each
class is rasterised from its own paths (even-odd, 10 px per metre), cleaned and traced back into
polygons. Scale: the blocks are drawn 35.93 pt deep, and all of them are 22.4 m deep on the plans.
Site metres: x east (right on the sheet), y north (up, the sheet's north arrow points up), origin
at the middle of block К (the first block that is built in full).
"""
import json
import math
import os
import sys

import cv2
import numpy as np
import pymupdf
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PDF = os.path.join(ROOT, '..', '00_Материалы_клиента', 'Мачмааи истикомати.pdf')
M_PER_PT = 22.4 / 35.935
PX_PER_M = 10.0
CLIP = (60, 20, 680, 820)          # sheet region of the site (pt)

# legend colour (RGB 0-255, fill opacity) -> class; the order is the paint order (later wins)
CLASSES = [
    ('paving', [((215, 207, 189), 1.0)]),
    ('podium', [((211, 200, 184), 1.0)]),
    ('asphalt', [((127, 127, 127), 0.75)]),
    ('path', [((202, 194, 181), 1.0), ((235, 230, 211), 1.0), ((214, 205, 167), 1.0)]),
    ('lawn', [((115, 166, 38), 1.0), ((124, 191, 51), 1.0)]),
    ('lawn_rest', [((132, 169, 41), 1.0), ((91, 131, 17), 1.0)]),
    ('play', [((231, 215, 118), 1.0), ((247, 224, 70), 0.5)]),
    ('court', [((228, 80, 6), 1.0), ((96, 225, 160), 1.0), ((91, 168, 216), 1.0), ((183, 217, 255), 1.0)]),
    ('stall', [((138, 138, 138), 1.0)]),
    ('existing', [((0, 128, 128), 0.25)]),
    ('block', [((76, 136, 165), 1.0)]),
    ('kinder', [((174, 101, 55), 1.0)]),
    ('studio', [((61, 173, 153), 1.0)]),
    ('admin', [((242, 163, 64), 1.0)]),
    ('transformer', [((192, 160, 160), 1.0)]),
    ('waste', [((131, 77, 175), 1.0)]),
]
DEBUG = dict(podium=(205, 185, 160), paving=(222, 212, 196), asphalt=(110, 110, 112), path=(200, 190, 175), lawn=(95, 150, 50),
             lawn_rest=(60, 110, 30), play=(240, 210, 90), court=(230, 90, 40), stall=(80, 80, 80),
             existing=(150, 200, 200), block=(60, 110, 150), kinder=(160, 90, 50), studio=(40, 160, 140),
             admin=(240, 160, 60), transformer=(190, 150, 150), waste=(130, 70, 170))


def key_of(x):
    f = x.get('fill')
    if f is None:
        return None
    return tuple(round(v * 255) for v in f), round(x.get('fill_opacity') or 1.0, 2)


def subpaths(x):
    """The path's closed rings (pt): items run on while each starts where the last ended."""
    rings, cur = [], []
    for it in x['items']:
        if it[0] == 're':
            r = it[1]
            rings.append([r.tl, r.tr, r.br, r.bl])
            continue
        if it[0] == 'qu':
            q = it[1]
            rings.append([q.ul, q.ur, q.lr, q.ll])
            continue
        if it[0] == 'l':
            a, b = it[1], it[2]
            seg = [a, b]
        elif it[0] == 'c':
            a, b = it[1], it[4]
            seg = [it[1]] + [it[1] * (1 - t) ** 3 + it[2] * 3 * t * (1 - t) ** 2 + it[3] * 3 * t * t * (1 - t) + it[4] * t ** 3
                             for t in (0.25, 0.5, 0.75, 1.0)]
        else:
            continue
        if cur and abs(cur[-1].x - a.x) + abs(cur[-1].y - a.y) > 0.05:
            rings.append(cur)
            cur = []
        cur += seg if not cur else seg[1:]
    if cur:
        rings.append(cur)
    return [r for r in rings if len(r) >= 3]


def main():
    doc = pymupdf.open(PDF)
    page = doc[1]
    drawings = page.get_drawings()
    words = page.get_text('words')
    x0, y0, x1, y1 = CLIP
    W, H = int((x1 - x0) * M_PER_PT * PX_PER_M), int((y1 - y0) * M_PER_PT * PX_PER_M)
    k = M_PER_PT * PX_PER_M

    def px(p):
        return [int(round((p.x - x0) * k)), int(round((p.y - y0) * k))]

    by_key = {}
    for x in drawings:
        kk = key_of(x)
        if kk:
            by_key.setdefault(kk, []).append(x)

    # blocks: one path each; the letter written inside names it
    blocks = {}
    for x in by_key.get(((76, 136, 165), 1.0), []):
        r = x['rect']
        letters = [w[4] for w in words if r.x0 < (w[0] + w[2]) / 2 < r.x1 and r.y0 < (w[1] + w[3]) / 2 < r.y1
                   and len(w[4]) == 1 and w[4].isalpha() and w[4].isupper()]
        heights = [w[4] for w in words if r.x0 < (w[0] + w[2]) / 2 < r.x1 and r.y0 < (w[1] + w[3]) / 2 < r.y1
                   and '/' in w[4] and w[4].replace('/', '').isdigit()]
        if not letters:
            continue
        pts = [p for ring in subpaths(x) for p in ring]
        blocks[letters[-1]] = dict(pt=[(p.x, p.y) for p in pts], label=heights[-1] if heights else None)

    # site frame: origin at the middle of block К
    kc = MultiPoint(blocks['К']['pt']).minimum_rotated_rectangle.centroid
    OX, OY = kc.x, kc.y

    def to_m(p):
        return (round((p[0] - OX) * M_PER_PT, 3), round(-(p[1] - OY) * M_PER_PT, 3))

    def px_to_m(c):
        return (round((c[0] / k + x0 - OX) * M_PER_PT, 3), round(-((c[1] / k + y0) - OY) * M_PER_PT, 3))

    out_blocks = {}
    for letter, b in blocks.items():
        rect = MultiPoint([to_m(p) for p in b['pt']]).minimum_rotated_rectangle
        c = list(rect.exterior.coords)[:4]
        e = [(c[(i + 1) % 4][0] - c[i][0], c[(i + 1) % 4][1] - c[i][1]) for i in range(4)]
        i = max(range(4), key=lambda j: math.hypot(*e[j]))
        L, Wd = math.hypot(*e[i]), math.hypot(*e[(i + 1) % 4])
        rot = math.degrees(math.atan2(e[i][1], e[i][0])) % 180.0
        floors = [int(v) for v in b['label'].split('/')] if b['label'] else None
        out_blocks[letter] = dict(centre=[round(rect.centroid.x, 3), round(rect.centroid.y, 3)], length=round(L, 2),
                                  width=round(Wd, 2), rot=round(rot, 2), label=b['label'], floors=floors,
                                  ring=[list(q) for q in c])

    # every class rasterised from its own paths, even-odd within a path
    masks = {}
    for name, keys in CLASSES:
        m = np.zeros((H, W), np.uint8)
        for kk in keys:
            for x in by_key.get(kk, []):
                one = np.zeros((H, W), np.uint8)
                for ring in subpaths(x):
                    t = np.zeros((H, W), np.uint8)
                    cv2.fillPoly(t, [np.array([px(p) for p in ring], np.int32)], 1)
                    one ^= t
                m |= one
        masks[name] = m

    # paint order: the later class wins
    lab = np.zeros((H, W), np.uint8)
    for i, (name, _) in enumerate(CLASSES):
        lab[masks[name] > 0] = i + 1
    dbg = np.full((H, W, 3), 255, np.uint8)
    for i, (name, _) in enumerate(CLASSES):
        dbg[lab == i + 1] = DEBUG[name]

    classes = {}
    for i, (name, _) in enumerate(CLASSES):
        m = (lab == i + 1).astype(np.uint8)
        if name in ('lawn', 'paving', 'path', 'asphalt'):
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        polys = []
        if hier is None:
            classes[name] = []
            continue
        for j, c in enumerate(cs):
            if hier[0][j][3] != -1 or len(c) < 3:
                continue
            ring = [px_to_m(q[0]) for q in cv2.approxPolyDP(c, 1.2, True)]
            holes = []
            ch = hier[0][j][2]
            while ch != -1:
                if len(cs[ch]) >= 3 and cv2.contourArea(cs[ch]) > 20:
                    holes.append([px_to_m(q[0]) for q in cv2.approxPolyDP(cs[ch], 1.2, True)])
                ch = hier[0][ch][0]
            if len(ring) < 3:
                continue
            g = Polygon(ring, [h for h in holes if len(h) >= 3]).buffer(0)
            if g.area < (0.5 if name == 'stall' else 2.0):
                continue
            polys.append(dict(ring=[list(p) for p in ring], holes=[[list(p) for p in h] for h in holes if len(h) >= 3],
                              area=round(g.area, 1)))
        classes[name] = polys

    # the existing buildings' storeys: the number written on them ("2КН", "16 ЮК", "3 КЖ"...)
    from shapely.geometry import Point
    for q in classes['existing']:
        g = Polygon(q['ring']).buffer(0)
        best = None
        for w in words:
            cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
            m = __import__('re').match(r'^(\d{1,2})', w[4])
            if not m or '.' in w[4] or len(w[4]) > 8:
                continue
            if g.buffer(1.0).contains(Point(to_m((cx, cy)))):
                best = int(m.group(1))
        q['floors'] = best

    # labels kept for landmarks (numbers of storeys on the side buildings, street names)
    keep = []
    for w in words:
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        if not (x0 < cx < x1 and y0 < cy < y1):
            continue
        t = w[4]
        if t in ('3', '6', 'ТП') or 'Кучаи' in t or 'Зехни' in t:
            keep.append(dict(t=t, p=list(to_m((cx, cy))), h=round((w[3] - w[1]) * M_PER_PT, 2)))

    res = dict(m_per_pt=M_PER_PT, origin_pt=[OX, OY], blocks=out_blocks, classes=classes, words=keep)
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    with open(os.path.join(ROOT, 'build', 'genplan.json'), 'w') as f:
        json.dump(res, f, ensure_ascii=False)
    cv2.imwrite(os.path.join(ROOT, 'build', 'genplan_classes.png'), cv2.cvtColor(dbg, cv2.COLOR_RGB2BGR))
    for l, b in sorted(out_blocks.items()):
        print(l, b['label'], b['length'], 'x', b['width'], 'rot', b['rot'], 'at', b['centre'])
    print({n: len(v) for n, v in classes.items()})


if __name__ == '__main__':
    main()
