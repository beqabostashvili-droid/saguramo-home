"""Living room + kitchen interior, warm-minimal style, Saguramo house.

Source: saguramo_sa11.10.2026ff.pdf (floor plan with furniture). Plan read on
its grid: axes 3.0 | 6.2 | 4.7 m across, rows 7.2 | 3.7 | 4.4 | 4.9 m down.
Coordinates: X = plan x (0 = left grid axis), Y = -plan y (0 = top axis),
Z = 0 finished floor. Ceiling 3.00 m (owner height used in the earlier model).

Rooms from the plan:
  საერთო ოთახი 54.67 m2 -> interior X -1.65..6.05, plan y 0.10..7.20
  სამზარეულო   21.86 m2 -> interior X 6.35..10.75, plan y 4.10..8.70
Assumed (not readable from the plan): window and door heights, the
1.6 m opening between living room and kitchen, glazing widths.

  blender --background --python interior-update/build_living_kitchen.py
"""
import math
import os

import bpy

OUT = os.path.dirname(os.path.abspath(__file__))
H = 3.00

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "Living + kitchen"


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


def box(name, x0, y0, z0, x1, y1, z1, material, c, soft=0.0):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(material)
    c.objects.link(ob)
    if soft:
        b = ob.modifiers.new("soft", "BEVEL")
        b.width = soft
        b.segments = 3
        b.limit_method = "NONE"
    return ob


def cyl(name, x, y, z0, z1, r, material, c, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=z1 - z0, location=(x, y, (z0 + z1) / 2))
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    for uc in ob.users_collection:
        uc.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def sphere(name, x, y, z, r, material, c):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x, y, z), segments=24, ring_count=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    for uc in ob.users_collection:
        uc.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def wall_x(name, x0, x1, y0, y1, openings, material, c):
    """Wall running along X (thickness y0..y1). openings: (a0, a1, sill, head)."""
    cuts = sorted(openings)
    a = x0
    for (o0, o1, sill, head) in cuts:
        if o0 > a:
            box(f"{name} pier", a, y0, 0, o0, y1, H, material, c)
        if sill > 0:
            box(f"{name} sill wall", o0, y0, 0, o1, y1, sill, material, c)
        if head < H:
            box(f"{name} lintel", o0, y0, head, o1, y1, H, material, c)
        a = o1
    if a < x1:
        box(f"{name} pier", a, y0, 0, x1, y1, H, material, c)


def wall_y(name, y0, y1, x0, x1, openings, material, c):
    """Wall running along Y (thickness x0..x1). openings: (b0, b1, sill, head)."""
    cuts = sorted(openings)
    b = y0
    for (o0, o1, sill, head) in cuts:
        if o0 > b:
            box(f"{name} pier", x0, b, 0, x1, o0, H, material, c)
        if sill > 0:
            box(f"{name} sill wall", x0, o0, 0, x1, o1, sill, material, c)
        if head < H:
            box(f"{name} lintel", x0, o0, head, x1, o1, H, material, c)
        b = o1
    if b < y1:
        box(f"{name} pier", x0, b, 0, x1, y1, H, material, c)


def glazing_x(name, x0, x1, y, head, panels, c, sill=0.0):
    w = (x1 - x0) / panels
    box(f"{name} head frame", x0, y - 0.04, head - 0.06, x1, y + 0.04, head, black, c)
    box(f"{name} sill frame", x0, y - 0.04, sill, x1, y + 0.04, sill + 0.04, black, c)
    for i in range(panels + 1):
        xx = x0 + i * w
        box(f"{name} mullion {i}", xx - 0.025, y - 0.04, sill, xx + 0.025, y + 0.04, head, black, c)
    for i in range(panels):
        box(f"{name} glass {i}", x0 + i * w + 0.025, y - 0.006, sill + 0.04, x0 + (i + 1) * w - 0.025, y + 0.006, head - 0.06, glass, c)


def glazing_y(name, y0, y1, x, sill, head, panels, c):
    w = (y1 - y0) / panels
    box(f"{name} head frame", x - 0.04, y0, head - 0.06, x + 0.04, y1, head, black, c)
    box(f"{name} sill frame", x - 0.04, y0, sill, x + 0.04, y1, sill + 0.05, black, c)
    for i in range(panels + 1):
        yy = y0 + i * w
        box(f"{name} mullion {i}", x - 0.04, yy - 0.025, sill, x + 0.04, yy + 0.025, head, black, c)
    for i in range(panels):
        box(f"{name} glass {i}", x - 0.006, y0 + i * w + 0.025, sill + 0.05, x + 0.006, y0 + (i + 1) * w - 0.025, head - 0.06, glass, c)


def node_mat(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    build(m.node_tree, m.node_tree.nodes["Principled BSDF"])
    return m


# ---------------------------------------------------------------- materials
plaster = mat("Warm white plaster", (0.80, 0.77, 0.72), 0.85)
ceiling_m = mat("Ceiling white", (0.86, 0.85, 0.82), 0.9)
black = mat("Matte black metal", (0.02, 0.02, 0.022), 0.4, 0.6)
glass = mat("Window glass", (0.95, 0.98, 0.97), 0.0, **{"Transmission Weight": 1.0, "IOR": 1.5})
fabric_grey = mat("Sofa fabric warm grey", (0.36, 0.33, 0.30), 0.95)
boucle = mat("Boucle off-white", (0.78, 0.75, 0.69), 1.0)
linen = mat("Rug oat", (0.55, 0.49, 0.41), 1.0)
stone = mat("Light stone worktop", (0.74, 0.72, 0.68), 0.3)
travertine = mat("Travertine coffee table", (0.70, 0.62, 0.52), 0.45)
leaf = mat("Plant leaves", (0.07, 0.17, 0.05), 0.6)
pot = mat("Clay pot", (0.42, 0.27, 0.19), 0.8)
grass_m = mat("Grass", (0.10, 0.19, 0.06), 0.9)
terrace_m = mat("Terrace stone", (0.55, 0.53, 0.50), 0.7)
art_m = mat("Art print", (0.62, 0.45, 0.32), 0.8)
leather = mat("Cognac leather", (0.33, 0.15, 0.06), 0.55)
warm_led = bpy.data.materials.new("Warm LED")
warm_led.use_nodes = True
_p = warm_led.node_tree.nodes["Principled BSDF"]
_p.inputs["Emission Color"].default_value = (1.0, 0.8, 0.55, 1)
_p.inputs["Emission Strength"].default_value = 20.0


def _oak(nt, p, planks=True, tone=((0.36, 0.22, 0.12), (0.52, 0.35, 0.20))):
    n, l = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 10.0
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 18.0, 1.0)
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*tone[0], 1)
    ramp.color_ramp.elements[1].color = (*tone[1], 1)
    l.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    if planks:
        br = n.new("ShaderNodeTexBrick")
        br.offset = 0.5
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 1.8
        br.inputs["Row Height"].default_value = 0.22
        br.inputs["Mortar Size"].default_value = 0.0015
        br.inputs["Bias"].default_value = 0.0
        l.new(tc.outputs["Object"], br.inputs["Vector"])
        l.new(ramp.outputs["Color"], br.inputs["Color1"])
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = 0.12
        l.new(ramp.outputs["Color"], mix.inputs["A"])
        mix.inputs["B"].default_value = (*tone[1], 1)
        l.new(mix.outputs["Result"], br.inputs["Color2"])
        br.inputs["Mortar"].default_value = (0.12, 0.08, 0.05, 1)
        l.new(br.outputs["Color"], p.inputs["Base Color"])
    else:
        l.new(ramp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.45


oak_floor = node_mat("Oak plank floor", lambda nt, p: _oak(nt, p, True))
oak = node_mat("Light oak veneer", lambda nt, p: _oak(nt, p, False, ((0.45, 0.30, 0.17), (0.62, 0.45, 0.28))))
walnut = node_mat("Smoked oak table", lambda nt, p: _oak(nt, p, False, ((0.16, 0.09, 0.05), (0.28, 0.17, 0.10))))


def _tiles(nt, p):
    n, l = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    br = n.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 1.2
    br.inputs["Row Height"].default_value = 0.6
    br.inputs["Mortar Size"].default_value = 0.002
    br.inputs["Color1"].default_value = (0.62, 0.59, 0.54, 1)
    br.inputs["Color2"].default_value = (0.66, 0.63, 0.58, 1)
    br.inputs["Mortar"].default_value = (0.42, 0.40, 0.37, 1)
    l.new(tc.outputs["Object"], br.inputs["Vector"])
    l.new(br.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.35


kitchen_floor = node_mat("Kitchen porcelain 60x120", _tiles)

# ---------------------------------------------------------------- shell
c_shell = coll("01 Shell - walls, floor, ceiling")
# Read from the PDF at 129 px/m (axis E = x 0, top axis = plan y 0):
LX0, LX1, LY0, LY1 = -1.67, 6.05, -7.22, -0.16     # living interior (54.7 m2)
KX0, KX1, KY0, KY1 = 6.36, 11.05, -8.93, -4.28     # kitchen interior (21.8 m2)
EXT, INT = 0.30, 0.15

box("Floor living | oak planks", LX0, LY0, -0.02, LX1, LY1, 0.0, oak_floor, c_shell)
box("Floor open link living-kitchen", LX1, LY0, -0.02, KX0, KY1, 0.0, oak_floor, c_shell)
box("Floor kitchen | porcelain", KX0, KY0, -0.02, KX1, KY1, 0.0, kitchen_floor, c_shell)
box("Structural slab", LX0 - EXT, KY0 - INT, -0.25, KX1 + EXT, LY1 + EXT, -0.02, plaster, c_shell)
box("Ceiling slab", LX0 - EXT, KY0 - INT, H, KX1 + EXT, LY1 + EXT, H + 0.25, ceiling_m, c_shell)

# Openings exactly as drawn. The plan shows NO windows in the west wall.
#   north: door by the basement stair (x 0.16..1.05) + sliding glazing x 2.09..6.05 to the 41 m2 terrace
#   east:  glazing plan y 0.17..3.66 to the covered dining terrace (19.8 m2)
#   east:  open link to the kitchen plan y 4.28..7.22 (no wall drawn)
#   south: open to the corridor x 4.50..6.05
wall_x("Living north wall (terrace)", LX0 - EXT, KX0, LY1, LY1 + EXT,
       [(0.16, 1.05, 0.0, 2.20), (2.09, 6.05, 0.0, 2.70)], plaster, c_shell)
wall_y("Living west wall (solid)", LY0 - INT, LY1 + EXT, LX0 - EXT, LX0, [], plaster, c_shell)
wall_x("Living south wall", LX0 - EXT, LX1, LY0 - INT, LY0, [(4.50, 6.05, 0.0, H)], plaster, c_shell)
wall_y("Living / kitchen line", KY0 - INT, LY1 + EXT, LX1, KX0,
       [(-8.27, -7.37, 0.0, 2.20), (-7.22, -4.28, 0.0, H), (-3.66, -0.17, 0.0, 2.70)], plaster, c_shell)
# kitchen: sliding glazing x 7.75..10.78 to the dining terrace, one small window east, door from the corridor
wall_x("Kitchen north wall (dining terrace)", KX0, KX1 + EXT, KY1, KY1 + EXT, [(7.75, 10.78, 0.0, 2.40)], plaster, c_shell)
wall_y("Kitchen east wall", KY0 - INT, KY1 + EXT, KX1, KX1 + EXT, [(-5.13, -4.28, 0.90, 2.30)], plaster, c_shell)
wall_x("Kitchen south wall", KX0, KX1 + EXT, KY0 - INT, KY0, [], plaster, c_shell)

c_win = coll("02 Glazing")
glazing_x("Living door by stair", 0.16, 1.05, LY1 + EXT / 2, 2.20, 1, c_win)
glazing_x("Living terrace sliding glazing", 2.09, 6.05, LY1 + EXT / 2, 2.70, 3, c_win)
glazing_y("Living glazing to dining terrace", -3.66, -0.17, (LX1 + KX0) / 2, 0.0, 2.70, 3, c_win)
glazing_x("Kitchen sliding glazing to dining terrace", 7.75, 10.78, KY1 + EXT / 2, 2.40, 3, c_win)
glazing_y("Kitchen east window", -5.13, -4.28, KX1 + EXT / 2, 0.90, 2.30, 1, c_win)
box("Kitchen door leaf (open)", LX1 + 0.02, -8.27, 0.0, LX1 + 0.06, -7.37, 2.18, oak, c_win)
for (x0, y0, x1, y1) in [(LX0, LY0, LX0 + 0.012, LY1), (LX0, LY0, 4.5, LY0 + 0.012)]:
    box("Skirting oak", x0, y0, 0, x1, y1, 0.07, oak, c_shell)

# outside: terrace + covered dining terrace + garden
c_out = coll("03 Outside (schematic)")
box("Terrace 41 m2", LX0 - EXT, LY1 + EXT, -0.22, KX1 + EXT, 4.9, -0.02, terrace_m, c_out)
box("Covered dining terrace floor", KX0 - 0.31, KY1 + EXT, -0.22, KX1 + EXT, LY1 + EXT, -0.02, terrace_m, c_out)
box("Outdoor table (covered terrace)", 9.2, -2.95, 0.72, 11.0, -1.95, 0.76, walnut, c_out)
box("Outdoor table base", 9.9, -2.75, 0.0, 10.3, -2.15, 0.72, black, c_out)
box("Corridor floor (to living)", 4.50, KY0 - INT, -0.02, LX1, LY0, 0.0, oak_floor, c_out)
box("Corridor wall W", 4.35, KY0 - INT, 0, 4.50, LY0 - INT, H, plaster, c_out)
box("Garden", -40, -40, -0.6, 40, 40, -0.25, grass_m, c_out)
box("Garden hedge north", -14, 7.5, -0.3, 16, 8.3, 1.6, leaf, c_out, 0.2)
box("Garden hedge west", -9.0, -14, -0.3, -8.2, 7.5, 1.6, leaf, c_out, 0.2)
box("Garden hedge east", 15.0, -14, -0.3, 15.8, 7.5, 1.6, leaf, c_out, 0.2)
# corridor / service rooms behind the south doors (plan: corridor 30 m2, pantry, laundry)
box("Corridor floor", LX0 - EXT, -10.6, -0.02, KX1 + EXT, KY0 - INT, 0.0, oak_floor, c_out)
box("Corridor ceiling", LX0 - EXT, -10.6, H, KX1 + EXT, KY0 - INT, H + 0.25, ceiling_m, c_out)
box("Corridor back wall", LX0 - EXT, -10.75, 0, KX1 + EXT, -10.6, H, plaster, c_out)
box("Corridor side wall W", LX0 - EXT, -10.6, 0, LX0, LY0 - INT, H, plaster, c_out)
box("Corridor side wall E", KX1, -10.6, 0, KX1 + EXT, KY0 - INT, H, plaster, c_out)

# ---------------------------------------------------------------- living furniture (positions from the plan)
c_liv = coll("04 Living room furniture")
box("Rug", -0.25, -5.95, 0.0, 2.35, -1.4, 0.012, linen, c_liv)
sx = 2.09   # sofa back line; plan sofa x 1.20..2.09, plan y 2.65..4.67, faces west
SY0, SY1 = -4.67, -2.65
box("Sofa base", sx - 0.9, SY0, 0.0, sx, SY1, 0.42, fabric_grey, c_liv, 0.03)
box("Sofa back", sx - 0.22, SY0, 0.42, sx, SY1, 0.82, fabric_grey, c_liv, 0.05)
box("Sofa arm N", sx - 0.9, SY1 - 0.2, 0.42, sx, SY1 + 0.005, 0.62, fabric_grey, c_liv, 0.05)
box("Sofa arm S", sx - 0.9, SY0 - 0.005, 0.42, sx, SY0 + 0.2, 0.62, fabric_grey, c_liv, 0.05)
cw = (SY1 - SY0 - 0.4) / 3
for i in range(3):
    y0 = SY0 + 0.2 + i * cw
    box(f"Sofa seat cushion {i + 1}", sx - 0.88, y0 + 0.005, 0.42, sx - 0.22, y0 + cw - 0.005, 0.55, fabric_grey, c_liv, 0.05)
    box(f"Sofa back cushion {i + 1}", sx - 0.40, y0 + 0.01, 0.55, sx - 0.22, y0 + cw - 0.01, 0.92, fabric_grey, c_liv, 0.07)
# coffee table: plan x 0.29..0.89, plan y 3.05..4.26
box("Coffee table travertine", 0.29, -4.26, 0.0, 0.89, -3.05, 0.36, travertine, c_liv, 0.01)
for k, yc in enumerate((-2.06, -5.27)):  # plan armchairs x 0.19..1.0, facing each other
    box(f"Armchair {k + 1} seat", 0.19, yc - 0.4, 0.0, 1.0, yc + 0.4, 0.40, boucle, c_liv, 0.08)
    by = yc + (0.28 if yc > -3 else -0.28)
    box(f"Armchair {k + 1} back", 0.19, by - 0.12, 0.40, 1.0, by + 0.12, 0.78, boucle, c_liv, 0.08)
# sideboard on the west wall (plan: small unit at plan y 6.18..7.0)
box("Sideboard oak", LX0, -7.0, 0.0, LX0 + 0.38, -6.18, 0.62, oak, c_liv, 0.005)
box("Art print", LX0 + 0.005, -7.05, 1.2, LX0 + 0.03, -6.13, 2.0, art_m, c_liv)
box("Art frame", LX0 + 0.003, -7.07, 1.18, LX0 + 0.028, -6.11, 2.02, black, c_liv)
# floor lamp + plants
cyl("Floor lamp stem", 2.05, -4.95, 0.0, 1.55, 0.012, black, c_liv)
cyl("Floor lamp shade", 2.05, -4.95, 1.45, 1.75, 0.2, boucle, c_liv)
def plant(name, x, y, h, c):
    cyl(f"{name} pot", x, y, 0.0, 0.42, 0.2, pot, c)
    cyl(f"{name} stem", x, y, 0.42, h - 0.3, 0.012, walnut, c, 8)
    for k, (dx, dy, dz, rr) in enumerate([(0.0, 0.0, 0, 0.26), (0.18, 0.05, -0.25, 0.2), (-0.15, 0.12, -0.35, 0.18),
                                           (0.05, -0.18, -0.15, 0.19), (-0.1, -0.08, 0.18, 0.16)]):
        s = sphere(f"{name} leaves {k}", x + dx, y + dy, h + dz, rr, leaf, c)
        s.scale = (1.0, 1.0, 0.75)


plant("Plant 1", -1.25, -0.6, 1.55, c_liv)
plant("Plant 2", 1.57, -0.55, 1.25, c_liv)

# dining for 8 (plan: table x 3.55..4.56, plan y 1.26..3.78)
c_din = coll("05 Dining")
TX0, TX1, TY0, TY1 = 3.55, 4.56, -3.78, -1.26
box("Dining table top smoked oak", TX0, TY0, 0.72, TX1, TY1, 0.76, walnut, c_din, 0.004)
box("Dining table base", (TX0 + TX1) / 2 - 0.12, TY0 + 0.35, 0.0, (TX0 + TX1) / 2 + 0.12, TY1 - 0.35, 0.72, walnut, c_din)


def chair(name, cx, cy, face, c):
    """face: direction the sitter looks, one of +x/-x."""
    w = 0.46
    x0, x1 = cx - 0.24, cx + 0.24
    y0, y1 = cy - w / 2, cy + w / 2
    for i, (lx, ly) in enumerate([(x0, y0), (x1 - 0.025, y0), (x0, y1 - 0.025), (x1 - 0.025, y1 - 0.025)]):
        box(f"{name} leg {i}", lx, ly, 0, lx + 0.025, ly + 0.025, 0.44, black, c)
    box(f"{name} seat", x0, y0, 0.44, x1, y1, 0.48, leather, c, 0.01)
    bx = x0 if face > 0 else x1 - 0.03
    box(f"{name} back", bx, y0, 0.62, bx + 0.03, y1, 0.86, leather, c, 0.01)
    box(f"{name} back post L", bx, y0, 0.48, bx + 0.03, y0 + 0.025, 0.86, black, c)
    box(f"{name} back post R", bx, y1 - 0.025, 0.48, bx + 0.03, y1, 0.86, black, c)


for i in range(4):
    cy = TY0 + (TY1 - TY0) * (i + 0.5) / 4
    chair(f"Dining chair W{i + 1}", TX0 - 0.18, cy, +1, c_din)
    chair(f"Dining chair E{i + 1}", TX1 + 0.18, cy, -1, c_din)
box("Linear pendant", (TX0 + TX1) / 2 - 0.04, TY0 + 0.2, 1.62, (TX0 + TX1) / 2 + 0.04, TY1 - 0.2, 1.68, black, c_din)
box("Linear pendant LED", (TX0 + TX1) / 2 - 0.03, TY0 + 0.22, 1.615, (TX0 + TX1) / 2 + 0.03, TY1 - 0.22, 1.62, warm_led, c_din)
for yy in (TY0 + 0.3, TY1 - 0.3):
    box("Pendant cable", (TX0 + TX1) / 2 - 0.003, yy - 0.003, 1.68, (TX0 + TX1) / 2 + 0.003, yy + 0.003, H, black, c_din)

# ---------------------------------------------------------------- kitchen
c_kit = coll("06 Kitchen")
D = 0.62
# L-shaped run as drawn: south wall x 7.25..11.05 (sink), east wall plan y 5.13..8.31 (hob + fridge column)
SX0 = 7.25
box("Kitchen plinth south", SX0, KY0, 0, KX1, KY0 + D - 0.06, 0.10, black, c_kit)
box("Kitchen base units south", SX0, KY0, 0.10, KX1, KY0 + D, 0.88, oak, c_kit)
for i in range(int((KX1 - D - SX0) / 0.6)):
    xx = SX0 + (i + 1) * 0.6
    box(f"Front joint S{i}", xx - 0.002, KY0 + D, 0.10, xx + 0.002, KY0 + D + 0.002, 0.88, black, c_kit)
box("Worktop south stone", SX0 - 0.02, KY0, 0.88, KX1, KY0 + D + 0.02, 0.92, stone, c_kit)
box("Stone backsplash south", SX0 - 0.02, KY0, 0.92, KX1, KY0 + 0.02, 1.55, stone, c_kit)
box("Open shelf oak", 8.4, KY0, 1.85, 10.2, KY0 + 0.28, 1.89, oak, c_kit)
box("Undermount sink", 7.5, KY0 + 0.12, 0.70, 8.1, KY0 + 0.50, 0.921, black, c_kit)
box("Tap column", 7.78, KY0 + 0.05, 0.92, 7.82, KY0 + 0.09, 1.25, black, c_kit)
box("Tap spout", 7.785, KY0 + 0.05, 1.21, 7.815, KY0 + 0.32, 1.25, black, c_kit)
EX0 = KX1 - 0.58
box("Kitchen plinth east", EX0 + 0.06, KY0 + D, 0, KX1, -6.37, 0.10, black, c_kit)
box("Kitchen base units east", EX0, KY0 + D, 0.10, KX1, -6.37, 0.88, oak, c_kit)
box("Worktop east stone", EX0 - 0.02, KY0 + D, 0.88, KX1, -6.37, 0.92, stone, c_kit)
box("Stone backsplash east", KX1 - 0.02, KY0 + D, 0.92, KX1, -6.37, 1.55, stone, c_kit)
box("Induction hob", EX0 + 0.08, -7.46, 0.92, KX1 - 0.08, -6.84, 0.926, black, c_kit)
box("Wall hood", EX0 + 0.05, -7.6, 2.0, KX1, -6.7, 2.3, black, c_kit)
box("Hood chimney", KX1 - 0.3, -7.3, 2.3, KX1, -7.0, H, black, c_kit)
box("Fridge column black", EX0, -6.37, 0, KX1, -5.13, 2.40, black, c_kit)
box("Fridge column oak top", EX0, -6.37, 2.40, KX1, -5.13, H, oak, c_kit)
# kitchen table for 6 (plan: x 7.56..9.42, plan y 5.98..6.80)
KTX0, KTX1, KTY0, KTY1 = 7.56, 9.42, -6.80, -5.98
box("Kitchen table oak", KTX0, KTY0, 0.72, KTX1, KTY1, 0.76, oak, c_kit, 0.004)
for lx in (KTX0 + 0.1, KTX1 - 0.14):
    box("Kitchen table leg frame", lx, KTY0 + 0.08, 0.0, lx + 0.04, KTY1 - 0.08, 0.72, black, c_kit)
for i in range(3):
    cx = KTX0 + (KTX1 - KTX0) * (i + 0.5) / 3
    for side, cy, rot in (("N", KTY1 + 0.2, -1), ("S", KTY0 - 0.2, 1)):
        x0, x1 = cx - 0.22, cx + 0.22
        y0, y1 = cy - 0.22, cy + 0.22
        for j, (lx, ly) in enumerate([(x0, y0), (x1 - 0.025, y0), (x0, y1 - 0.025), (x1 - 0.025, y1 - 0.025)]):
            box(f"Kitchen chair {side}{i} leg {j}", lx, ly, 0, lx + 0.025, ly + 0.025, 0.45, black, c_kit)
        box(f"Kitchen chair {side}{i} seat", x0, y0, 0.45, x1, y1, 0.48, oak, c_kit, 0.006)
        by = y1 - 0.03 if rot < 0 else y0
        box(f"Kitchen chair {side}{i} back", x0, by, 0.62, x1, by + 0.03, 0.82, oak, c_kit, 0.006)
for i, px in enumerate((8.1, 8.9)):
    cyl(f"Kitchen pendant cable {i}", px, -6.39, 1.75, H, 0.003, black, c_kit, 8)
    sphere(f"Kitchen pendant globe {i}", px, -6.39, 1.62, 0.15, warm_led, c_kit)

# ---------------------------------------------------------------- lights
c_light = coll("07 Lights")


def spot(name, x, y, energy=55):
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy = energy
    ld.color = (1.0, 0.85, 0.66)
    ld.spot_size = math.radians(80)
    ld.spot_blend = 0.6
    ob = bpy.data.objects.new(name, ld)
    ob.location = (x, y, H - 0.02)
    c_light.objects.link(ob)
    box(name + " trim", x - 0.05, y - 0.05, H - 0.006, x + 0.05, y + 0.05, H, warm_led, c_light)


for x in (-0.6, 1.3, 3.2, 5.1):
    for y in (-1.6, -4.0, -6.2):
        spot(f"Downlight living {x},{y}", x, y)
for x in (7.3, 8.8, 10.1):
    for y in (-5.0, -7.6):
        spot(f"Downlight kitchen {x},{y}", x, y, 45)

world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
sky = world.node_tree.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(28)
    sky.sun_rotation = math.radians(160)
except (TypeError, AttributeError):
    pass
world.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.6

sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = 4.0
sun.angle = math.radians(1.0)
so = bpy.data.objects.new("Sun", sun)
so.rotation_euler = (math.radians(62), 0, math.radians(200))   # low sun through the terrace glazing
scene.collection.objects.link(so)
# soft fill at the big glazing (acts like a sky portal)
fl = bpy.data.lights.new("Glazing fill", "AREA")
fl.shape = "RECTANGLE"
fl.size, fl.size_y = 3.9, 2.5
fl.energy = 700
fl.color = (0.92, 0.95, 1.0)
fo = bpy.data.objects.new("Glazing fill", fl)
fo.location = (4.07, LY1 + 0.6, 1.4)
fo.rotation_euler = (math.radians(-90), 0, 0)   # shine into the room (-Y)
scene.collection.objects.link(fo)
fl2 = bpy.data.lights.new("Kitchen glazing fill", "AREA")
fl2.shape = "RECTANGLE"
fl2.size, fl2.size_y = 3.0, 2.2
fl2.energy = 400
fl2.color = (0.92, 0.95, 1.0)
fo2 = bpy.data.objects.new("Kitchen glazing fill", fl2)
fo2.location = (9.26, KY1 + 0.6, 1.3)
fo2.rotation_euler = (math.radians(-90), 0, 0)
scene.collection.objects.link(fo2)
fl3 = bpy.data.lights.new("East glazing fill", "AREA")
fl3.shape = "RECTANGLE"
fl3.size, fl3.size_y = 2.5, 3.4
fl3.energy = 450
fl3.color = (0.92, 0.95, 1.0)
fo3 = bpy.data.objects.new("East glazing fill", fl3)
fo3.location = (6.9, -1.9, 1.4)
fo3.rotation_euler = (0, math.radians(90), 0)    # shine into the room (-X)
scene.collection.objects.link(fo3)


def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    co = bpy.data.objects.new(name, cd)
    co.location = loc
    scene.collection.objects.link(co)
    t = bpy.data.objects.new(name + " target", None)
    t.location = target
    scene.collection.objects.link(t)
    c = co.constraints.new("TRACK_TO")
    c.target = t
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return co


cams = [
    ("living_toward_lounge.png", camera("Cam living toward lounge", (5.7, -6.7, 1.45), (-0.6, -2.4, 0.95), 17)),
    ("living_toward_dining.png", camera("Cam living toward dining", (-1.3, -6.8, 1.45), (4.6, -1.6, 1.0), 17)),
    ("kitchen.png", camera("Cam kitchen", (6.75, -4.45, 1.5), (9.9, -8.3, 0.95), 16)),
]

r = scene.render
r.engine = "CYCLES"
scene.cycles.samples = int(os.environ.get("SAMPLES", "160"))
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 8
r.resolution_x, r.resolution_y = 1600, 1000
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [
    i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items] else "None"
scene.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.3"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Saguramo_Living_Kitchen.blend"))
only = os.environ.get("ONLY")
for fname, cam in cams:
    if only and only not in fname:
        continue
    scene.camera = cam
    r.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fname)
print("INTERIOR_DONE")
