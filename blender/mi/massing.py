"""The blocks not built yet, and the other buildings of the genplan, as a white architectural model:
their real size (footprint from the genplan, floors from its labels), a shallow groove at every floor
so the storeys read, the two shop floors a little wider than the tower. They keep the blocks' places
on the site until each is made in full (like К, block_k.py).
"""
import math

from shapely.geometry import Polygon

from complex.geom import MeshBuilder

from .config import level


def grooved(mb, poly, z0, z1, step, mat='Massing', groove='Massing groove', first=None):
    """a prism with a 6 cm groove round it at every floor line"""
    zs = [z0]
    z = first if first is not None else z0 + step
    while z < z1 - 0.5:
        zs.append(z)
        z += step
    zs.append(z1)
    thin = poly.buffer(-0.06, join_style='mitre')
    for a, b in zip(zs, zs[1:]):
        mb.prism(poly, a + (0.04 if a > z0 else 0.0), b - (0.04 if b < z1 else 0.0), mat)
        if a > z0:
            mb.prism(thin, a - 0.04, a + 0.04, groove)
    mb.polygon_face(poly, z1, 'Massing roof')


def block(mb, ring, floors):
    """ring: the tower's footprint (site metres); floors: (lower part, higher part) from "16/18" """
    g = Polygon(ring).buffer(0)
    lo, hi = floors
    pod = g.buffer(0.6, join_style='mitre')
    grooved(mb, pod, 0.0, level(3), 5.1)
    # the higher part over most of the block, the lower one over its last bay (like К)
    c = list(g.exterior.coords)[:4]
    e = [(c[(i + 1) % 4][0] - c[i][0], c[(i + 1) % 4][1] - c[i][1]) for i in range(4)]
    i = max(range(4), key=lambda j: math.hypot(*e[j]))
    L = math.hypot(*e[i])
    d = (e[i][0] / L, e[i][1] / L)
    a, b = c[i], c[(i + 1) % 4]
    w = c[(i + 2) % 4]
    k = 7.5 / L
    cut = (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
    cut2 = (cut[0] + (w[0] - b[0]), cut[1] + (w[1] - b[1]))
    low = Polygon([a, cut, cut2, (a[0] + (w[0] - b[0]), a[1] + (w[1] - b[1]))]).buffer(0)
    high = g.difference(low.buffer(0.01, join_style='mitre'))
    grooved(mb, low, level(3), level(lo + 1), 3.3)
    grooved(mb, high, level(3), level(hi + 1), 3.3)
    # a parapet ring on top
    top = level(hi + 1)
    mb.prism(high.difference(high.buffer(-0.35, join_style='mitre')), top, top + 1.0, 'Massing', 'Massing')
    return level(hi + 1) + 1.0


def building(mb, ring, floors, step=3.3, ground=None):
    g = Polygon(ring).buffer(0)
    top = (ground or step) + (floors - 1) * step
    grooved(mb, g, 0.0, top, step, first=ground or step)
    mb.prism(g.difference(g.buffer(-0.3, join_style='mitre')), top, top + 0.8, 'Massing', 'Massing')
    return top + 0.8


def neighbour(mb, ring, floors, mat):
    """the existing houses round the plot: plain light blocks, a flat roof"""
    g = Polygon(ring).buffer(0)
    if g.area < 8:
        return 0
    top = 3.1 * floors + 0.6
    mb.prism(g, 0.0, top, mat, 'Neighbour roof')
    mb.prism(g.difference(g.buffer(-0.25, join_style='mitre')), top, top + 0.5, mat, mat)
    return top
