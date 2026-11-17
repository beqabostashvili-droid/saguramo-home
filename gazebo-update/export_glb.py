"""Export the gazebo model as one GLB for the web 3D viewer.

  blender --background gazebo-update/Saguramo_Gazebo.blend --python gazebo-update/export_glb.py

Both glass states are included; the web page shows one at a time by object
name ("Glass ..." = winter/closed, "Parked glass ..." = summer/open).
"""
import os

import bpy

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "saguramo_gazebo.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    p = m.node_tree.nodes.get("Principled BSDF")
    if p and p.inputs["Base Color"].is_linked:
        for link in list(p.inputs["Base Color"].links):
            m.node_tree.links.remove(link)
        p.inputs["Base Color"].default_value = (0.45, 0.28, 0.15, 1) if "Oak" in m.name else (0.66, 0.64, 0.6, 1)

for c in bpy.data.collections:
    c.hide_viewport = False
bpy.ops.object.select_all(action="DESELECT")
for ob in bpy.context.scene.objects:
    if ob.type == "MESH":
        ob.hide_set(False)
        ob.select_set(True)

bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_lights=False,
                          export_cameras=False)
print("GLB", OUT, os.path.getsize(OUT))
