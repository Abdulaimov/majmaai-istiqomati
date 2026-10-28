import sys, pymupdf
d = pymupdf.open(sys.argv[1])
for n in map(int, sys.argv[2].split(',')):
    p = d[n - 1]
    ws = p.get_text('words')
    nums = [(round(w[0]), round(w[1]), w[4]) for w in ws if w[4].replace(' ', '').isdigit() and len(w[4]) >= 3]
    # join "7" "500" pairs
    print('page', n)
    ws2 = sorted([w for w in ws if w[4].isdigit()], key=lambda w: (round(w[1]), w[0]))
    out = []
    i = 0
    while i < len(ws2):
        w = ws2[i]
        if i + 1 < len(ws2) and abs(ws2[i+1][1] - w[1]) < 2 and 0 < ws2[i+1][0] - w[2] < 6 and len(ws2[i+1][4]) == 3:
            out.append((round((w[0] + ws2[i+1][2]) / 2, 1), round((w[1] + w[3]) / 2, 1), w[4] + ws2[i+1][4])); i += 2
        else:
            out.append((round((w[0] + w[2]) / 2, 1), round((w[1] + w[3]) / 2, 1), w[4])); i += 1
    print([o for o in out if len(o[2]) >= 4])
    # axis bubbles: red circles
    circ = []
    for x in p.get_drawings():
        c = x.get('color')
        if c and tuple(round(v * 255) for v in c) == (168, 15, 2) and any(it[0] == 'c' for it in x['items']):
            r = x['rect']; circ.append((round((r.x0 + r.x1) / 2, 1), round((r.y0 + r.y1) / 2, 1), round(r.width, 1)))
    print('axes', sorted(circ))
