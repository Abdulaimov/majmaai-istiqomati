"""Unwarp a planar facade of a render into a flat picture in metres (homography from 4 corners).

    tools/ab/py tools/mi/rect.py RENDER OUT W_M H_M PPM  x_tl,y_tl x_tr,y_tr x_br,y_br x_bl,y_bl
"""
import sys
import cv2
import numpy as np

src, out, W, H, ppm = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
pts = np.float32([[float(v) for v in a.split(',')] for a in sys.argv[6:10]])
img = cv2.imread(src)
dst = np.float32([[0, 0], [W * ppm, 0], [W * ppm, H * ppm], [0, H * ppm]])
M = cv2.getPerspectiveTransform(pts, dst)
r = cv2.warpPerspective(img, M, (int(W * ppm), int(H * ppm)), flags=cv2.INTER_CUBIC)
# metre grid every 1 m (faint) and 5 m (strong)
for x in range(0, int(W) + 1):
    cv2.line(r, (int(x * ppm), 0), (int(x * ppm), 6 if x % 5 else 18), (0, 0, 255), 1)
for y in range(0, int(H) + 1):
    cv2.line(r, (0, int(y * ppm)), (6 if y % 5 else 18, int(y * ppm)), (0, 0, 255), 1)
cv2.imwrite(out, r)
print(r.shape)
