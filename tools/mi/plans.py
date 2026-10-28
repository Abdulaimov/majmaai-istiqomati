"""Outlines of block К from the architect's plan sheets -> build/plan_K.json (block metres).

    tools/ab/py tools/mi/plans.py

Sheets (client PDF): 23 = floor 1, 29 = floor 2, 32 = typical floor (shared by Б, В, Г, К).
Plan scale from the grid axes: 7 500 mm = 136.2 pt -> 18.165 pt per metre.
Block metres: x along the block from its middle, + towards the south-east end (the podium's rounded
end, right on the sheets), y across, + towards the north-east (the inner street: top of sheets 23/29,
the bottom of sheet 32, which is drawn mirrored: its lift core sits at the top, on 23 at the bottom).
The tower (typical floor, 36.8 m) is centred on x = 0; axis 1 (the north-west end) is x = -18.4.
"""
import json
import os

import cv2
import numpy as np
import pymupdf
from shapely.geometry import Polygon

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PDF = os.path.join(ROOT, '..', '00_Материалы_клиента', 'Мачмааи истикомати.pdf')
PT_PER_M = 136.2 / 7.5
WALL = (189, 168, 136)
COLUMN = (123, 101, 68)
FLOORS = [(236, 220, 204), (243, 243, 243), (61, 173, 153), (232, 232, 232), (255, 255, 255), (234, 230, 227),
          (182, 165, 148), (255, 119, 119), (247, 224, 70), (104, 179, 83), (238, 238, 238)]

# per sheet: axis 1 x (pt), the middle between the outer y axes (pt), mirrored (sheet 32)
SHEETS = {23: dict(ax1=100.9, ymid=(223.9 + 569.1) / 2, flip=False, clip=(60, 150, 1000, 640)),
          29: dict(ax1=101.3, ymid=(214.8 + 560.1) / 2, flip=False, clip=(60, 140, 1000, 630)),
          32: dict(ax1=227.8 - 1.7 * 0 , ymid=(91.2 + 436.4) / 2, flip=True, clip=(180, 40, 920, 490))}
PX = 20  # raster px per metre


def rings(x):
    out, cur = [], []
    for it in x['items']:
        if it[0] == 're':
            r = it[1]
            out.append([(r.x0, r.y0), (r.x1, r.y0), (r.x1, r.y1), (r.x0, r.y1)])
            continue
        if it[0] == 'qu':
            q = it[1]
            out.append([(q.ul.x, q.ul.y), (q.ur.x, q.ur.y), (q.lr.x, q.lr.y), (q.ll.x, q.ll.y)])
            continue
        if it[0] == 'l':
            a, b = it[1], it[2]
            seg = [(a.x, a.y), (b.x, b.y)]
        elif it[0] == 'c':
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]
            seg = [(p0.x, p0.y)] + [((p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3).x,
                                     (p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3).y)
                                    for t in (0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)]
        else:
            continue
        if cur and abs(cur[-1][0] - seg[0][0]) + abs(cur[-1][1] - seg[0][1]) > 0.05:
            out.append(cur)
            cur = []
        cur += seg if not cur else seg[1:]
    if cur:
        out.append(cur)
    return [r for r in out if len(r) >= 3]


def outline(page, s):
    """Outer outline of the floor: walls, columns and floor fills rasterised, holes closed."""
    x0, y0, x1, y1 = s['clip']
    k = PX / PT_PER_M
    W, H = int((x1 - x0) * k), int((y1 - y0) * k)
    m = np.zeros((H, W), np.uint8)
    for x in page.get_drawings():
        f = x.get('fill')
        if not f:
            continue
        c = tuple(round(v * 255) for v in f)
        if c not in [WALL, COLUMN] + FLOORS:
            continue
        for r in rings(x):
            cv2.fillPoly(m, [np.array([[(p[0] - x0) * k, (p[1] - y0) * k] for p in r], np.int32)], 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 0.06 * PX, True)[:, 0, :]

    def to_m(p):
        X = (p[0] / k + x0 - s['ax1']) / PT_PER_M - 18.4
        Y = -((p[1] / k + y0) - s['ymid']) / PT_PER_M
        return [round(X, 3), round(-Y if s['flip'] else Y, 3)]

    ring = [to_m(p) for p in c]
    g = Polygon(ring).buffer(0)
    return ring, g


def walls(page, s):
    """Wall and column pieces (block metres): where the outer wall is solid, the rest is glazing."""
    x0, y0, x1, y1 = s['clip']
    out = []
    for x in page.get_drawings():
        f = x.get('fill')
        if not f or tuple(round(v * 255) for v in f) not in (WALL, COLUMN):
            continue
        for r in rings(x):
            pts = [[round((p[0] - s['ax1']) / PT_PER_M - 18.4, 3),
                    round((1 if s['flip'] else -1) * (p[1] - s['ymid']) / PT_PER_M, 3)] for p in r]
            if Polygon(pts).buffer(0).area > 0.01:
                out.append(pts)
    return out


def main():
    doc = pymupdf.open(PDF)
    res = {}
    for n, s in SHEETS.items():
        ring, g = outline(doc[n - 1], s)
        b = g.bounds
        res[n] = dict(outline=ring, walls=walls(doc[n - 1], s), bounds=[round(v, 2) for v in b], area=round(g.area, 1))
        print(n, 'bounds', [round(v, 2) for v in b], 'area', round(g.area, 1), 'pts', len(ring))
    with open(os.path.join(ROOT, 'build', 'plan_K.json'), 'w') as f:
        json.dump(res, f)


if __name__ == '__main__':
    main()
