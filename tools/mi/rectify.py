"""Unwarp a planar facade of a client render into metres, with the floor grid and the plan's
window openings drawn over it (the check of a measured facade layout).

    tools/ab/py tools/mi/rectify.py RENDER OUT --corners x,y x,y x,y x,y --u0 U0 --u1 U1 --z0 Z0 --z1 Z1
        [--ppm 40] [--floors 16.2:3.0] [--open u0:u1,...] [--flip]

corners: top-left, top-right, bottom-right, bottom-left of the facade in the render (px); they are
the facade points (u0, z1), (u1, z1), (u1, z0), (u0, z0) in metres (u along the facade, z height).
"""
import argparse
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('out')
ap.add_argument('--corners', nargs=4, required=True)
for k in ('u0', 'u1', 'z0', 'z1'):
    ap.add_argument(f'--{k}', type=float, required=True)
ap.add_argument('--ppm', type=float, default=40)
ap.add_argument('--floors', default=None)
ap.add_argument('--open', default='')
a = ap.parse_args()
pts = np.float32([[float(v) for v in c.split(',')] for c in a.corners])
W, H = a.u1 - a.u0, a.z1 - a.z0
k = a.ppm
dst = np.float32([[0, 0], [W * k, 0], [W * k, H * k], [0, H * k]])
M = cv2.getPerspectiveTransform(pts, dst)
img = cv2.imread(a.src)
r = cv2.warpPerspective(img, M, (int(W * k), int(H * k)), flags=cv2.INTER_CUBIC)
ov = r.copy()
Y = lambda z: int(round((a.z1 - z) * k))
X = lambda u: int(round((u - a.u0) * k))
if a.floors:
    z, step = map(float, a.floors.split(':'))
    n = 5
    while z < a.z1:
        cv2.line(ov, (0, Y(z)), (r.shape[1], Y(z)), (0, 0, 255), 1)
        cv2.putText(ov, str(n), (3, Y(z) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        z += step
        n += 1
for s in filter(None, a.open.split(',')):
    u0, u1 = map(float, s.split(':'))
    cv2.rectangle(ov, (X(u0), 0), (X(u1), r.shape[0]), (255, 160, 0), 1)
for u in range(int(a.u0), int(a.u1) + 1):
    cv2.line(ov, (X(u), r.shape[0] - (14 if u % 5 else 34)), (X(u), r.shape[0]), (0, 200, 0), 2)
    if u % 5 == 0:
        cv2.putText(ov, str(u), (X(u) + 2, r.shape[0] - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 160, 0), 1)
r = cv2.addWeighted(ov, 0.75, r, 0.25, 0)
cv2.imwrite(a.out, r)
print(r.shape)
