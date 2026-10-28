"""The site from the genplan (build/genplan.json, read off the drawing's vectors by tools/mi/genplan.py):
roads, paving, paths, lawns behind kerbs, playgrounds, the courts, the car parks with their bays;
the existing houses round the plot; lamps, benches, trees, cars and people for the viewer.

Levels: roads at 0, paving and paths +0.12, lawns +0.15 behind a kerb, play surfaces +0.13.
"""
import math
import random

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from ab import landscape as LS
from ab.site import bench, kerb_line, lamp, mulch, raised
from complex import geom
from complex.geom import MeshBuilder, make_object, resample, ring_coords

from . import massing

Z = dict(asphalt=0.0, paving=0.12, path=0.12, lawn=0.15, play=0.13)


def polys(gp, cls):
    out = []
    for p in gp['classes'].get(cls, []):
        g = Polygon(p['ring'], [h for h in p['holes'] if len(h) >= 3]).buffer(0)
        if not g.is_empty:
            out.append(g)
    return out


def parts(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    return [q for q in getattr(g, 'geoms', []) if q.geom_type == 'Polygon']


def rect_axes(g):
    r = g.minimum_rotated_rectangle
    c = list(r.exterior.coords)[:4]
    e = [(c[(i + 1) % 4][0] - c[i][0], c[(i + 1) % 4][1] - c[i][1]) for i in range(4)]
    i = max(range(4), key=lambda j: math.hypot(*e[j]))
    L, W = math.hypot(*e[i]), math.hypot(*e[(i + 1) % 4])
    return r, L, W, (e[i][0] / L, e[i][1] / L)


def build_site(mats, col, gp, built, avoid_trees):
    """built: the footprints of the blocks and their podiums (site metres); avoid_trees: where no
    tree may stand (the blocks with a margin)."""
    LS.walk_reset()
    rnd = random.Random(20261027)
    C = {k: unary_union(polys(gp, k)) for k in gp['classes']}
    allg = unary_union([g for g in C.values() if not g.is_empty])
    x0, y0, x1, y1 = allg.bounds
    REGION = box(x0 - 30, y0 - 30, x1 + 30, y1 + 30)

    court = C['court'].buffer(0.3).buffer(-0.3)
    play = C['play'].difference(court)
    lawn = unary_union([C['lawn'], C['lawn_rest']]).difference(court).difference(play)
    path = C['path'].difference(lawn).difference(play).difference(court)
    paving = unary_union([C['paving'], C['podium'], C['block'], C['kinder'], C['studio'], C['admin'],
                          C['transformer'], C['waste']]).difference(unary_union([lawn, path, play, court]))
    stalls = C['stall']
    asphalt = C['asphalt'].difference(unary_union([lawn, path, paving, play, court]))
    # the plot's ground under the blocks (their shops reach the paving) and the small gaps
    # between the genplan's areas: paving
    filled = unary_union([asphalt, lawn, path, paving, play, court, stalls])
    gaps = allg.buffer(0.4).buffer(-0.4).difference(filled)
    small = [q for q in parts(gaps) if q.area < 30]
    if small:
        paving = unary_union([paving] + [q.buffer(0.02) for q in small])

    mb = MeshBuilder()
    mb.polygon_face(box(-1600, -1600, 1600, 1600).difference(REGION.buffer(-0.5)), -0.06, 'Ground')
    mb.polygon_face(REGION.buffer(-0.5).difference(filled.buffer(0.05)), -0.04, 'Ground')
    for q in parts(asphalt.union(stalls)):
        mb.polygon_face(q, 0.0, 'Asphalt')
    raised(mb, paving.buffer(0.03), Z['paving'], 'Paving', 'Kerb')
    raised(mb, path, Z['path'] + 0.005, 'Sidewalk', 'Kerb')
    raised(mb, lawn, Z['lawn'], 'Lawn', 'Kerb')
    kerb_line(mb, lawn, Z['lawn'] - 0.02, 0.12, 0.08)
    for i, q in enumerate(parts(play)):
        raised(mb, q, Z['play'], 'Rubber orange' if i % 2 == 0 else 'Rubber yellow', 'Kerb')
    for q in parts(court):
        raised(mb, q, Z['play'], 'Court blue', 'Kerb')
        r, L, W, d = rect_axes(q)
        mb.tube(ring_coords(r.buffer(-0.6, join_style='mitre')), [Z['play'] + 0.01] * 4, [Z['play'] + 0.02] * 4, 0.08, 'Road line', closed=True)
    sm = mb.to_mesh('Ground', mats)
    make_object('Ground', sm, col)

    # car parks: the bays the genplan draws along the inner street, white lines, cars in most
    mb = MeshBuilder()
    cars, people, benches, labels = [], [], [], []
    for q in parts(stalls):
        if q.area < 8:
            continue
        r, L, W, d = rect_axes(q)
        n = (-d[1], d[0])
        c = r.centroid
        k = int(L // 2.5)
        s0 = -k * 2.5 / 2
        rot = math.atan2(n[1], n[0])
        for i in range(k + 1):
            s = s0 + i * 2.5
            a = (c.x + d[0] * s - n[0] * W / 2, c.y + d[1] * s - n[1] * W / 2)
            b = (c.x + d[0] * s + n[0] * W / 2, c.y + d[1] * s + n[1] * W / 2)
            mb.tube([a, b], [0.005, 0.005], [0.012, 0.012], 0.1, 'Road line')
            if i < k and rnd.random() < 0.72:
                p = (c.x + d[0] * (s + 1.25), c.y + d[1] * (s + 1.25))
                cars.append([round(p[0], 2), round(p[1], 2), 0.0, round(rot + (math.pi if rnd.random() < 0.5 else 0), 3), rnd.randrange(8)])

    # the existing houses round the plot (their storeys written on the genplan), the kindergarten,
    # the television studio and the offices of the genplan as white models of their size
    paints = ['Neighbour cream', 'Neighbour peach', 'Neighbour blue', 'Neighbour solid', 'Neighbour mint', 'Neighbour rose']
    for i, p in enumerate(gp['classes']['existing']):
        f = p.get('floors') or 3
        f = 3 if f <= 0 else min(f, 18)
        massing.neighbour(mb, p['ring'], f, paints[i % len(paints)])
    named = [('kinder', 3, 3.6, 'Детский сад', 'Боғчаи кӯдакон'), ('studio', 3, 4.2, 'Телестудия', 'Телестудия'),
             ('admin', 6, 3.3, 'Административное здание', 'Бинои маъмурӣ')]
    for cls, floors, step, ru, tj in named:
        for g in parts(C[cls]):
            if g.area < 300:
                continue
            top = massing.building(mb, list(g.exterior.coords)[:-1], floors, step)
            c = g.centroid
            labels.append(dict(x=round(c.x, 2), y=round(c.y, 2), z=round(top + 2, 1), ru=ru, tj=tj, kind=cls))
    for cls in ('transformer', 'waste'):
        for g in parts(C[cls]):
            mb.prism(g.buffer(-0.1), Z['paving'], 2.6 if cls == 'transformer' else 1.8, 'Massing', 'Massing roof')
    sm = mb.to_mesh('Site props', mats)
    make_object('Site props', sm, col)

    # lamps along the paths and pavements (one per 16 m), benches by the lawns (one per 11 m)
    mb = MeshBuilder()
    lamps_at, bench_at = [], []

    def spaced(lst, p, gap):
        if any(math.dist(p, q) < gap for q in lst):
            return False
        lst.append(p)
        return True
    # the other buildings of the genplan stand on its paving: nothing is put in them
    houses = unary_union([C[k] for k in ('existing', 'kinder', 'studio', 'admin', 'transformer', 'waste')])
    no = unary_union([built.buffer(2.0), houses.buffer(1.0)])
    walkable = unary_union([paving, path]).difference(houses.buffer(0.5))
    inner = walkable.buffer(-0.05)
    for q in parts(lawn):
        if q.area < 25:
            continue
        ext = q.exterior
        ring = ring_coords(q.buffer(0.5, join_style='mitre')) if q.buffer(0.5).geom_type == 'Polygon' else ring_coords(q)
        for p in resample(ring, 8.0):
            P = Point(p)
            if no.contains(P) or not walkable.buffer(-0.2).contains(P):
                continue
            if spaced(lamps_at, p, 16.0):
                lamp(mb, p[0], p[1], Z['paving'], 4.2)
                continue
            if q.area <= 60 or any(math.dist(p, l) < 3 for l in lamps_at) or any(math.dist(p, b) < 11.0 for b in bench_at):
                continue
            # along the lawn's edge, seat to the path, back to the lawn (bench(): the backrest on
            # its +y side), 0.45 m off the kerb; the whole seat and 1.5 m in front of it on paving
            sd = ext.project(P)
            e0, e1, e = ext.interpolate(sd - 0.6), ext.interpolate(sd + 0.6), ext.interpolate(sd)
            rot = math.atan2(e1.y - e0.y, e1.x - e0.x)
            out = (P.x - e.x, P.y - e.y)
            if (-math.sin(rot)) * out[0] + math.cos(rot) * out[1] > 0:
                rot += math.pi
            n = math.hypot(*out) or 1.0
            c = (e.x + out[0] / n * 0.75, e.y + out[1] / n * 0.75)
            seat = affinity.rotate(box(c[0] - 0.95, c[1] - 0.3, c[0] + 0.95, c[1] + 0.3), rot, origin=c, use_radians=True)
            front = Point(c[0] + out[0] / n * 1.4, c[1] + out[1] / n * 1.4).buffer(0.55)
            if not inner.contains(seat) or not inner.contains(front) or front.intersects(no):
                continue
            bench_at.append(c)
            bench(mb, c[0], c[1], Z['paving'], rot)
            benches.append([round(c[0], 2), round(c[1], 2), round(rot, 3)])
    # street lamps along the roads
    for q in parts(asphalt):
        if q.area < 400:
            continue
        for p in resample(ring_coords(q.buffer(-0.5)) if q.buffer(-0.5).geom_type == 'Polygon' else ring_coords(q), 30.0):
            P = Point(p)
            nb = q.exterior.interpolate(q.exterior.project(P))
            rot = math.atan2(P.y - nb.y, P.x - nb.x)
            o = (nb.x - math.cos(rot) * 0.9, nb.y - math.sin(rot) * 0.9)
            if no.contains(Point(o)) or stalls.buffer(1.0).contains(Point(o)):
                continue
            if spaced(lamps_at, o, 26.0):
                lamp(mb, o[0], o[1], Z['paving'], 8.0, street=True, rot=rot)
    sm = mb.to_mesh('Lamps', mats)
    make_object('Lamps', sm, col)

    # trees: avenues along the strips of lawn by the streets (pines along the inner street, as on
    # renders 9 and 10), groves on the larger lawns; none on play areas, courts or by the blocks
    trees = []
    keep_off = unary_union([avoid_trees, play.buffer(1.5), court.buffer(2.0), asphalt.buffer(0.6), stalls.buffer(1.0)])

    def plant(p, h, r, kind):
        if keep_off.contains(Point(p)):
            return False
        if any(math.dist(p, (t[0], t[1])) < max(3.5, r * 1.5) for t in trees):
            return False
        trees.append([round(p[0], 2), round(p[1], 2), Z['lawn'], round(h, 2), round(r, 2), kind])
        return True
    for q in parts(lawn):
        if q.area < 6:
            continue
        r, L, W, d = rect_axes(q)
        if W < 4.5 and L > 8:
            # a strip: a row down its middle
            c = r.centroid
            n = int(L // 7.0)
            for i in range(n):
                s = -L / 2 + 3.5 + i * 7.0
                p = (c.x + d[0] * s, c.y + d[1] * s)
                if q.buffer(-0.5).contains(Point(p)):
                    kind = 'conifer' if (i % 3 != 2) else 'broad'
                    plant(p, rnd.uniform(9, 13) if kind == 'conifer' else rnd.uniform(7, 10), 2.2 if kind == 'conifer' else 3.2, kind)
        else:
            inner = q.buffer(-1.2)
            if inner.is_empty:
                continue
            bx = inner.bounds
            n = int(q.area / 38) + 1
            for _ in range(n * 6):
                if n <= 0:
                    break
                p = (rnd.uniform(bx[0], bx[2]), rnd.uniform(bx[1], bx[3]))
                if not inner.contains(Point(p)):
                    continue
                kind = rnd.choice(['broad', 'broad', 'broad', 'small', 'conifer'])
                h = rnd.uniform(6, 10) if kind == 'broad' else rnd.uniform(3.5, 5) if kind == 'small' else rnd.uniform(8, 12)
                if plant(p, h, 3.0 if kind == 'broad' else 1.8 if kind == 'small' else 2.0, kind):
                    n -= 1
    # people on the paths and the paving round the shops
    for q in parts(walkable):
        if q.area < 40:
            continue
        bx = q.bounds
        k = int(q.area / 260)
        for _ in range(k * 5):
            if k <= 0:
                break
            p = (rnd.uniform(bx[0], bx[2]), rnd.uniform(bx[1], bx[3]))
            if q.buffer(-0.8).contains(Point(p)) and not no.buffer(-1.5).contains(Point(p)) \
                    and all(math.dist(p, b[:2]) > 1.6 for b in benches) and all(math.dist(p, l) > 1.0 for l in lamps_at) \
                    and all(math.dist(p, c[:2]) > 2.8 for c in cars) and all(math.dist(p, t[:2]) > 1.0 for t in trees):
                people.append([round(p[0], 2), round(p[1], 2), Z['paving'] + 0.02, rnd.randrange(10)])
                k -= 1
    return dict(trees=trees, cars=cars, people=people, benches=benches, labels=labels,
                lamps=[list(l) for l in LS.LIGHTS], region=list(REGION.bounds),
                lawn=lawn, paving=walkable, asphalt=asphalt)
