"""Holes in block К's shell: horizontal rays at every 20 cm of each face of the tower and the brick part,
from 3 m outside straight in; a ray that goes further than 3 m + the deepest recess (the floor-20
terraces, 2.5 m) without hitting anything has found a gap. Also rays from above onto the roofs.

    blender -b build/mi.blend -P blender/mi_gaps.py
"""
import math
import sys
import os
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mi import block_k as K  # noqa: E402
from mi.config import frame, genplan, to_site  # noqa: E402

gp = genplan()
fr = frame(gp['blocks']['К'])
dg = bpy.context.evaluated_depsgraph_get()
obs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('K_')]
trees = []
for o in obs:
    trees.append(BVHTree.FromObject(o, dg))


def cast(p, d, far):
    best = None
    for t in trees:
        h = t.ray_cast(Vector(p), Vector(d), far)
        if h[0] is not None and (best is None or h[3] < best):
            best = h[3]
    return best


c, s = math.cos(fr[1]), math.sin(fr[1])
def site_dir(dx, dy):
    return (c * dx - s * dy, s * dx + c * dy, 0.0)


faces = [  # (a, b) in block metres, outward to the right; z range
    ((K.XE, K.YN), (K.XB, K.YN), K.Z_SOFFIT, K.CROWN),
    ((K.XE, K.YS), (K.XE, K.YN), K.Z_SOFFIT, K.CROWN),
    ((K.XB, K.YS), (K.XE, K.YS), K.Z_SOFFIT, K.CROWN),
    ((K.XB, K.YN), (K.XB, K.YS), K.BRICK_TOP, K.CROWN),
    ((K.XB, K.YBN), (K.XW, K.YBN), K.level(4), K.BRICK_TOP),
    ((K.XW, K.YBN), (K.XW, K.YS), K.level(4), K.BRICK_TOP),
    ((K.XW, K.YS), (K.XB, K.YS), K.level(4), K.BRICK_TOP),
]
holes = []
for (a, b, z0, z1) in faces:
    L = math.dist(a, b)
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (d[1], -d[0])
    u = 0.1
    while u < L - 0.1:
        z = z0 + 0.1
        while z < z1 - 0.05:
            x, y = a[0] + d[0] * u + n[0] * 3.0, a[1] + d[1] * u + n[1] * 3.0
            X, Y = to_site(fr, x, y)
            h = cast((X, Y, z), site_dir(-n[0], -n[1]), 3.0 + 3.2)
            if h is None:
                holes.append((round(a[0], 2), round(a[1], 2), round(u, 2), round(z, 2)))
            z += 0.2
        u += 0.2
print('rays done; holes:', len(holes))
groups = {}
for h in holes:
    k = (h[0], h[1], round(h[2]), round(h[3] / 3.0))
    groups.setdefault(k, []).append(h)
for k, v in sorted(groups.items())[:60]:
    us = [h[2] for h in v]; zs = [h[3] for h in v]
    print('face', k[:2], 'u %.1f-%.1f z %.1f-%.1f' % (min(us), max(us), min(zs), max(zs)), len(v))

# from above: every 40 cm over the tower and the brick part, straight down from 80 m; the first hit
# must be a roof, a terrace, a parapet or a planter (not deep inside the shell)
from shapely.geometry import Point, Polygon
tower = Polygon([(K.XW, K.YS), (K.XE, K.YS), (K.XE, K.YN), (K.XB, K.YN), (K.XB, K.YBN), (K.XW, K.YBN)])
deep = []
x = K.XW + 0.2
while x < K.XE:
    y = K.YS + 0.2
    while y < K.YN:
        if tower.contains(Point(x, y)):
            X, Y = to_site(fr, x, y)
            h = cast((X, Y, 80.0), (0.0, 0.0, -1.0), 80.0)
            z = 80.0 - h if h is not None else -1
            floor_z = K.BRICK_ROOF - 0.1 if x < K.XB else K.Z20 - 0.2
            if z < floor_z:
                deep.append((round(x, 1), round(y, 1), round(z, 2)))
        y += 0.4
    x += 0.4
print('from above: holes', len(deep), deep[:20])
