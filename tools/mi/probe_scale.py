import sys, fitz, math
from shapely.geometry import MultiPoint
d = fitz.open(sys.argv[1]); p = d[1]
words = p.get_text('words')
for x in p.get_drawings():
    f = x.get('fill')
    if not f or tuple(round(v * 255) for v in f) != (76, 136, 165):
        continue
    P = []
    for it in x['items']:
        if it[0] == 'l': P += [it[1], it[2]]
        elif it[0] == 're': r = it[1]; P += [r.tl, r.tr, r.br, r.bl]
    r = x['rect']
    lab = [w[4] for w in words if r.x0 < (w[0]+w[2])/2 < r.x1 and r.y0 < (w[1]+w[3])/2 < r.y1 and len(w[4]) == 1 and w[4].isalpha()]
    mr = MultiPoint([(q.x, q.y) for q in P]).minimum_rotated_rectangle
    c = list(mr.exterior.coords)
    a = math.dist(c[0], c[1]); b = math.dist(c[1], c[2])
    print(lab[-1:] , round(max(a, b), 2), round(min(a, b), 2), 'pt', round(max(a,b)/min(a,b),3), 'hull area', round(MultiPoint([(q.x,q.y) for q in P]).convex_hull.area,1), 'mrr', round(mr.area,1))
