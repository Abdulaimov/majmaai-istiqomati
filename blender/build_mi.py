"""Build the «Маҷмааи истиқоматӣ» complex in Blender: block К in full, the other ten blocks and the
genplan's buildings as a white model, the site from the genplan.

    blender/export_mi.sh                     # -> public/models/mi.glb, src/model/complex.json
    blender -b -P blender/build_mi.py -- --out build/mi [--render build/mi.png --view k_ne]

Inputs: build/genplan.json (tools/mi/genplan.py) and build/plan_K.json (tools/mi/plans.py).
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from complex import geom  # noqa: E402
from complex.geom import get_collection, make_object  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

VIEWS = {
    # roughly render 10 (the north-east face of К from across the inner street) and render 4 (above)
    'k_ne': dict(location=(62.0, 34.0, 4.0), target=(0.0, 0.0, 34.0), lens=24.0),
    'k_air': dict(location=(110.0, -120.0, 150.0), target=(0.0, 0.0, 20.0), lens=35.0),
    'top': dict(location=(-60.0, 110.0, 700.0), target=(-60.0, 110.1, 0.0), lens=30.0),
}


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='build/mi')
    p.add_argument('--render')
    p.add_argument('--view', default='k_ne')
    p.add_argument('--res', default='1600x1000')
    p.add_argument('--samples', type=int, default=32)
    p.add_argument('--no-site', action='store_true')
    p.add_argument('--no-glb', action='store_true')
    return p.parse_args(argv)


def add_view(scene, name, location, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.5
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    return ob


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    from mi.materials import build_materials
    from mi.config import FULL, KEY, LETTERS, frame, genplan, level, to_site
    from mi import block_k, massing
    mats = build_materials()
    geom.TREE_LOG = []
    gp = genplan()
    with open(os.path.join(ROOT, 'build', 'plan_K.json')) as f:
        plan = json.load(f)
    root = get_collection('Complex')
    towers = []
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    footprints = []

    for letter, b in sorted(gp['blocks'].items(), key=lambda kv: KEY[kv[0]]):
        key = KEY[letter]
        fr = frame(b)
        lo, hi = b['floors']
        info = dict(key=key, letter=letter, label=f'Блок {letter}', tj=f'Блоки {letter}', centre=b['centre'],
                    rot=round(math.degrees(fr[1]), 2), floors=hi, floors_low=lo, full=key in FULL)
        if key == 'K':
            def put(mb, name, fr=fr):
                mb.verts = [(*to_site(fr, v[0], v[1]), v[2]) for v in mb.verts]
                ob = make_object(name, mb.to_mesh(name, mats), root)
                ob['block'] = key
            r = block_k.build(mats, root, plan, put)
            info['outline'] = [list(map(lambda v: round(v, 3), to_site(fr, x, y))) for x, y in r['outline']]
            info['podium'] = [list(map(lambda v: round(v, 3), to_site(fr, x, y))) for x, y in r['podium']]
            info['top'] = round(r['top'], 2)
            for (x, y, z, h) in r['trees']:
                X, Y = to_site(fr, x, y)
                geom.TREE_LOG.append([round(X, 2), round(Y, 2), round(z, 2), h, round(h * 0.33, 2), 'small'])
            footprints.append(Polygon(info['podium']).buffer(0))
        else:
            mb = geom.MeshBuilder()
            top = massing.block(mb, b['ring'], (lo, hi))
            ob = make_object(f'{key}_model', mb.to_mesh(f'{key}_model', mats), root)
            ob['block'] = key
            info['outline'] = b['ring']
            info['top'] = round(top, 2)
            footprints.append(Polygon(b['ring']).buffer(0.7, join_style='mitre'))
        towers.append(info)
    # the podiums between the blocks of a row (the genplan's links): white model, two floors
    mb = geom.MeshBuilder()
    for p in gp['classes'].get('podium', []):
        g = Polygon(p['ring']).buffer(0)
        if g.area > 100 and not g.intersects(footprints[[t['key'] for t in towers].index('K')].buffer(2)):
            massing.grooved(mb, g, 0.0, level(3), 5.1)
            footprints.append(g)
    make_object('Links_model', mb.to_mesh('Links_model', mats), root)

    built = unary_union(footprints)
    site = None
    if not args.no_site:
        from mi import site as site_mod
        site = site_mod.build_site(mats, get_collection('Site'), gp, built, built.buffer(3.0))

    for n, v in VIEWS.items():
        add_view(scene, n, **v)
    out = os.path.abspath(os.path.join(ROOT, args.out))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out + '.blend', compress=True)
    info = dict(site_centre=[0.0, 0.0], towers=towers, people=site['people'] if site else [],
                trees_placed=geom.TREE_LOG + (site['trees'] if site else []), tree_protos=[], trees=[],
                cars=site['cars'] if site else [], benches=site['benches'] if site else [],
                labels=site['labels'] if site else [], lamps=site['lamps'] if site else [], shops=[],
                region=site['region'] if site else None)
    with open(out + '.json', 'w') as f:
        json.dump(info, f, ensure_ascii=False)
    print('towers', len(towers), 'trees', len(info['trees_placed']), 'cars', len(info['cars']), 'people', len(info['people']),
          'lamps', len(info['lamps']))
    if not args.no_glb:
        bpy.ops.export_scene.gltf(filepath=out + '.glb', export_format='GLB', export_apply=True,
                                  export_cameras=False, export_lights=False, export_extras=True)


if __name__ == '__main__':
    main()
