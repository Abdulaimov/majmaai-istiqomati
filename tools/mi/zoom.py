"""Crops of a render around points, with a pixel grid, to read exact coordinates.
    tools/ab/py tools/mi/zoom.py RENDER OUT_PREFIX R x,y [x,y ...]"""
import sys
import cv2
src, pre, R = sys.argv[1], sys.argv[2], int(sys.argv[3])
img = cv2.imread(src)
tiles = []
for a in sys.argv[4:]:
    x, y = map(int, a.split(','))
    c = img[y - R:y + R, x - R:x + R].copy()
    c = cv2.resize(c, (c.shape[1] * 2, c.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
    for k in range(0, 2 * R + 1, 10):
        col = (0, 0, 255) if (x - R + k) % 50 == 0 else (0, 200, 255)
        if (x - R + k) % 50 == 0:
            cv2.line(c, (k * 2, 0), (k * 2, 2 * R * 2), col, 1)
            cv2.putText(c, str(x - R + k), (k * 2 + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1)
        if (y - R + k) % 50 == 0:
            cv2.line(c, (0, k * 2), (2 * R * 2, k * 2), col, 1)
            cv2.putText(c, str(y - R + k), (2, k * 2 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1)
    cv2.putText(c, a, (4, 4 * R - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    tiles.append(c)
cv2.imwrite(pre + '.png', cv2.hconcat(tiles))
