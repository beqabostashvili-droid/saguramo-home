"""Export the new gazebo + measured pool terrace as Autodesk FBX files.

  blender --background gazebo-update/Saguramo_Gazebo.blend --python gazebo-update/export_gazebo_fbx.py

Writes Saguramo_Gazebo_winter.fbx (glass closed) and Saguramo_Gazebo_summer.fbx
(glass parked open). Meshes only, metres, Y-up (Autodesk convention).
Procedural colours are flattened, because FBX keeps plain colours only.
"""
import os

import bpy

OUT = os.path.dirname(os.path.abspath(__file__))
FLAT = {"Oak": (0.45, 0.28, 0.15, 1)}

for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    p = m.node_tree.nodes.get("Principled BSDF")
    if p and p.inputs["Base Color"].is_linked:
        for link in list(p.inputs["Base Color"].links):
            m.node_tree.links.remove(link)
        p.inputs["Base Color"].default_value = next(
            (c for k, c in FLAT.items() if k in m.name), (0.66, 0.64, 0.6, 1))

cols = bpy.data.collections
for c in cols:  # the saved file hides one glass state; hidden objects can't be selected
    c.hide_viewport = False
for winter in (True, False):
    keep_out = "05 Glass PARKED - summer" if winter else "04 Glass CLOSED - winter"
    bpy.ops.object.select_all(action="DESELECT")
    n = 0
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or any(c.name == keep_out for c in ob.users_collection):
            continue
        ob.hide_set(False)
        ob.select_set(True)
        n += 1
    out = os.path.join(OUT, f"Saguramo_Gazebo_{'winter' if winter else 'summer'}.fbx")
    bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={"MESH"},
                             axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
                             mesh_smooth_type="FACE", path_mode="AUTO")
    print("EXPORTED", os.path.basename(out), n, "meshes", os.path.getsize(out), "bytes")
