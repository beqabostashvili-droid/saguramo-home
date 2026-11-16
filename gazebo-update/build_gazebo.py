"""Modern pool-side gazebo with frameless slide-and-turn glazing.

Replaces the existing mahogany slatted pergola next to the pool in
saguramoqq_31.10.2026.fbx (Autodesk Viewer link https://autode.sk/4tcUVqx).

All site positions were measured in that FBX by top-view hit tests along the
pool axis (u) and across it (w). Blender X = u, Y = w, Z = 0 at the terrace
paving (FBX y = -0.17). Origin = pool centre.

Measured (metres, +-0.03):
  existing pergola        X -3.54 .. 1.64   Y 4.55 .. 9.70   top +2.43
  pool water              X -5.38 .. 5.50   Y -2.92 .. 0.96  floor -1.50
  pool coping (0.30)      around the water
  timber deck             Y -7.65 .. -3.22
  terrace paving          X -7.65 .. 1.70 (gazebo side), strip to Y 2.80 east
  east retaining wall     X 1.70 .. 2.00, raised lawn behind ~ +1.7
  west wall + railing     X -7.95 .. -7.65, lawn below at -1.25
The new gazebo keeps exactly the existing footprint and height class; no
roof overhang, so nothing moves closer to the pool or the walls.

Run:
  blender --background --python gazebo-update/build_gazebo.py
"""
import math
import os

import bpy

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- gazebo
GX0, GX1 = -3.54, 1.64     # along the pool
GY0, GY1 = 4.55, 9.70      # away from the pool
POST = 0.12                # square steel post
CLEAR_H = 2.25             # floor to ceiling
ROOF_TOP = 2.45            # matches existing pergola top (~2.43)
GLASS_T = 0.010
TRACK_H = 0.04
PANELS = 6                 # per side -> ~0.82 m panels

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Gazebo"
scene.unit_settings.system = "METRIC"


def coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


def mat(name, color, rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        p.inputs[k].default_value = v
    return m


def box(name, x0, y0, z0, x1, y1, z1, material, collection):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    collection.objects.link(ob)
    return ob


def tex_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    build(m.node_tree)
    return m


# ---------------------------------------------------------------- materials
black_al = mat("Black aluminium / steel", (0.018, 0.018, 0.02), 0.35, 0.7)
fascia = mat("Anthracite fascia", (0.035, 0.037, 0.04), 0.4, 0.5)
glass = mat("Low-iron glass", (0.92, 0.96, 0.95), 0.0, 0.0,
            **{"Transmission Weight": 1.0, "IOR": 1.5})
water = mat("Pool water", (0.15, 0.55, 0.7), 0.02, 0.0,
            **{"Transmission Weight": 0.85, "IOR": 1.33})
pool_tile = mat("Pool lining", (0.55, 0.75, 0.8), 0.3)
coping = mat("Pool coping (white)", (0.85, 0.85, 0.83), 0.5)
granite = mat("Grey granite paving", (0.42, 0.42, 0.42), 0.6)
stucco = mat("White stucco walls", (0.82, 0.81, 0.78), 0.85)
grass = mat("Grass", (0.11, 0.2, 0.06), 0.9)
deck_m = mat("Mahogany deck", (0.16, 0.06, 0.03), 0.6)
cushion = mat("Outdoor fabric", (0.62, 0.6, 0.56), 0.9)
led = bpy.data.materials.new("Warm LED")
led.use_nodes = True
_p = led.node_tree.nodes["Principled BSDF"]
_p.inputs["Emission Color"].default_value = (1.0, 0.78, 0.5, 1)
_p.inputs["Emission Strength"].default_value = 25.0


def _wood(nt):
    n, l = nt.nodes, nt.links
    p = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.6, 14.0, 0.6)
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 8.0
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.30, 0.16, 0.07, 1)
    ramp.color_ramp.elements[1].color = (0.55, 0.34, 0.17, 1)
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], noise.inputs["Vector"])
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.55


wood = tex_mat("Oak ceiling and furniture", _wood)

# ---------------------------------------------------------------- site (measured)
c_site = coll("00 Site context - measured from FBX")
box("Ground (beyond measured area)", -40, -40, -1.60, 40, 40, -1.45, grass, c_site)
# pool
WX0, WX1, WY0, WY1, CW = -5.38, 5.50, -2.92, 0.96, 0.30
box("Paving east of pool (extent not measured)", WX1 + CW, -7.65, -0.20, 12.0, WY1 + CW, 0.0, granite, c_site)
box("Pool water", WX0, WY0, -1.45, WX1, WY1, -0.08, water, c_site)
box("Pool floor", WX0, WY0, -1.55, WX1, WY1, -1.50, pool_tile, c_site)
box("Pool coping south", WX0 - CW, WY0 - CW, -0.20, WX1 + CW, WY0, 0.0, coping, c_site)
box("Pool coping north", WX0 - CW, WY1, -0.20, WX1 + CW, WY1 + CW, 0.0, coping, c_site)
box("Pool coping west", WX0 - CW, WY0, -0.20, WX0, WY1, 0.0, coping, c_site)
box("Pool coping east", WX1, WY0, -0.20, WX1 + CW, WY1, 0.0, coping, c_site)
# timber deck on the far side of the pool
box("Timber deck", WX0 - CW, -7.65, -0.20, WX1 + CW, WY0 - CW, 0.0, deck_m, c_site)
# granite paving, gazebo side
box("Granite paving | gazebo terrace", -7.65, WY1 + CW, -0.20, 1.70, 9.70, 0.0, granite, c_site)
box("Granite paving | strip along pool", 1.70, WY1 + CW, -0.20, 12.0, 2.80, 0.0, granite, c_site)
box("Granite paving | west of pool", -7.65, -7.65, -0.20, WX0 - CW, WY1 + CW, 0.0, granite, c_site)
# east retaining wall and raised lawn (~+1.7)
box("East retaining wall", 1.70, 2.80, -0.20, 2.00, 9.90, 1.75, stucco, c_site)
box("Retaining wall along pool strip", 2.00, 2.80, -0.20, 12.0, 3.00, 1.75, stucco, c_site)
box("Raised lawn east", 2.00, 3.00, -0.30, 12.0, 14.0, 1.70, grass, c_site)
# west wall with railing, lawn below
box("West wall", -7.95, -7.65, -1.30, -7.65, 9.90, 0.0, stucco, c_site)
box("West railing top rail", -7.83, -7.65, 0.80, -7.77, 9.70, 0.84, black_al, c_site)
box("Lawn west (lower)", -20.0, -12.0, -1.40, -7.95, 16.0, -1.25, grass, c_site)
# back wall line and lawn behind gazebo
box("Back wall", -7.95, 9.70, -0.20, 2.00, 9.90, 0.30, stucco, c_site)
box("Lawn behind", -7.95, 9.90, -0.60, 2.00, 16.0, -0.33, grass, c_site)

# ---------------------------------------------------------------- structure
c_str = coll("01 Gazebo structure")
corners = [(GX0, GY0), (GX1 - POST, GY0), (GX1 - POST, GY1 - POST), (GX0, GY1 - POST)]
for i, (x, y) in enumerate(corners):
    box(f"Steel post 120x120 | {i + 1}", x, y, 0.0, x + POST, y + POST, CLEAR_H, black_al, c_str)

box("Roof deck", GX0, GY0, CLEAR_H, GX1, GY1, ROOF_TOP - 0.02, fascia, c_str)
box("Fascia south (pool side)", GX0, GY0, CLEAR_H - 0.02, GX1, GY0 + 0.03, ROOF_TOP, fascia, c_str)
box("Fascia north", GX0, GY1 - 0.03, CLEAR_H - 0.02, GX1, GY1, ROOF_TOP, fascia, c_str)
box("Fascia west", GX0, GY0, CLEAR_H - 0.02, GX0 + 0.03, GY1, ROOF_TOP, fascia, c_str)
box("Fascia east", GX1 - 0.03, GY0, CLEAR_H - 0.02, GX1, GY1, ROOF_TOP, fascia, c_str)
box("Gazebo floor | porcelain", GX0, GY0, 0.0, GX1, GY1, 0.01, coping, c_str)

c_ceil = coll("02 Oak slat ceiling and lighting")
slat_w, gap = 0.07, 0.03
x = GX0 + POST
k = 0
while x + slat_w <= GX1 - POST + 1e-6:
    box(f"Oak ceiling slat {k:02d}", x, GY0 + POST, CLEAR_H - 0.03, x + slat_w, GY1 - POST, CLEAR_H, wood, c_ceil)
    x += slat_w + gap
    k += 1
for i in range(2):
    for j in range(2):
        cx = GX0 + (GX1 - GX0) * (i + 1) / 3
        cy = GY0 + (GY1 - GY0) * (j + 1) / 3
        box(f"LED downlight {i}{j}", cx - 0.06, cy - 0.06, CLEAR_H - 0.035, cx + 0.06, cy + 0.06, CLEAR_H - 0.03, led, c_ceil)
        pl = bpy.data.lights.new(f"Downlight {i}{j}", "SPOT")
        pl.energy = 60
        pl.color = (1.0, 0.82, 0.62)
        pl.spot_size = math.radians(70)
        lo = bpy.data.objects.new(f"Downlight {i}{j}", pl)
        lo.location = (cx, cy, CLEAR_H - 0.05)
        c_ceil.objects.link(lo)

# ---------------------------------------------------------------- glazing
c_track = coll("03 Glazing tracks")
c_closed = coll("04 Glass CLOSED - winter")
c_open = coll("05 Glass PARKED - summer")

h = POST / 2
z0, z1 = 0.015, CLEAR_H - TRACK_H - 0.005
lenx = (GX1 - GX0) - 2 * POST
leny = (GY1 - GY0) - 2 * POST
pwx, pwy = lenx / PANELS, leny / PANELS
sides = {
    "south": dict(along="x", fixed=GY0 + h),
    "north": dict(along="x", fixed=GY1 - h),
    "west": dict(along="y", fixed=GX0 + h),
    "east": dict(along="y", fixed=GX1 - h),
}
for name, s in sides.items():
    f = s["fixed"]
    if s["along"] == "x":
        box(f"Top track {name}", GX0 + POST, f - 0.03, CLEAR_H - TRACK_H, GX1 - POST, f + 0.03, CLEAR_H, black_al, c_track)
        box(f"Floor track {name}", GX0 + POST, f - 0.02, 0.0, GX1 - POST, f + 0.02, 0.014, black_al, c_track)
        for i in range(PANELS):
            a0 = GX0 + POST + i * pwx
            box(f"Glass {name} {i + 1}", a0 + 0.002, f - GLASS_T / 2, z0, a0 + pwx - 0.002, f + GLASS_T / 2, z1, glass, c_closed)
    else:
        box(f"Top track {name}", f - 0.03, GY0 + POST, CLEAR_H - TRACK_H, f + 0.03, GY1 - POST, CLEAR_H, black_al, c_track)
        box(f"Floor track {name}", f - 0.02, GY0 + POST, 0.0, f + 0.02, GY1 - POST, 0.014, black_al, c_track)
        for i in range(PANELS):
            a0 = GY0 + POST + i * pwy
            box(f"Glass {name} {i + 1}", f - GLASS_T / 2, a0 + 0.002, z0, f + GLASS_T / 2, a0 + pwy - 0.002, z1, glass, c_closed)

# summer: slide-and-turn, each side parks at one corner (pinwheel)
pitch = 0.035
for i in range(PANELS):
    s = GX0 + POST + 0.03 + i * pitch            # south -> SW corner
    box(f"Parked glass south {i + 1}", s, GY0 + POST, z0, s + GLASS_T, GY0 + POST + pwx, z1, glass, c_open)
    y = GY1 - POST - 0.03 - i * pitch            # west -> NW corner
    box(f"Parked glass west {i + 1}", GX0 + POST, y - GLASS_T, z0, GX0 + POST + pwy, y, z1, glass, c_open)
    xx = GX1 - POST - 0.03 - i * pitch           # north -> NE corner
    box(f"Parked glass north {i + 1}", xx - GLASS_T, GY1 - POST - pwx, z0, xx, GY1 - POST, z1, glass, c_open)
    yy = GY0 + POST + 0.03 + i * pitch           # east -> SE corner
    box(f"Parked glass east {i + 1}", GX1 - POST - pwy, yy, z0, GX1 - POST, yy + GLASS_T, z1, glass, c_open)

# ---------------------------------------------------------------- furniture (scale)
c_furn = coll("06 Furniture (scale reference)")
cx, cy = (GX0 + GX1) / 2, (GY0 + GY1) / 2
tx0, ty0 = cx - 1.1, cy - 0.45
box("Dining table top", tx0, ty0, 0.72, tx0 + 2.2, ty0 + 0.9, 0.76, wood, c_furn)
for dx in (0.15, 1.97):
    box(f"Table leg {dx}", tx0 + dx, ty0 + 0.1, 0.0, tx0 + dx + 0.08, ty0 + 0.8, 0.72, black_al, c_furn)
for side, yb in (("pool side", ty0 - 0.55), ("back", ty0 + 1.05)):
    box(f"Bench {side}", tx0 + 0.1, yb, 0.42, tx0 + 2.1, yb + 0.4, 0.46, wood, c_furn)
    box(f"Bench legs {side}", tx0 + 0.2, yb + 0.05, 0.0, tx0 + 2.0, yb + 0.35, 0.42, black_al, c_furn)

# ---------------------------------------------------------------- world, cameras
world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
sky = world.node_tree.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(35)
    sky.sun_rotation = math.radians(210)
except (TypeError, AttributeError):
    pass
world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.35

sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = 3.5
sun.angle = math.radians(1.5)
so = bpy.data.objects.new("Sun", sun)
so.rotation_euler = (math.radians(50), 0, math.radians(200))
scene.collection.objects.link(so)


def camera(name, loc, target, lens=26):
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


cam_ext = camera("Camera from deck", (6.5, -8.5, 3.2), (-1.2, 5.5, 0.9), 24)
cam_top = camera("Camera plan", (-1.0, 2.5, 40.0), (-1.0, 2.5, 0.0), 50)
cam_top.data.type = "ORTHO"
cam_top.data.ortho_scale = 21
cam_int = camera("Camera interior to pool", (1.2, 9.25, 1.5), (-2.0, -1.0, 0.6), 18)

r = scene.render
r.engine = "CYCLES"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
r.resolution_x, r.resolution_y = 1600, 1000
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = -0.7


def set_state(winter):
    c_closed.hide_render = c_closed.hide_viewport = not winter
    c_open.hide_render = c_open.hide_viewport = winter


def render(cam, fname):
    scene.camera = cam
    r.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fname)


txt = bpy.data.texts.new("START HERE - gazebo")
txt.write(__doc__)

set_state(True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Saguramo_Gazebo.blend"))

if os.environ.get("GAZEBO_RENDER", "1") == "1":
    set_state(True)
    render(cam_ext, "gazebo_winter_closed.png")
    render(cam_int, "gazebo_interior_winter.png")
    set_state(False)
    render(cam_ext, "gazebo_summer_open.png")
    render(cam_top, "gazebo_plan.png")
    set_state(True)
print("GAZEBO_DONE")
