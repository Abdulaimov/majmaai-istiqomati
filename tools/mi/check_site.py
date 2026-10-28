"""Where the props stand (model/complex.json against the genplan, build/genplan.json): benches on the
paving with 1.5 m free in front, nothing in a building, people clear of benches, lamps, cars and
trees, trees clear of the blocks and of each other. Prints the problems (none: all is well).

    tools/ab/py tools/mi/check_site.py
"""
import json
import math
import os

from shapely.geometry import Point, Polygon, box
from shapely import affinity
from shapely.ops import unary_union

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
cx = json.load(open(os.path.join(ROOT, 'src', 'model', 'complex.json')))
gp = json.load(open(os.path.join(ROOT, 'build', 'genplan.json')))


def U(cls):
    return unary_union([Polygon(p['ring']).buffer(0) for p in gp['classes'].get(cls, [])])


towers = unary_union([Polygon(t.get('podium') or t['outline']).buffer(0) for t in cx['towers']])
others = unary_union([U(k) for k in ('existing', 'kinder', 'studio', 'admin', 'transformer', 'waste')])
built = unary_union([towers, others])
walk = unary_union([U('paving'), U('path'), U('podium')]).buffer(0.3)
lawn = unary_union([U('lawn'), U('lawn_rest')])
bad = []
for b in cx['benches']:
    x, y, r = b
    seat = affinity.rotate(box(x - 0.95, y - 0.3, x + 0.95, y + 0.3), r, origin=(x, y), use_radians=True)
    if not walk.contains(seat):
        bad.append(('bench off the paving', b))
    # the backrest at the bench's +y (-sin r, cos r): the seat faces the other way; 1.5 m in front
    # of it free of lawn and buildings
    fx, fy = x + math.sin(r) * 1.2, y - math.cos(r) * 1.2
    front = Point(fx, fy).buffer(0.5)
    if front.intersects(built) or lawn.contains(Point(fx, fy)):
        bad.append(('bench facing the lawn or a wall', b))
    for l in cx['lamps']:
        if math.dist((x, y), l[:2]) < 1.5:
            bad.append(('bench at a lamp', b))
for p in cx['people']:
    P = Point(p[0], p[1])
    if built.buffer(0.3).contains(P):
        bad.append(('person in a building', p))
    if any(math.dist(p[:2], b[:2]) < 1.2 for b in cx['benches']):
        bad.append(('person on a bench', p))
    if any(math.dist(p[:2], c[:2]) < 2.6 for c in cx['cars']):
        bad.append(('person in a car', p))
    if any(math.dist(p[:2], t[:2]) < 0.8 and t[2] < 1 for t in cx['trees_placed']):
        bad.append(('person in a tree', p))
ground = [t for t in cx['trees_placed'] if t[2] < 1.0]
for i, t in enumerate(ground):
    if towers.buffer(1.5).contains(Point(t[0], t[1])):
        bad.append(('tree in a block', t))
    for u in ground[i + 1:]:
        if math.dist(t[:2], u[:2]) < 2.0:
            bad.append(('trees one in another', t, u))
for c in cx['cars']:
    if built.contains(Point(c[0], c[1])):
        bad.append(('car in a building', c))
for b in bad:
    print(*b)
print(len(bad), 'problems;', len(cx['benches']), 'benches,', len(cx['people']), 'people,', len(cx['trees_placed']), 'trees,', len(cx['cars']), 'cars')
