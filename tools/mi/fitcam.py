"""Fit a client render's camera (level, two-point perspective with a shifted principal point) to
image points of block К's corners: position, heading, focal length, principal point.

    tools/ab/py tools/mi/fitcam.py
"""
import math
import numpy as np
from scipy.optimize import least_squares

A = math.radians(127.0 - 180.0)
c, s = math.cos(A), math.sin(A)


def site(x, y, z):
    return np.array([c * x - s * y, s * x + c * y, z])


XB, XE, YS, YN, ZS, ZC = -10.98, 18.22, -11.22, 11.18, 15.23, 67.42
RENDERS = {
    'r10': [((XE, YN, ZC), (871, 345)), ((XB, YN, ZC), (1793, 831)), ((XB, YN, ZS), (1792, 2650)),
            ((XE, YN, ZS), (871, 2563)), ((XE, YS, ZC), (458, 695)), ((XE, YS, ZS), (459, 2606)),
            ((XE, YN, 0.0), (871, 3207))],
    'r9': [((XE, YS, ZC), (2367, 1131)), ((XE, YN, ZC), (2910, 931)), ((XE, YN, ZS), (2910, 2622)),
           ((XE, YS, ZS), (2368, 2659)), ((XB, YN, ZC), (3335, 1236))],
}
GUESS = {'r10': [126.0, 11.1, 4.0, math.atan2(0.201, -0.978), 4014, 2470, 3040],
         'r9': [141.1, -54.8, 5.3, math.atan2(0.259, -0.966), 4054, 2470, 2945]}


def project(p, P):
    X, Y, Z, th, f, cx, cy = p
    F = np.array([math.cos(th), math.sin(th)])
    R = np.array([math.sin(th), -math.cos(th)])
    d = P[:2] - np.array([X, Y])
    xc, zc = d @ R, d @ F
    yc = P[2] - Z
    return np.array([cx + f * xc / zc, cy - f * yc / zc])


for name, pts in RENDERS.items():
    P3 = [site(*a) for a, _ in pts]
    uv = [np.array(b, float) for _, b in pts]

    def res(p):
        return np.concatenate([project(p, P) - q for P, q in zip(P3, uv)])
    g = np.array(GUESS[name], float)
    # (the principal point's x only loosely: renders are often cropped)
    r = least_squares(res, g, x_scale=[10, 10, 1, 0.05, 100, 100, 100])
    p = r.x
    err = np.abs(res(p)).reshape(-1, 2)
    fwd = (math.cos(p[3]), math.sin(p[3]))
    print(name, 'pos', [round(v, 2) for v in p[:3]], 'fwd', [round(v, 4) for v in fwd], 'f', round(p[4], 1),
          'cx', round(p[5], 1), 'cy', round(p[6], 1), 'max err px', round(err.max(), 1), 'rms', round(float(np.sqrt((err ** 2).mean())), 1))
