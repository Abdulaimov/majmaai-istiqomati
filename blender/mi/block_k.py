"""Block К, built in full: the exterior of the client renders 9 (south-east face) and 10 (north-east face).

The facades are measured off the renders, each face rectified to metres (tools/mi/rectify.py):
render 10's north-east face from its corners (871,345) (1793,831) (1792,2650) (871,2563) = u 0..29.2
(from the east corner), z 15.23..67.42; render 9's south-east face from (2367,1131) (2910,931)
(2910,2622) (2368,2659) = u 0..22.4 (from the south corner). The floor grid (config.py: floor 3 at
9.7 m, then 3.0 m a floor) lies on the balcony slabs and the windows' spandrels of both renders.

The plan outline (sheet 32): the white tower x -10.98..18.22, y -11.22..11.18; the brick part at the
north-west end x -18.63..-10.98, its north-east face set back 1.5 m (y 9.68). Block frame: x along
the block, + to the south-east (the podium's rounded end), y + to the north-east (the inner street).

What the renders show, bottom to top:
- floors 1-3, the podium: shop windows (mullions every 1.58 m), a white band, floor 2's tall glass,
  a white band, floor 3 in brick with small windows; white blades in pairs on the tower's 3.15 m
  module in front of floors 2-3, rising into the parapet (13.8 m); a rounded end to the crossroads;
- floor 4 in brick, set back under the tower; the tower's white soffit at 15.23 m;
- floors 5-19: a flat white wall with deep openings (0.4 m) in tiers of three floors (5-7, 8-10,
  11-13, 14-19), a 0.6 m white band between the tiers; in each opening a window (black frames, a
  dark spandrel at every floor, a mullion, a transom), a white or timber panel, or a narrow groove;
  wide and narrow openings change places from tier to tier (the renders' chequered rhythm), and the
  warm LED line in a groove jumps from module to module with them;
- the north-east face: a stack of corner balconies at the east corner (a glazed corner on floors
  5-7), a deep slot with a balcony on every floor (a warm LED line under each) that cuts through the
  crown, and a three-storey loggia box on floors 11-13 lined in timber, round the east corner;
- floor 20 set back behind the frame with terraces (a white upstand and a glass rail in every
  opening, trees in planters), sloping hoods at the top of the openings, the frame's top beam to
  67.4 m with a warm LED line along it and down the tower's corners;
- the brick part: 17 floors, punched windows (2 x 2 panes), a roof terrace with small trees.
"""
import math
import random

from shapely.geometry import Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from complex.geom import MeshBuilder, resample

from .config import level

XB, XE = -10.98, 18.22          # the white tower along x
YS, YN = -11.22, 11.18          # across
XW = -18.63                     # the brick part's north-west face
YBN = 9.68                      # the brick part's north-east face (set back 1.5 m)
Z_SOFFIT = 15.23
Z20 = level(20)                 # 60.7: floor 20, set back behind the frame
ROOF = level(21)                # 63.7
HOOD0, HOOD1 = 64.05, 66.2      # the hoods at the top of the openings
CROWN = 67.4                    # the frame's top beam
BRICK_FLOORS = 17
BRICK_ROOF = level(BRICK_FLOORS + 1)    # 54.7
BRICK_TOP = BRICK_ROOF + 0.6
REC = 0.4                       # openings' depth below floor 20
PIER = 0.6                      # the frame's depth round the floor-20 terraces
SET20 = 1.9                     # floor 20 set back from the faces

TIERS = [(5, 8), (8, 11), (11, 14), (14, 20)]


def tier_z(t):
    f0, f1 = TIERS[t]
    return level(f0) + 0.5, level(f1) - 0.1


# ---- the openings, measured (u0, u1, kind) ------------------------------------------------------
# W window, N narrow window, B white panel, T timber panel, G groove, L groove with the LED line,
# CW glazed corner, C corner balconies (both touch the east corner)
NE_RIGHT_A = [(12.88, 14.31, 'N'), (16.06, 18.65, 'W'), (19.23, 20.69, 'N'), (21.28, 21.85, 'L'),
              (22.4, 25.03, 'W'), (25.6, 27.5, 'W')]
NE_RIGHT_B = [(12.88, 15.44, 'W'), (16.04, 17.5, 'N'), (18.06, 18.65, 'L'), (19.23, 21.81, 'W'),
              (22.41, 23.88, 'N'), (25.6, 27.5, 'W')]
NE = {0: [(0.0, 1.63, 'CW'), (2.23, 2.78, 'G'), (3.38, 5.88, 'W'), (6.53, 7.96, 'N'), (8.56, 9.13, 'G')] + NE_RIGHT_A,
      1: [(0.0, 1.9, 'C'), (3.35, 4.81, 'N'), (6.53, 8.9, 'W')] + NE_RIGHT_B,
      2: NE_RIGHT_A,                    # floors 11-13: the loggia box on the left part
      3: [(0.0, 1.9, 'C'), (3.35, 4.81, 'N'), (6.53, 8.9, 'W')] + NE_RIGHT_B}
SE = {0: [(1.13, 2.28, 'B'), (2.85, 3.4, 'G'), (3.98, 5.4, 'N'), (5.98, 8.54, 'B'), (9.13, 11.69, 'W'),
          (12.25, 14.81, 'B'), (16.5, 17.94, 'N'), (18.5, 22.4, 'CW')],
      1: [(1.13, 2.28, 'B'), (2.85, 5.4, 'W'), (7.13, 8.54, 'B'), (9.13, 11.69, 'W'), (12.25, 12.81, 'G'),
          (13.4, 14.81, 'B'), (15.38, 17.94, 'W'), (18.5, 19.06, 'G'), (19.65, 22.4, 'C')],
      2: [(1.13, 2.28, 'T'), (2.85, 3.4, 'T'), (3.98, 5.4, 'N'), (5.98, 8.54, 'T'), (9.13, 11.69, 'W'),
          (12.25, 14.81, 'T'), (16.5, 17.94, 'N')],
      3: [(1.13, 2.28, 'B'), (2.85, 5.4, 'W'), (5.98, 6.56, 'G'), (7.13, 8.54, 'B'), (9.13, 11.69, 'W'),
          (13.4, 14.81, 'B'), (15.38, 17.94, 'W'), (18.5, 19.06, 'G'), (19.65, 22.4, 'C')]}
SLOT = (9.69, 11.6)             # north-east face, floors 5 to the top
BOX = dict(ne=10.05, se=18.56, out=1.0, z0=33.9, z1=43.6, floors=(11, 12, 13))
# the north-west face above the brick part (the south-east face's floors 14-19, no corner balconies)
NW_T4 = [(2.85, 5.4, 'W'), (5.98, 6.56, 'G'), (7.13, 8.54, 'B'), (9.13, 11.69, 'W'), (13.4, 14.81, 'B'),
         (15.38, 17.94, 'W'), (18.5, 19.06, 'G')]


def sw_tiers():
    """the courtyard face (no render shows it): the north-east face's module (3.18 m), wide and
    narrow openings changing places from tier to tier, white panels at the lift lobby (middle)"""
    out = {}
    for t in range(4):
        row = []
        for k in range(9):
            u0 = 0.95 + 3.18 * k
            wide = (k + t) % 2 == 0
            kind = 'B' if k == 4 else ('W' if wide else 'N')
            row.append((u0, u0 + (2.58 if wide else 1.45), kind))
            if not wide and k in (1, 7):
                row.append((u0 + 2.02, u0 + 2.58, 'G'))
        out[t] = row
    return out


class Face:
    """A straight facade from a to b (block metres), outward to the right of a->b."""

    def __init__(self, a, b):
        self.a = a
        self.L = math.dist(a, b)
        self.d = ((b[0] - a[0]) / self.L, (b[1] - a[1]) / self.L)
        self.n = (self.d[1], -self.d[0])

    def p(self, u, off=0.0):
        return (self.a[0] + self.d[0] * u + self.n[0] * off, self.a[1] + self.d[1] * u + self.n[1] * off)

    def quad(self, u0, u1, o0, o1):
        return Polygon([self.p(u0, o0), self.p(u1, o0), self.p(u1, o1), self.p(u0, o1)])


def fbox(mb, F, u0, u1, o0, o1, z0, z1, mat, caps=True):
    if u1 - u0 < 1e-3 or o1 - o0 < 1e-3 or z1 - z0 < 1e-3:
        return
    mb.prism(F.quad(u0, u1, o0, o1), z0, z1, mat, mat if caps else None, mat if caps else None)


def fwall(mb, F, u0, u1, off, z0, z1, mat):
    """a flat wall or pane facing out, UVs in facade metres"""
    if u1 - u0 > 1e-3 and z1 - z0 > 1e-3:
        mb.quad_wall(F.p(u0, off), F.p(u1, off), z0, z1, mat, u0=u0)


def bwall(mb, F, u0, u1, off, z0, z1, mat):
    """the same, facing in"""
    if u1 - u0 > 1e-3 and z1 - z0 > 1e-3:
        mb.quad_wall(F.p(u1, off), F.p(u0, off), z0, z1, mat, u0=u0)


def jamb(mb, F, u, o0, o1, z0, z1, mat, facing):
    """the side of an opening at u from depth o0 to o1 (o < 0 is in), facing +d (facing=1) or -d"""
    if z1 - z0 < 1e-3:
        return
    if facing > 0:
        mb.quad_wall(F.p(u, o1), F.p(u, o0), z0, z1, mat)
    else:
        mb.quad_wall(F.p(u, o0), F.p(u, o1), z0, z1, mat)


def extrude(mb, F, u0, u1, profile, mat):
    """a profile drawn across the facade (points (offset, z)) run along it from u0 to u1; every
    face turned outwards (checked against the profile's middle)"""
    P = lambda u, o, z: (*F.p(u, o), z)
    co = sum(p[0] for p in profile) / len(profile)
    cz = sum(p[1] for p in profile) / len(profile)
    um = (u0 + u1) / 2

    def put(pts, out):
        a, b, c = pts[0], pts[1], pts[2]
        n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
             (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
             (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        mb.face(pts if sum(n[i] * out[i] for i in range(3)) >= 0 else pts[::-1], mat)
    for (oa, za), (ob, zb) in zip(profile, profile[1:] + profile[:1]):
        q = (*F.p(um, (oa + ob) / 2), (za + zb) / 2)
        c = (*F.p(um, co), cz)
        put([P(u0, oa, za), P(u1, oa, za), P(u1, ob, zb), P(u0, ob, zb)], tuple(q[i] - c[i] for i in range(3)))
    for u, s in ((u0, -1), (u1, 1)):
        put([P(u, o, z) for o, z in profile], (F.d[0] * s, F.d[1] * s, 0.0))


def holed_wall(mb, F, u0, u1, off, z0, z1, mat, holes, inward=False):
    """a flat wall with rectangular openings [(u0, u1, z0, z1)], cut into vertical strips at the
    openings' edges, each strip solid except where an opening crosses it"""
    us = sorted({u0, u1, *[min(max(h[0], u0), u1) for h in holes], *[min(max(h[1], u0), u1) for h in holes]})
    put = bwall if inward else fwall
    for a, b in zip(us, us[1:]):
        if b - a < 1e-4:
            continue
        m = (a + b) / 2
        cuts = sorted((h[2], h[3]) for h in holes if h[0] < m < h[1])
        z = z0
        for c0, c1 in cuts:
            if c0 > z + 1e-4:
                put(mb, F, a, b, off, z, min(c0, z1), mat)
            z = max(z, c1)
        if z1 > z + 1e-4:
            put(mb, F, a, b, off, z, z1, mat)


# ---- what fills an opening -------------------------------------------------------------------------

def window(mb, F, u0, u1, z0, z1, off=-REC, narrow=False, sill=True):
    """a window over several floors (render 10): the pane, black frames round it, a mullion at a third,
    at every floor a dark spandrel from 0.4 m under the floor to 0.5 m over it framed in black, a
    transom 1.1 m over the floor"""
    if u1 - u0 < 0.15 or z1 - z0 < 0.2:
        return
    fwall(mb, F, u0, u1, off, z0, z1, 'K glass')
    fo, fd = off - 0.03, off + 0.06
    fr = 0.06
    fbox(mb, F, u0, u0 + fr, fo, fd, z0, z1, 'Frame dark')
    fbox(mb, F, u1 - fr, u1, fo, fd, z0, z1, 'Frame dark')
    fbox(mb, F, u0, u1, fo, fd, z0, z0 + fr, 'Frame dark')
    fbox(mb, F, u0, u1, fo, fd, z1 - fr, z1, 'Frame dark')
    if u1 - u0 > 0.7:
        m = u0 + (u1 - u0) * (0.36 if narrow else 0.3)
        fbox(mb, F, m - 0.03, m + 0.03, fo, fd - 0.01, z0, z1, 'Frame dark')
    f = 3
    while level(f) - 0.4 < z1:
        z = level(f)
        s0, s1 = max(z - 0.4, z0), min(z + 0.5, z1)
        if s1 - s0 > 0.05:
            fwall(mb, F, u0, u1, off + 0.004, s0, s1, 'Spandrel')
            for zz in (s0, s1):
                if z0 + 0.02 < zz < z1 - 0.02:
                    fbox(mb, F, u0, u1, fo, fd, zz - 0.03, zz + 0.03, 'Frame dark')
        if sill and z0 + 0.05 < z + 1.1 < z1 - 0.05:
            fbox(mb, F, u0, u1, fo, fd - 0.02, z + 1.08, z + 1.12, 'Frame dark')
        f += 1


def panel(mb, F, u0, u1, z0, z1, mat='Panel white', off=-REC):
    fwall(mb, F, u0, u1, off, z0, z1, mat)


def rail(mb, F, u0, u1, off, z, h=1.0, mat='Railing glass'):
    """glass balustrade: a pane with a slim top rail"""
    fwall(mb, F, u0, u1, off, z, z + h, mat)
    bwall(mb, F, u0, u1, off - 0.002, z, z + h, mat)
    fbox(mb, F, u0, u1, off - 0.025, off + 0.025, z + h - 0.04, z + h, 'Frame dark')


def reveals(mb, F, u0, u1, z0, z1, dep, left=True, right=True, head=True, sill=True, mat='Stone white'):
    """the sides, head and sill of an opening, dep deep"""
    if left:
        jamb(mb, F, u0, 0.0, -dep, z0, z1, mat, +1)
    if right:
        jamb(mb, F, u1, 0.0, -dep, z0, z1, mat, -1)
    if head:
        mb.polygon_face(F.quad(u0, u1, -dep, 0.0), z1, mat, up=False)
    if sill:
        mb.polygon_face(F.quad(u0, u1, -dep, 0.0), z0, mat, up=True)


def fill(mb, F, u0, u1, z0, z1, kind, glass_from=None, glass_to=None):
    """the content of an opening between z0 and z1 at the openings' depth"""
    a = u0 if glass_from is None else glass_from
    b = u1 if glass_to is None else glass_to
    if kind in ('W', 'N', 'CW', 'C'):
        window(mb, F, a, b, z0, z1, narrow=kind == 'N')
    elif kind == 'B':
        panel(mb, F, a, b, z0, z1)
    elif kind == 'T':
        panel(mb, F, a, b, z0, z1, 'Wood slat')
    elif kind in ('G', 'L'):
        panel(mb, F, a, b, z0, z1, 'Panel white', off=-0.22)
        if kind == 'L':
            fbox(mb, F, b - 0.06, b - 0.01, -0.22, -0.17, z0, z1, 'LED warm')


def crown_opening(mb, F, u0, u1, kind, left=True, right=True):
    """an opening at floor 20: the white upstand standing a little proud, a glass rail on it, the
    terrace behind; at the top a hood sloping from the face at 66.2 m to the frame's back at 64.05 m"""
    a, b = u0, u1
    fbox(mb, F, a, b, -PIER, 0.15, Z20 - 0.12, Z20 + 1.15, 'Stone white')
    rail(mb, F, a + 0.02, b - 0.02, -0.12, Z20 + 1.15, 0.95)
    if kind == 'L':
        fbox(mb, F, u1 - 0.06, u1 - 0.01, -PIER, -PIER + 0.05, Z20 + 1.15, HOOD1, 'LED warm')
    P = lambda uu, o, z: (*F.p(uu, o), z)
    mb.face([P(u0, -PIER, HOOD0), P(u1, -PIER, HOOD0), P(u1, 0.0, HOOD1), P(u0, 0.0, HOOD1)], 'Stone white')
    for u, s in ((u0, 1), (u1, -1)):
        tri = [P(u, 0.0, HOOD1), P(u, -PIER, HOOD0), P(u, -PIER, HOOD1)]
        mb.face(tri if s > 0 else tri[::-1], 'Stone white')
    if left:
        jamb(mb, F, u0, 0.0, -PIER, Z20 - 0.1, HOOD1, 'Stone white', +1)
    if right:
        jamb(mb, F, u1, 0.0, -PIER, Z20 - 0.1, HOOD1, 'Stone white', -1)


def build_face(mb, F, tiers, extra_holes=(), crown=True, z_from=None, corner=''):
    """the white wall of a face from the soffit (or z_from) to the top beam, its openings and their
    contents. corner: 'start' or 'end' when the face's corner openings (C, CW) touch that end."""
    holes, jobs = [], []
    for t, row in tiers.items():
        z0, z1 = tier_z(t)
        if z_from is not None:
            z0 = max(z0, z_from)
        if z1 <= z0:
            continue
        top = t == 3 and crown
        for (u0, u1, kind) in row:
            holes.append((u0, u1, z0, HOOD1 if top else z1))
            jobs.append((t, u0, u1, kind, z0, z1, top))
    holes += list(extra_holes)
    zw0 = Z_SOFFIT if z_from is None else z_from
    holed_wall(mb, F, 0.0, F.L, 0.0, zw0, CROWN, 'Stone white', holes)
    if crown:
        # the frame's back face round the floor-20 terraces, solid behind the hoods and the beam
        back = [(h[0], h[1], Z20 - 0.1, CROWN + 1 if h[3] > CROWN else HOOD0) for h in holes if h[3] > Z20]
        holed_wall(mb, F, 0.0, F.L, -PIER, Z20 - 0.1, CROWN, 'Stone white', back, inward=True)
        cap = F.quad(0.0, F.L, -PIER, 0.0)
        cuts = [F.quad(h[0], h[1], -PIER - 0.01, 0.01) for h in holes if h[3] > CROWN]
        if cuts:
            cap = cap.difference(unary_union(cuts))
        mb.polygon_face(cap, CROWN, 'Stone white')
    for (t, u0, u1, kind, z0, z1, top) in jobs:
        at0 = corner == 'start' and u0 < 1e-6
        at1 = corner == 'end' and u1 > F.L - 1e-6
        g0 = REC if at0 else None
        g1 = F.L - REC if at1 else None
        fill(mb, F, u0, u1, z0, z1, kind, g0, g1)
        dep = 0.22 if kind in ('G', 'L') else REC
        reveals(mb, F, u0, u1, z0, z1, dep, left=not at0, right=not at1, head=not top, sill=True)
        if top:
            fwall(mb, F, u0 if not at0 else REC, u1 if not at1 else F.L - REC, -dep, z1, Z20 + 0.02, 'Stone white')
            crown_opening(mb, F, u0, u1, kind, left=not at0, right=not at1)
        if kind == 'C':
            balconies(mb, F, u0, u1, TIERS[t], at0, at1)
    return holes


def balconies(mb, F, u0, u1, tier, at0, at1):
    """corner balconies on every floor of a tier but its first: a slab a metre proud of the face, a
    glass rail round it (the part on this face; corner_square() adds the corner)"""
    f0, f1 = tier
    for f in range(f0 + 1, f1):
        z = level(f)
        a = u0 if not at0 else 0.0
        b = u1 if not at1 else F.L
        fbox(mb, F, a, b, -REC, 1.0, z - 0.32, z, 'Loggia slab')
        rail(mb, F, a, b, 0.95, z, 1.0)
        if not at0:
            side = Face(F.p(a, -REC), F.p(a, 0.95))
            rail(mb, side, 0.0, side.L, 0.0, z, 1.0)
        if not at1:
            side = Face(F.p(b, 0.95), F.p(b, -REC))
            rail(mb, side, 0.0, side.L, 0.0, z, 1.0)


def corner_square(mb, tiers_c):
    """the east corner: where the north-east and south-east balconies meet, the corner square of the
    slabs and the rail round it"""
    cx, cy = XE, YN
    sq = Polygon([(cx, cy), (cx + 1.0, cy), (cx + 1.0, cy + 1.0), (cx, cy + 1.0)])
    for (f0, f1) in tiers_c:
        for f in range(f0 + 1, f1):
            z = level(f)
            mb.prism(sq, z - 0.32, z, 'Loggia slab', 'Loggia slab', 'Loggia slab')
            rail(mb, Face((cx + 0.95, cy), (cx + 0.95, cy + 0.95)), 0.0, 0.95, 0.0, z, 1.0)
            rail(mb, Face((cx + 0.95, cy + 0.95), (cx, cy + 0.95)), 0.0, 0.95, 0.0, z, 1.0)


def slot(mb, F, u0, u1):
    """the deep slot of the north-east face: white sides 1.2 m deep, a glazed door at the back and a
    balcony on every floor (slab to the face, dark glass rail, warm LED line under its front edge);
    it cuts through the crown"""
    D = 1.2
    z0 = level(5) + 0.5
    fwall(mb, F, u0, u1, -D, z0, CROWN, 'Loggia wall')
    jamb(mb, F, u0, 0.0, -D, z0, CROWN, 'Stone white', +1)
    jamb(mb, F, u1, 0.0, -D, z0, CROWN, 'Stone white', -1)
    mb.polygon_face(F.quad(u0, u1, -D, 0.0), z0, 'Stone white', up=True)
    for f in range(5, 21):
        z = level(f)
        window(mb, F, u0 + 0.1, u1 - 0.1, max(z + 0.05, z0), z + 2.7, off=-D + 0.02, sill=False)
        if f > 5:
            fbox(mb, F, u0, u1, -D, -0.05, z - 0.45, z, 'Loggia slab')
            rail(mb, F, u0 + 0.03, u1 - 0.03, -0.1, z, 1.0, 'Railing glass dark')
            fbox(mb, F, u0 + 0.03, u1 - 0.03, -0.1, -0.05, z - 0.45, z - 0.41, 'LED warm')


def loggia_box(mb):
    """the loggia box of floors 11-13 round the east corner (renders 9, 10): a white frame a metre
    proud of both faces, timber soffit and ends inside, glazed doors between timber piers at the
    back, a loggia on each floor with a glass rail; a warm LED line inside its frame"""
    o, z0, z1 = BOX['out'], BOX['z0'], BOX['z1']
    t = 0.5
    ne0 = XE - BOX['ne']               # x of its north-west end
    se0 = YS + BOX['se']               # y of its south end
    outer = Polygon([(ne0, YN - REC), (XE - REC, YN - REC), (XE - REC, se0), (XE + o, se0), (XE + o, YN + o), (ne0, YN + o)])
    inner = Polygon([(ne0 + t, YN - REC), (XE - REC, YN - REC), (XE - REC, se0 + t), (XE + o - 0.1, se0 + t),
                     (XE + o - 0.1, YN + o - 0.1), (ne0 + t, YN + o - 0.1)])
    mb.prism(outer, z1 - t, z1, 'Stone white', 'Stone white', 'Stone white')
    mb.prism(outer, z0, z0 + 0.6, 'Stone white', 'Stone white', 'Stone white')
    mb.polygon_face(inner, z1 - t - 0.002, 'Wood slat', up=False)
    endNE = Polygon([(ne0, YN - REC), (ne0 + t, YN - REC), (ne0 + t, YN + o), (ne0, YN + o)])
    endSE = Polygon([(XE - REC, se0), (XE + o, se0), (XE + o, se0 + t), (XE - REC, se0 + t)])
    for e in (endNE, endSE):
        mb.prism(e, z0 + 0.6, z1 - t, 'Stone white', None, None)
    # the ends' inner faces in timber
    E1 = Face((ne0 + t + 0.002, YN + o - 0.1), (ne0 + t + 0.002, YN - REC))
    fwall(mb, E1, 0.0, E1.L, 0.0, z0 + 0.6, z1 - t, 'Wood slat')
    E2 = Face((XE - REC, se0 + t + 0.002), (XE + o - 0.1, se0 + t + 0.002))
    fwall(mb, E2, 0.0, E2.L, 0.0, z0 + 0.6, z1 - t, 'Wood slat')
    # the LED line inside the frame: up both ends, along the soffit's front edges
    FN = Face((ne0 + t, YN + o), (XE + o, YN + o))
    FS = Face((XE + o, se0 + t), (XE + o, YN + o))
    fbox(mb, FN, 0.0, 0.05, -0.08, -0.02, z0 + 0.6, z1 - t, 'LED warm')
    fbox(mb, FS, 0.0, 0.05, -0.08, -0.02, z0 + 0.6, z1 - t, 'LED warm')
    fbox(mb, FN, 0.0, FN.L, -0.08, -0.02, z1 - t - 0.05, z1 - t, 'LED warm')
    fbox(mb, FS, 0.0, FS.L, -0.08, -0.02, z1 - t - 0.05, z1 - t, 'LED warm')
    # the back walls (REC in): glazed doors between timber piers on every floor
    NEb = Face((XE - REC, YN - REC), (ne0 + t, YN - REC))
    SEb = Face((XE - REC, se0 + t), (XE - REC, YN - REC))
    for B in (NEb, SEb):
        n = max(1, round(B.L / 3.0))
        w = B.L / n
        for f in BOX['floors']:
            z = level(f)
            zt = min(level(f + 1) - 0.3, z1 - t)
            for k in range(n):
                a, b = k * w, (k + 1) * w
                window(mb, B, a + 0.35, b - 0.35, z + 0.05, zt, off=0.0, sill=False)
                fbox(mb, B, a, a + 0.35, -0.02, 0.12, z, zt, 'Wood slat')
                fbox(mb, B, b - 0.35, b, -0.02, 0.12, z, zt, 'Wood slat')
            fbox(mb, B, 0.0, B.L, -0.02, 0.12, zt, min(level(f + 1), z1 - t), 'Wood slat')
    # the loggias: slabs at floors 12 and 13, glass rails along both open sides (floor 11 stands
    # on the box's bottom slab)
    floor = Polygon([(ne0 + t, YN - REC), (XE - REC, YN - REC), (XE - REC, se0 + t), (XE + o - 0.25, se0 + t),
                     (XE + o - 0.25, YN + o - 0.25), (ne0 + t, YN + o - 0.25)])
    for i, f in enumerate(BOX['floors']):
        z = level(f) if i else z0 + 0.6
        if i:
            mb.prism(floor, z - 0.3, z, 'Loggia slab', 'Deck wood', 'Loggia slab')
        Rn = Face((ne0 + t, YN + o - 0.35), (XE + o - 0.35, YN + o - 0.35))
        rail(mb, Rn, 0.0, Rn.L, 0.0, z, 1.0)
        Rs = Face((XE + o - 0.35, YN + o - 0.35), (XE + o - 0.35, se0 + t))
        rail(mb, Rs, 0.0, Rs.L, 0.0, z, 1.0)


def floor20(mb, rnd, trees):
    """floor 20 set back SET20 behind the frame: its glazed walls, the terrace round it (timber
    deck, planters with small trees), its roof with a parapet and the lift machine room"""
    box = Polygon([(XB + SET20, YS + SET20), (XE - SET20, YS + SET20), (XE - SET20, YN - SET20), (XB + SET20, YN - SET20)])
    ring = list(orient(box, 1.0).exterior.coords)
    for a, b in zip(ring, ring[1:]):
        F = Face(a, b)
        n = max(1, round(F.L / 1.6))
        w = F.L / n
        window(mb, F, 0.0, F.L, Z20 + 0.05, ROOF - 0.5, off=0.0, sill=False)
        for k in range(1, n):
            fbox(mb, F, k * w - 0.04, k * w + 0.04, -0.02, 0.06, Z20, ROOF - 0.5, 'Frame dark')
        fwall(mb, F, 0.0, F.L, 0.0, ROOF - 0.5, ROOF + 1.7, 'Loggia wall')
    mb.polygon_face(box, ROOF + 1.7, 'Roof')
    plant = Polygon([(-1.5, -5.0), (4.5, -5.0), (4.5, 1.0), (-1.5, 1.0)])
    mb.prism(plant, ROOF + 1.7, ROOF + 3.3, 'Stone white', 'Roof')
    terr = Polygon([(XB + PIER, YS + PIER), (XE - PIER, YS + PIER), (XE - PIER, YN - PIER), (XB + PIER, YN - PIER)]).difference(box)
    mb.polygon_face(terr, Z20 + 0.02, 'Deck wood')
    # planters on the terrace (low trees: they stay under the hoods, 1.2 m behind the frame's back)
    mid = Polygon([(XB + 1.35, YS + 1.35), (XE - 1.35, YS + 1.35), (XE - 1.35, YN - 1.35), (XB + 1.35, YN - 1.35)])
    for p in resample(list(orient(mid, 1.0).exterior.coords)[:-1], 5.2):
        mb.box(p[0], p[1], Z20, 0.9, 0.9, 0.6, 'Planter')
        mb.box(p[0], p[1], Z20 + 0.6, 0.78, 0.78, 0.02, 'Shrub')
        trees.append((p[0], p[1], Z20 + 0.6, rnd.uniform(2.0, 2.5)))
    # the roof garden on floor 20's roof: trees that show over the frame's top beam (render 9)
    for (x, y) in ((XB + 4.6, YS + 4.4), (XB + 4.6, YN - 4.4), (XE - 4.4, YS + 4.4), (XE - 4.4, YN - 4.4), (9.0, 2.5), (-4.0, 4.0)):
        mb.box(x, y, ROOF + 1.7, 1.6, 1.6, 0.6, 'Planter')
        mb.box(x, y, ROOF + 2.3, 1.45, 1.45, 0.02, 'Shrub')
        trees.append((x, y, ROOF + 2.3, rnd.uniform(3.4, 4.2)))


def floor4_and_soffit(mb):
    """floor 4 in brick, set back REC under the white tower, square windows on the tower's module;
    the tower's soffit over it"""
    z0, z1 = level(4), Z_SOFFIT
    xi, ys, yn = XE - REC, YS + REC, YN - REC
    for G in (Face((xi, yn), (XB, yn)), Face((xi, ys), (xi, yn)), Face((XB, ys), (xi, ys))):
        holes = []
        k = 0
        while 0.95 + 3.18 * k + 1.2 < G.L:
            c = 0.95 + 3.18 * k + 0.6
            holes.append((c - 0.6, c + 0.6, z0 + 0.9, z0 + 2.2))
            k += 1
        holed_wall(mb, G, 0.0, G.L, 0.0, z0, z1, 'Brick brown', holes)
        for (a, b, za, zb) in holes:
            window(mb, G, a, b, za, zb, off=-0.2, sill=False)
            reveals(mb, G, a, b, za, zb, 0.2, mat='Brick brown')
    fp = Polygon([(XB, YS), (XE, YS), (XE, YN), (XB, YN)])
    under = fp.difference(Polygon([(XB - 1, ys), (xi, ys), (xi, yn), (XB - 1, yn)]))
    mb.polygon_face(under, Z_SOFFIT, 'Stone white', up=False)


def corners_led(mb):
    """warm LED lines down the white tower's corners and along the top of the frame"""
    for (x, y, z0) in ((XE, YS, Z_SOFFIT), (XB, YN, Z_SOFFIT), (XB, YS, BRICK_TOP), (XE, YN, Z20 - 0.1)):
        sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
        mb.box(x + sx * 0.01, y + sy * 0.01, z0, 0.05, 0.05, CROWN - z0, 'LED warm')
    ring = Polygon([(XB, YS), (XE, YS), (XE, YN), (XB, YN)])
    led = ring.buffer(0.035, join_style='mitre').difference(ring.buffer(-0.035, join_style='mitre'))
    gap = Face((XE, YN), (XB, YN)).quad(SLOT[0], SLOT[1], -1.0, 1.0)
    mb.prism(led.difference(gap), CROWN - 0.05, CROWN + 0.01, 'LED warm', 'LED warm')


# ---- the brick part ---------------------------------------------------------------------------------

def brick_part(mb, rnd, trees):
    """17 floors of dark grey brick at the north-west end (render 10), from the podium's roof; the
    windows where the plan has them (2 x 2 panes, 1.4 x 2.1 m, a white sill), on the north-west end a
    recess with French windows; a parapet and a roof terrace"""
    z0, z1 = level(4), BRICK_TOP
    faces = [
        (Face((XB, YBN), (XW, YBN)), [2.15, 4.86], False),      # north-east (set back)
        (Face((XW, YBN), (XW, YS)), [YBN + 0.05], True),          # north-west end
        (Face((XW, YS), (XB, YS)), [2.81, 5.65], False),          # south-west
    ]
    for F, cs, recess in faces:
        holes = []
        for f in range(4, BRICK_FLOORS + 1):
            z = level(f)
            for c in cs:
                if recess:
                    holes.append((c - 1.85, c + 1.85, z + 0.05, z + 2.75))
                else:
                    holes.append((c - 0.7, c + 0.7, z + 0.55, z + 2.65))
        holed_wall(mb, F, 0.0, F.L, 0.0, z0, z1, 'Brick brown', holes)
        for (a, b, za, zb) in holes:
            if not recess:
                window(mb, F, a, b, za, zb, off=-0.2)
                fbox(mb, F, a - 0.08, b + 0.08, -0.22, 0.06, za - 0.07, za, 'Stone white')
                reveals(mb, F, a, b, za, zb, 0.2, sill=False, mat='Brick brown')
            else:
                for (p, q) in ((a + 0.3, (a + b) / 2 - 0.15), ((a + b) / 2 + 0.15, b - 0.3)):
                    window(mb, F, p, q, za, zb, off=-0.9, sill=False)
                fwall(mb, F, a, b, -0.92, za, zb, 'Brick brown')
                reveals(mb, F, a, b, za, zb, 0.9, mat='Brick brown')
                rail(mb, F, a + 0.02, b - 0.02, -0.05, za, 1.0)
    roof = Polygon([(XW, YS), (XB, YS), (XB, YBN), (XW, YBN)])
    par = roof.difference(roof.buffer(-0.35, join_style='mitre'))
    mb.prism(par, BRICK_ROOF, BRICK_TOP, 'Brick brown', 'Stone white')
    mb.polygon_face(roof.buffer(-0.35, join_style='mitre'), BRICK_ROOF + 0.05, 'Deck wood')
    mb.prism(roof.buffer(-0.45, join_style='mitre'), z0, BRICK_ROOF, 'Panel white', None)
    for (x, y) in ((-16.2, -8.0), (-13.4, -8.0), (-16.2, 6.8), (-13.4, 6.8), (-14.8, -0.6)):
        mb.box(x, y, BRICK_ROOF, 1.6, 1.6, 0.6, 'Planter')
        mb.box(x, y, BRICK_ROOF + 0.6, 1.45, 1.45, 0.02, 'Shrub')
        trees.append((x, y, BRICK_ROOF + 0.6, rnd.uniform(2.8, 3.6)))


# ---- the podium (floors 1-3) --------------------------------------------------------------------------

def ring_faces(poly):
    c = list(orient(poly, 1.0).exterior.coords)[:-1]
    return [Face(a, b) for a, b in zip(c, c[1:] + c[:1]) if math.dist(a, b) > 0.05]


def blade(mb, F, u, w=0.3):
    """a white blade of the podium (render 10): 0.6 m proud under the parapet, tapering to the band
    over the shops"""
    extrude(mb, F, u - w / 2, u + w / 2, [(-0.05, 5.5), (0.18, 5.5), (0.6, 7.2), (0.6, 12.7), (-0.05, 12.7)], 'Stone white')


def podium(mb, outline):
    g = orient(Polygon(outline).buffer(0).simplify(0.05), 1.0)
    faces = ring_faces(g)
    run = 0.0
    M = 3.15
    for F in faces:
        L = F.L
        # floor 1: shop windows, black mullions every 1.58 m, a transom
        fwall(mb, F, 0, L, -0.25, 0.12, 4.7, 'Shop glass')
        fbox(mb, F, 0, L, -0.3, -0.2, 0.0, 0.15, 'Frame dark')
        fbox(mb, F, 0, L, -0.3, -0.2, 3.62, 3.68, 'Frame dark')
        k = math.ceil(run / (M / 2))
        while k * (M / 2) <= run + L:
            u = k * (M / 2) - run
            fbox(mb, F, max(0, u - 0.035), min(L, u + 0.035), -0.3, -0.18, 0.0, 4.7, 'Frame dark')
            k += 1
        # the band over the shops, floor 2's glass, the band at floor 3
        fbox(mb, F, 0, L, -0.3, 0.2, 4.7, 5.5, 'Stone white')
        fwall(mb, F, 0, L, -0.3, 5.5, 9.4, 'Shop glass')
        fbox(mb, F, 0, L, -0.35, -0.25, 7.4, 7.46, 'Frame dark')
        fbox(mb, F, 0, L, -0.3, 0.12, 9.4, 10.3, 'Stone white')
        # floor 3: brick, small windows between the pairs of blades
        holes = []
        k = math.ceil(run / M) - 1
        while k * M <= run + L and L > 3.0:
            # (none on the rounded end: its short facets cannot hold a flat window)
            c = k * M - run + 2.08
            if 0.7 < c < L - 0.7:
                holes.append((c - 0.6, c + 0.6, 10.75, 11.85))
            k += 1
        holed_wall(mb, F, 0, L, -0.3, 10.3, 12.7, 'Brick brown', holes)
        B = Face(F.p(0, -0.3), F.p(L, -0.3))
        for (a, b, za, zb) in holes:
            window(mb, B, a, b, za, zb, off=-0.15, sill=False)
            reveals(mb, B, a, b, za, zb, 0.15, mat='Brick brown')
        # the blades in pairs on the module (1.0 m apart)
        k = math.ceil((run - 1.0) / M)
        while k * M <= run + L:
            for off in (0.0, 1.0):
                u = k * M + off - run
                if 0.2 < u < L - 0.2:
                    blade(mb, F, u)
            k += 1
        # the parapet
        fbox(mb, F, 0, L, -0.35, 0.62, 12.7, 13.8, 'Stone white')
        run += L
    mb.polygon_face(g.buffer(-0.3), 0.13, 'Shop floor')
    tower = Polygon([(XW, YS), (XE, YS), (XE, YN), (XW, YN)])
    deck = g.buffer(-0.35).difference(tower.buffer(-0.05, join_style='mitre'))
    deck = deck.union(Polygon([(XW, YBN), (XB, YBN), (XB, YN), (XW, YN)]).intersection(g.buffer(-0.35)))
    mb.polygon_face(deck, level(4) + 0.02, 'Deck wood')
    # the closed box behind the podium's glass (its shops are drawn by the glass itself)
    mb.prism(g.buffer(-0.5), 0.13, level(4), 'Shop wall', None, None)
    return deck


# ---- the block ------------------------------------------------------------------------------------------

def build(mats, col, plan, put):
    """put(builder, name): turns the builder from the block frame onto the site and makes the
    object. Returns the info the viewer needs (outline, heights, trees)."""
    rnd = random.Random(27)
    trees = []
    mb = MeshBuilder()
    NEf = Face((XE, YN), (XB, YN))          # u from the east corner
    SEf = Face((XE, YS), (XE, YN))          # u from the south corner
    SWf = Face((XB, YS), (XE, YS))          # u from the west corner
    NWf = Face((XB, YN), (XB, YS))          # u from the north corner

    zb0, zb1 = BOX['z0'], BOX['z1']
    build_face(mb, NEf, NE, [(SLOT[0], SLOT[1], level(5) + 0.5, CROWN + 1.0), (0.0, BOX['ne'], zb0, zb1)], corner='start')
    build_face(mb, SEf, SE, [(BOX['se'], SEf.L, zb0, zb1)], corner='end')
    build_face(mb, SWf, sw_tiers())
    # the north-west face over the brick part, and beside its set-back face down to the soffit
    build_face(mb, NWf, {3: NW_T4}, z_from=BRICK_TOP + 0.3)
    fwall(mb, NWf, 0.0, NWf.L, 0.0, BRICK_TOP - 0.05, BRICK_TOP + 0.3, 'Stone white')
    fwall(mb, NWf, 0.0, YN - YBN, 0.0, Z_SOFFIT, BRICK_TOP, 'Stone white')
    slot(mb, NEf, *SLOT)
    loggia_box(mb)
    corner_square(mb, [TIERS[1], TIERS[3]])
    corners_led(mb)
    floor4_and_soffit(mb)
    # the closed box behind the openings (nothing shows through between the panes)
    core = Polygon([(XB + 0.45, YS + 0.45), (XE - 0.45, YS + 0.45), (XE - 0.45, YN - 0.45), (XB + 0.45, YN - 0.45)])
    mb.prism(core, Z_SOFFIT, Z20 - 0.1, 'Panel white', None, None)
    floor20(mb, rnd, trees)
    brick_part(mb, rnd, trees)
    deck = podium(mb, plan['23']['outline'])
    put(mb, 'K_block')

    # planters with small trees on the podium's deck at the rounded end
    pl = MeshBuilder()
    for q in getattr(deck, 'geoms', [deck]):
        if q.area < 30:
            continue
        b = q.buffer(-1.6)
        cc = b.centroid
        for (dx, dy) in ((0, 0), (4.5, 3.0), (-4.0, -3.0), (5.0, -4.5), (-3.5, 4.0)):
            p = (cc.x + dx, cc.y + dy)
            if b.contains(Point(p)):
                pl.box(p[0], p[1], level(4), 1.8, 1.8, 0.6, 'Planter')
                pl.box(p[0], p[1], level(4) + 0.6, 1.65, 1.65, 0.02, 'Shrub')
                trees.append((p[0], p[1], level(4) + 0.6, rnd.uniform(3.2, 4.0)))
    put(pl, 'K_planters')
    outline = [(XW, YS), (XE, YS), (XE, YN), (XW, YN)]
    return dict(outline=outline, podium=list(Polygon(plan['23']['outline']).buffer(0).exterior.coords)[:-1],
                top=CROWN, trees=trees, floors=20)
