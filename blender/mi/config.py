"""The residential complex «Маҷмааи истиқоматӣ» (Dushanbe): eleven blocks on the genplan.

Site metres: x east, y north, origin at the middle of block К (tools/mi/genplan.py -> build/genplan.json).
Block frame (every block): x along the block, + towards the end the genplan's long axis points away
from (for К: + to the south-east, the podium's rounded end), y across, + to the left of +x (for К:
the north-east, the inner street). site(x, y) turns and moves a block point onto the site.

Heights (no sections in the drawings): floor 1 at 0.000 and floor 2 at +5.100 on the plans; the rest
read off the client renders 9 and 10 (rectified facades, tools/mi/rectify.py): floor 3 at 9.7, then
3.0 m a floor (127.5 px a floor against 210-218 px a shop floor at block К's corner on render 10;
the balcony slabs and the spandrels of the windows sit on that grid). The genplan writes "18/20" on К:
the tower has 20 floors (roof of floor 20 at 63.7, its crown frame to 67.4); the brick part at its
north-west end shows 17 floors on render 10 (window rows; top 12.1 m under the crown).
"""
import json
import math
import os

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
GENPLAN = os.path.join(ROOT, 'build', 'genplan.json')

FLOOR1 = 5.1
FLOOR2 = 4.6
STOREY = 3.0


def level(n):
    """height of floor n above the street (n may be fractional above floor 3)"""
    if n <= 1:
        return 0.0
    if n == 2:
        return FLOOR1
    return FLOOR1 + FLOOR2 + (n - 3) * STOREY


def genplan():
    with open(GENPLAN) as f:
        return json.load(f)


# Latin keys (file and object names) -> the letters on the drawings
LETTERS = {'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Е', 'J': 'Ж', 'I': 'И', 'K': 'К', 'L': 'Л', 'M': 'М'}
KEY = {v: k for k, v in LETTERS.items()}
# the block built in full now; the others stand as white models of their size until they are made
FULL = ('K',)


def frame(gp_block):
    """(centre, angle) of a block's frame: +x the reverse of the genplan's long axis direction"""
    cx, cy = gp_block['centre']
    return (cx, cy), math.radians(gp_block['rot'] - 180.0)


def to_site(frame_, x, y):
    (cx, cy), a = frame_
    c, s = math.cos(a), math.sin(a)
    return (cx + c * x - s * y, cy + s * x + c * y)
