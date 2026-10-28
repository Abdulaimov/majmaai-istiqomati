"""Quick geometry stills of build/mi.blend (workbench, flat colours, shadows).
    blender -b build/mi.blend -P blender/mi_shot.py -- OUT_DIR x,y,z:tx,ty,tz:lens [...]"""
import math, os, sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'MATERIAL'
sh.show_shadows = True
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sc.display.light_direction = (0.45, -0.55, 0.7)
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.75, 0.82, 0.9)
for i, v in enumerate(argv[1:]):
    a, b, lens = v.split(':')
    loc = tuple(map(float, a.split(','))); tgt = tuple(map(float, b.split(',')))
    cd = bpy.data.cameras.new(f'c{i}'); cd.lens = float(lens); cd.clip_end = 5000
    ob = bpy.data.objects.new(f'c{i}', cd); sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = ob
    sc.render.filepath = os.path.join(out, f'shot{i}.png')
    bpy.ops.render.render(write_still=True)
