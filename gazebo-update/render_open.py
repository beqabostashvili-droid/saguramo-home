"""Render the gazebo with all glass parked open (summer), close-up views.

Run after build_gazebo.py:
  blender --background gazebo-update/Saguramo_Gazebo.blend --python gazebo-update/render_open.py
"""
import os

import bpy

OUT = os.path.dirname(os.path.abspath(__file__))
scene = bpy.context.scene
cols = bpy.data.collections
cols["04 Glass CLOSED - winter"].hide_render = True
cols["05 Glass PARKED - summer"].hide_render = False


def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    co = bpy.data.objects.new(name, cd)
    co.location = loc
    scene.collection.objects.link(co)
    tgt = bpy.data.objects.new(name + " target", None)
    tgt.location = target
    scene.collection.objects.link(tgt)
    c = co.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return co


views = [
    # from the west paving, three-quarter view
    # (model Y = -w, see build_gazebo.py)
    ("gazebo_open_corner.png", camera("Camera open corner", (-6.8, -2.3, 2.0), (-0.6, -7.6, 1.0), 20)),
    # inside, standing at the table, toward the pool with everything open
    ("gazebo_open_interior.png", camera("Camera open interior", (0.6, -8.3, 1.55), (-2.4, -2.0, 0.8), 18)),
]
for fname, cam in views:
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fname)
