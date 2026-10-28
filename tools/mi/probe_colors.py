import sys, pymupdf, collections
from PIL import Image, ImageDraw
d = pymupdf.open(sys.argv[1]); p = d[1]
dr = p.get_drawings()
groups = collections.defaultdict(list)
for x in dr:
    f = x.get('fill')
    if f is None: continue
    key = (tuple(round(v * 255) for v in f), round(x.get('fill_opacity') or 1, 2))
    groups[key].append(x)
S = 2.0
for i, (key, xs) in enumerate(sorted(groups.items(), key=lambda kv: -sum(x['rect'].width * x['rect'].height for x in kv[1]))):
    area = sum(x['rect'].width * x['rect'].height for x in xs)
    if area < 50: continue
    im = Image.new('RGB', (int(1190 * S * 0.56), int(842 * S)), 'white'); dd = ImageDraw.Draw(im)
    for x in xs:
        for it in x['items']:
            pts = []
            if it[0] == 'l': pts = [it[1], it[2]]
            elif it[0] == 're': r = it[1]; pts = [r.tl, r.tr, r.br, r.bl, r.tl]
            elif it[0] == 'qu': q = it[1]; pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
            if pts: dd.line([(q.x * S, q.y * S) for q in pts], fill=key[0], width=3)
        r = x['rect']; 
    print(i, key, len(xs), round(area), 'closePath' , sum(1 for x in xs if x.get('closePath')))
    im.thumbnail((500, 700)); im.save(f'{sys.argv[2]}/c{i:02d}.png')
