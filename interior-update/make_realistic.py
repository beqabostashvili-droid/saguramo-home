"""Realistic pass over the living room + kitchen scene.

Takes Saguramo_Living_Kitchen.blend (from build_living_kitchen.py) and
  - lights it with a real sky photo (Poly Haven HDRI alps_field),
  - swaps flat materials for scanned PBR textures (floor, walls, oak, stone, fabric),
  - swaps block furniture for real models (armchairs, coffee table, media
    cabinet, plants, vases, kitchen pendants),
  - adds sheer curtains at the terrace glazing.
Assets: assets/polyhaven (CC0), fetched by fetch_polyhaven.py.

  blender --background interior-update/Saguramo_Living_Kitchen.blend --python interior-update/make_realistic.py
Env: SAMPLES (default 256), ONLY=<part of output name>, RES=<percent>.
"""
import glob
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(os.path.dirname(HERE), "assets", "polyhaven")
scene = bpy.context.scene
H = 3.0


def tex_path(asset, key):
    hits = [p for p in glob.glob(os.path.join(PH, asset, "*")) if key.lower() in os.path.basename(p).lower()]
    if not hits:
        raise SystemExit(f"missing texture {asset} {key}")
    return hits[0]


def img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color:
        im.colorspace_settings.name = "Non-Color"
    return im


def pbr(mat_name, asset, scale=1.0, tint=None, desat=False, rough_mul=1.0, rotate=0.0, normal_strength=1.0):
    """Rebuild a material with box-projected scanned textures (object space, metres)."""
    m = bpy.data.materials.get(mat_name)
    if m is None:
        return
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ("OUTPUT_MATERIAL",):
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / scale, 1 / scale, 1 / scale)
    mp.inputs["Rotation"].default_value = (0, 0, rotate)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def t(key, nc):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img(tex_path(asset, key), nc)
        n.projection = "BOX"
        n.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    dif = t("diff", False)
    col = dif.outputs["Color"]
    if desat:
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = 0.0
        nt.links.new(col, hs.inputs["Color"])
        col = hs.outputs["Color"]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(col, mix.inputs["A"])
        mix.inputs["B"].default_value = (*tint, 1)
        col = mix.outputs["Result"]
    nt.links.new(col, p.inputs["Base Color"])
    rough = t("rough", True)
    if rough_mul != 1.0:
        mm = nt.nodes.new("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        mm.inputs[1].default_value = rough_mul
        nt.links.new(rough.outputs["Color"], mm.inputs[0])
        nt.links.new(mm.outputs["Value"], p.inputs["Roughness"])
    else:
        nt.links.new(rough.outputs["Color"], p.inputs["Roughness"])
    nor = t("nor_gl", True)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = normal_strength
    nt.links.new(nor.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    return p


# ---------------------------------------------------------------- materials
pbr("Oak plank floor", "laminate_floor_02", scale=2.0)
pbr("Warm white plaster", "beige_wall_001", scale=2.5, desat=True, tint=(1.24, 1.15, 1.0), normal_strength=0.4)
pbr("Light oak veneer", "white_oak_veneer", scale=1.2)
pbr("Smoked oak table", "oak_veneer_01", scale=1.2, tint=(0.55, 0.48, 0.42))
pbr("Light stone worktop", "marble_01", scale=1.5, rough_mul=0.5)
pbr("Sofa fabric warm grey", "rough_linen", scale=0.6, desat=True, tint=(0.62, 0.57, 0.51))
pbr("Boucle off-white", "wool_boucle", scale=0.5, desat=True, tint=(1.05, 1.0, 0.92))
pbr("Rug oat", "rough_linen", scale=0.35, desat=True, tint=(0.82, 0.74, 0.62), normal_strength=1.5)
pbr("Travertine coffee table", "marble_01", scale=0.8, tint=(1.0, 0.92, 0.82), rough_mul=0.7)
pbr("Kitchen porcelain 60x120", "marble_01", scale=3.0, desat=True, tint=(1.05, 1.02, 0.97), rough_mul=0.6)

# ---------------------------------------------------------------- colour scheme (owner's choice)
SCHEME = os.environ.get("SCHEME", "grey")
if SCHEME == "grey":
    # modern grey + black living room: large-format light-grey concrete-look tiles,
    # white walls, anthracite sofa, grey rug, black dining set and sideboard, grey marble
    p = pbr("Oak plank floor", "plastered_wall_04", scale=1.6, desat=True, tint=(0.80, 0.80, 0.79), rough_mul=0.75, normal_strength=0.3)
    nt = bpy.data.materials["Oak plank floor"].node_tree
    br = nt.nodes.new("ShaderNodeTexBrick")     # 120 x 120 cm tiles with 2 mm joints
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 1.2
    br.inputs["Row Height"].default_value = 1.2
    br.inputs["Mortar Size"].default_value = 0.0025
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0.55, 0.55, 0.55, 1)
    tcn = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tcn.outputs["Object"], br.inputs["Vector"])
    base_link = p.inputs["Base Color"].links[0]
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(base_link.from_socket, mul.inputs["A"])
    nt.links.new(br.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], p.inputs["Base Color"])
    p.inputs["Specular IOR Level"].default_value = 0.6
    pbr("Warm white plaster", "beige_wall_001", scale=2.5, desat=True, tint=(1.42, 1.42, 1.40), normal_strength=0.3)
    pbr("Sofa fabric warm grey", "rough_linen", scale=0.6, desat=True, tint=(0.16, 0.16, 0.17))
    pbr("Rug oat", "rough_linen", scale=0.35, desat=True, tint=(0.42, 0.42, 0.42), normal_strength=1.5)
    pbr("Travertine coffee table", "marble_01", scale=0.8, desat=True, tint=(1.15, 1.15, 1.15), rough_mul=0.4)
    pbr("Smoked oak table", "oak_veneer_01", scale=1.2, desat=True, tint=(0.09, 0.09, 0.09), rough_mul=0.8)
    lm = bpy.data.materials["Cognac leather"].node_tree.nodes["Principled BSDF"]
    lm.inputs["Base Color"].default_value = (0.11, 0.11, 0.115, 1)
    am = bpy.data.materials["Art print"].node_tree.nodes["Principled BSDF"]
    am.inputs["Base Color"].default_value = (0.32, 0.32, 0.33, 1)
    blk = bpy.data.materials["Matte black metal"]
    for ob in bpy.data.objects:
        if ob.name.startswith("Sideboard") or ob.name.startswith("Skirting"):
            ob.data.materials[0] = blk
    # kitchen in the same grey + black: matte mid-grey fronts, dark grey stone worktop,
    # light-grey porcelain floor, black table, dark leather chairs
    pbr("Light oak veneer", "plastered_wall_04", scale=3.0, desat=True, tint=(0.40, 0.40, 0.41), rough_mul=0.7, normal_strength=0.05)
    pbr("Light stone worktop", "marble_01", scale=1.5, desat=True, tint=(0.18, 0.18, 0.19), rough_mul=0.45)
    pbr("Kitchen porcelain 60x120", "marble_01", scale=3.0, desat=True, tint=(0.92, 0.92, 0.91), rough_mul=0.6)
    # matte versions: under the pendants a glossy black top mirrors the white ceiling and reads grey
    tbl = bpy.data.materials["Smoked oak table"].copy()
    tbl.name = "Kitchen table black oak"
    pbr(tbl.name, "oak_veneer_01", scale=1.2, desat=True, tint=(0.05, 0.05, 0.05), rough_mul=1.6)
    tbl.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    lea = bpy.data.materials["Cognac leather"].copy()
    lea.name = "Kitchen chair black leather"
    lp = lea.node_tree.nodes["Principled BSDF"]
    lp.inputs["Base Color"].default_value = (0.035, 0.035, 0.037, 1)
    lp.inputs["Roughness"].default_value = 0.75
    lp.inputs["Specular IOR Level"].default_value = 0.25
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.data.materials:
            continue
        if ob.name.startswith("Kitchen table"):
            ob.data.materials[0] = tbl
        elif ob.name.startswith("Kitchen chair") and ob.data.materials[0].name == "Light oak veneer":
            ob.data.materials[0] = lea
cm =bpy.data.materials["Ceiling white"].node_tree.nodes["Principled BSDF"]
cm.inputs["Base Color"].default_value = (0.9, 0.89, 0.86, 1)

# ---------------------------------------------------------------- remove block stand-ins
for ob in list(bpy.data.objects):
    n = ob.name
    if (n.startswith("Armchair") or n.startswith("Media console")
            or n.startswith("Plant ") or n.startswith("Kitchen pendant globe")
            or n.startswith("Garden hedge") or n.startswith("Floor lamp")):
        bpy.data.objects.remove(ob, do_unlink=True)

c_real = bpy.data.collections.new("08 Real models (Poly Haven CC0)")
scene.collection.children.link(c_real)


def place(asset, loc, rot_z_deg=0.0, height=None, width=None, name=None):
    """Import a glTF model, put its footprint centre at loc (x, y) on z=loc[2]."""
    path = glob.glob(os.path.join(PH, asset, "*.gltf"))[0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name or asset, None)
    c_real.objects.link(root)
    for o in new:
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        c_real.objects.link(o)
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    s = 1.0
    if height:
        s = height / (mx.z - mn.z)
    elif width:
        s = width / max(mx.x - mn.x, mx.y - mn.y)
    for o in new:
        if o.parent is root:
            o.location = (o.location - Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)))
    root.scale = (s, s, s)
    root.rotation_euler = (0, 0, math.radians(rot_z_deg))
    root.location = loc
    print("PLACED", asset, "size", tuple(round(v * s, 2) for v in (mx - mn)))
    return root


# lounge: two leather/oak armchairs facing each other across the coffee table (plan layout)
# positions from the plan (saguramo_sa11.10.2026ff.pdf)
place("modern_arm_chair_01", (0.595, -2.06, 0), rot_z_deg=0, name="Armchair N")
place("modern_arm_chair_01", (0.595, -5.27, 0), rot_z_deg=180, name="Armchair S")
place("ceramic_vase_03", (-1.48, -6.75, 0.62), height=0.42, name="Vase on sideboard")
place("ceramic_vase_01", (-1.48, -6.4, 0.62), height=0.26, name="Vase 2 on sideboard")
place("ceramic_vase_01", (4.05, -2.5, 0.76), height=0.3, name="Vase on dining table")
place("potted_plant_02", (-1.15, -0.7, 0), height=1.1, name="Plant NW corner")
place("potted_plant_02", (1.57, -0.6, 0), rot_z_deg=70, height=0.95, name="Plant by terrace door")
for i, px in enumerate((8.1, 8.9)):
    lamp = place("modern_ceiling_lamp_01", (px, -6.39, 1.5), width=0.30, name=f"Kitchen pendant {i + 1}")
    top = 1.5 + 0.30 * (1.55 / 0.70)  # model is 0.70 wide x 1.55 tall at native scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.003, depth=H - top, location=(px, -6.39, (top + H) / 2))
    cab = bpy.context.active_object
    cab.name = f"Kitchen pendant cable {i + 1}"
    cab.data.materials.append(bpy.data.materials["Matte black metal"])
    ld = bpy.data.lights.new(f"Pendant bulb {i + 1}", "POINT")
    ld.energy = 25
    ld.color = (1.0, 0.82, 0.6)
    ld.shadow_soft_size = 0.08
    lo = bpy.data.objects.new(f"Pendant bulb {i + 1}", ld)
    lo.location = (px, -6.39, 1.58)
    c_real.objects.link(lo)

# ---------------------------------------------------------------- sheer curtains at the terrace glazing
sheer = bpy.data.materials.new("Sheer linen curtain")
sheer.use_nodes = True
snt = sheer.node_tree
sp = snt.nodes["Principled BSDF"]
sp.inputs["Base Color"].default_value = (0.93, 0.91, 0.86, 1)
sp.inputs["Roughness"].default_value = 0.9
sp.inputs["Transmission Weight"].default_value = 0.0
mixs = snt.nodes.new("ShaderNodeMixShader")
trans = snt.nodes.new("ShaderNodeBsdfTranslucent")
trans.inputs["Color"].default_value = (0.95, 0.93, 0.88, 1)
transp = snt.nodes.new("ShaderNodeBsdfTransparent")
mix2 = snt.nodes.new("ShaderNodeMixShader")
mix2.inputs["Fac"].default_value = 0.45
snt.links.new(sp.outputs["BSDF"], mixs.inputs[1])
snt.links.new(trans.outputs["BSDF"], mixs.inputs[2])
mixs.inputs["Fac"].default_value = 0.5
snt.links.new(mixs.outputs["Shader"], mix2.inputs[1])
snt.links.new(transp.outputs["BSDF"], mix2.inputs[2])
out = next(n for n in snt.nodes if n.type == "OUTPUT_MATERIAL")
snt.links.new(mix2.outputs["Shader"], out.inputs["Surface"])
c_cur = bpy.data.collections.new("09 Curtains")
scene.collection.children.link(c_cur)
for k, (x0, x1) in enumerate([(1.15, 2.05)]):   # stacked on the solid wall left of the terrace glazing
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=2, size=1)
    cur = bpy.context.active_object
    cur.name = f"Sheer curtain stack {k + 1}"
    for uc in list(cur.users_collection):
        uc.objects.unlink(cur)
    c_cur.objects.link(cur)
    cur.scale = (x1 - x0, 1, 1)
    cur.rotation_euler = (math.radians(90), 0, 0)
    cur.dimensions = (x1 - x0, 2.85, 0)
    cur.location = ((x0 + x1) / 2, -0.32, 2.88 / 2 + 0.02)
    w = cur.modifiers.new("folds", "WAVE")
    w.use_x, w.use_y = True, False
    w.height, w.width, w.narrowness, w.speed = 0.045, 0.09, 1.0, 0.0
    w.use_normal = True
    cur.data.materials.append(sheer)
    box_rod = bpy.data.meshes.new("rod")
    rod = bpy.data.objects.new(f"Curtain track {k + 1}", box_rod)
box_track = None
bpy.ops.mesh.primitive_cube_add(size=1, location=(3.6, -0.32, 2.93))
trk = bpy.context.active_object
trk.name = "Ceiling curtain track"
trk.dimensions = (4.95, 0.04, 0.03)
trk.data.materials.append(bpy.data.materials["Matte black metal"])

# ---------------------------------------------------------------- world: real sky
world = scene.world
wnt = world.node_tree
for n in list(wnt.nodes):
    if n.type not in ("OUTPUT_WORLD", "BACKGROUND"):
        wnt.nodes.remove(n)
bg = next(n for n in wnt.nodes if n.type == "BACKGROUND")
env = wnt.nodes.new("ShaderNodeTexEnvironment")
env.image = img(glob.glob(os.path.join(PH, "alps_field", "*.hdr"))[0])
tc = wnt.nodes.new("ShaderNodeTexCoord")
mp = wnt.nodes.new("ShaderNodeMapping")
mp.inputs["Rotation"].default_value = (0, 0, math.radians(float(os.environ.get("HDRI_ROT", "200"))))
wnt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
wnt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
wnt.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0
# the HDRI carries the sky light; keep the sun lamp for crisp shadows, soften the fills
sun = bpy.data.objects["Sun"]
sun.data.energy = 3.0
for n in ("Glazing fill", "Kitchen glazing fill", "East glazing fill"):
    bpy.data.objects[n].data.energy *= 0.35
for ob in bpy.data.objects:
    if ob.type == "LIGHT" and ob.data.type == "SPOT":
        ob.data.energy *= 0.6

r = scene.render
scene.cycles.samples = int(os.environ.get("SAMPLES", "256"))
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 10
scene.cycles.transparent_max_bounces = 16
r.resolution_percentage = int(os.environ.get("RES", "100"))
scene.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.9"))
# sofa arms share faces with the base: nudge them out 5 mm to stop flicker
for ob in bpy.data.objects:
    if ob.name.startswith("Sofa arm"):
        ob.location.y += 0.005 if ob.name.endswith("N") else -0.005

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Saguramo_Living_Kitchen_real.blend"))
only = os.environ.get("ONLY")
for cam_name, fname in [("Cam living toward lounge", "real_living_toward_lounge.png"),
                        ("Cam living toward dining", "real_living_toward_dining.png"),
                        ("Cam kitchen", "real_kitchen.png")]:
    if only and only not in fname:
        continue
    scene.camera = bpy.data.objects[cam_name]
    base_ev = float(os.environ.get("EXPOSURE", "0.9"))
    scene.view_settings.exposure = base_ev + ((0.6 if SCHEME != "grey" else 0.25) if "kitchen" in fname else 0.15)
    r.filepath = os.path.join(HERE, fname)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fname)
print("REAL_DONE")
