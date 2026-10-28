import sys, pymupdf, collections
d = pymupdf.open(sys.argv[1])
for n in map(int, sys.argv[2].split(',')):
    p = d[n - 1]
    dr = p.get_drawings()
    c = collections.Counter(); area = collections.defaultdict(float); bb = {}
    for x in dr:
        f = x.get('fill')
        key = ('F', tuple(round(v * 255) for v in f)) if f else ('S', tuple(round(v * 255) for v in (x.get('color') or (0, 0, 0))), round(x.get('width') or 0, 2))
        r = x['rect']; c[key] += 1; area[key] += r.width * r.height
        b = bb.get(key); bb[key] = r if b is None else b | r
    print('page', n, len(dr))
    for k, v in sorted(c.items(), key=lambda kv: -area[kv[0]])[:18]:
        print('  ', k, v, round(area[k]), [round(t) for t in bb[k]])
