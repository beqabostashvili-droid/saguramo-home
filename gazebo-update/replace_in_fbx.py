"""Swap the old slatted pergola in the Autodesk FBX for the new glazed gazebo.

  blender --background --python gazebo-update/replace_in_fbx.py -- <input.fbx> [out_dir]

Writes  <name>_new_gazebo_winter.fbx  (glass closed)
        <name>_new_gazebo_summer.fbx  (glass parked open)

The old pergola is the FBX nodes "Wood - Mahogany Vertical" and
"Glass - Mirror" (the FBX is grouped by material; both groups contain only
the pergola). Placement is NOT typed in: the pool water and the old pergola
are read from the imported geometry itself, and the gazebo model
(Saguramo_Gazebo.blend, X = u along the pool, Y = -w, origin pool centre,
Z 0 = terrace paving) is fitted onto them.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
GAZEBO_BLEND = os.path.join(HERE, "Saguramo_Gazebo.blend")
OLD_PERGOLA = ("Wood - Mahogany Vertical", "Glass - Mirror")
POOL_WATER = "Water - Wavy"
# gazebo footprint centre in gazebo-model coordinates (from build_gazebo.py)
GAZ_CENTRE_LOCAL = Vector(((-3.54 + 1.64) / 2, -(4.55 + 9.70) / 2))
OLD_GLASS_TOP_ABOVE_PAVING = 2.224 + 0.169   # measured in the viewer

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("usage: blender --background --python replace_in_fbx.py -- input.fbx [out_dir]")
src = os.path.abspath(argv[0])
out_dir = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.dirname(src)
base = os.path.splitext(os.path.basename(src))[0]


def world_verts(objs):
    pts = []
    for ob in objs:
        if ob.type != "MESH":
            continue
        mw = ob.matrix_world
        pts.extend(mw @ v.co for v in ob.data.vertices)
    return pts


def min_area_rect(pts):
    """Brute-force minimum-area rectangle in XY: (angle_rad, centre, length, width)."""
    best = None
    for i in range(0, 1800):
        a = math.radians(i / 10)
        c, s = math.cos(a), math.sin(a)
        us = [p.x * c + p.y * s for p in pts]
        ws = [-p.x * s + p.y * c for p in pts]
        area = (max(us) - min(us)) * (max(ws) - min(ws))
        if best is None or area < best[0]:
            uc, wc = (max(us) + min(us)) / 2, (max(ws) + min(ws)) / 2
            centre = Vector((uc * c - wc * s, uc * s + wc * c))
            best = (area, a, centre, max(us) - min(us), max(ws) - min(ws))
    _, a, centre, L, W = best
    if W > L:  # make `a` the long-axis direction
        a, L, W = a + math.pi / 2, W, L
    return a, centre, L, W


def objects_named(prefix):
    return [o for o in bpy.data.objects if o.name == prefix or o.name.startswith(prefix + ".")]


def build_variant(winter):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    scene = bpy.context.scene

    pool = objects_named(POOL_WATER)
    old = [o for n in OLD_PERGOLA for o in objects_named(n)]
    if not pool or not old:
        raise SystemExit(f"could not find pool ({len(pool)}) or old pergola ({len(old)}) objects")

    pool_pts = world_verts(pool)
    old_pts = world_verts(old)
    a, pool_c, pL, pW = min_area_rect(pool_pts)
    _, old_c, oL, oW = min_area_rect(old_pts)
    print(f"POOL water {pL:.2f} x {pW:.2f} m, axis {math.degrees(a):.2f} deg, centre {pool_c.x:.2f},{pool_c.y:.2f}")
    print(f"OLD pergola {oL:.2f} x {oW:.2f} m, centre {old_c.x:.2f},{old_c.y:.2f}")

    # choose the u sign so the gazebo centre lands where the old pergola is
    best = None
    for flip in (0.0, math.pi):
        rot = Matrix.Rotation(a + flip, 4, "Z")
        predicted = pool_c + (rot.to_3x3() @ GAZ_CENTRE_LOCAL.to_3d()).xy
        err = (predicted - old_c).length
        if best is None or err < best[0]:
            best = (err, rot)
    err, rot = best
    print(f"FIT gazebo centre vs old pergola centre: {err:.3f} m")
    if err > 0.25:
        raise SystemExit("fit error too large - model or measurements disagree, not exporting")

    glass_top = max(p.z for p in world_verts(objects_named("Glass - Mirror")))
    paving_z = glass_top - OLD_GLASS_TOP_ABOVE_PAVING
    print(f"PAVING level {paving_z:.3f}")
    M = Matrix.Translation((pool_c.x, pool_c.y, paving_z)) @ rot

    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)

    want = ["01 Gazebo structure", "02 Oak slat ceiling and lighting", "03 Glazing tracks",
            "04 Glass CLOSED - winter" if winter else "05 Glass PARKED - summer",
            "06 Dining - modern table and chairs", "07 Outdoor kitchen"]
    with bpy.data.libraries.load(GAZEBO_BLEND, link=False) as (src_data, dst):
        dst.collections = [c for c in src_data.collections if c in want]
    root = bpy.data.collections.new("NEW GAZEBO " + ("winter" if winter else "summer"))
    scene.collection.children.link(root)
    for c in dst.collections:
        root.children.link(c)
        for ob in list(c.objects):
            if ob.type != "MESH":
                bpy.data.objects.remove(ob, do_unlink=True)
                continue
            ob.matrix_world = M @ ob.matrix_world

    # FBX keeps plain colours only: bake procedural base colours to a flat value
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        p = m.node_tree.nodes.get("Principled BSDF")
        if p and p.inputs["Base Color"].is_linked:
            for l in list(p.inputs["Base Color"].links):
                m.node_tree.links.remove(l)
            p.inputs["Base Color"].default_value = (0.45, 0.28, 0.15, 1) if "Oak" in m.name else (0.6, 0.6, 0.6, 1)

    out = os.path.join(out_dir, f"{base}_new_gazebo_{'winter' if winter else 'summer'}.fbx")
    bpy.ops.export_scene.fbx(filepath=out, axis_forward="-Z", axis_up="Y",
                             path_mode="COPY", embed_textures=True,
                             mesh_smooth_type="FACE", use_mesh_modifiers=True)
    print("EXPORTED", out)


for winter in (True, False):
    build_variant(winter)
print("REPLACE_DONE")
