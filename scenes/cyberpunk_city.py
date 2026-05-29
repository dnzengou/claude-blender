"""
CYBERPUNK CITY GENERATOR  —  Claude × Blender MCP Example
==========================================================
Run this in Blender's Script Editor (Text > Run Script)
OR send it via Claude Desktop → Blender MCP connector.

What it builds:
  • 7×7 procedural skyscraper grid, height-weighted by distance from center
  • Per-building neon accent strips + lit window arrays
  • Wet reflective ground plane
  • Atmospheric fog via World volume shader
  • 3 coloured area lights (magenta / cyan / orange)
  • Low-angle cinematic camera (28mm) with depth-of-field
  • Cycles render preset: 1920×1080, 128 samples, Filmic High Contrast + Bloom
"""

import bpy
import random
import math
from mathutils import Vector, Euler


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

SEED = 42
GRID = 7           # buildings per axis
SPACING = 7.0      # metres between building centres
NEON_PALETTE = [
    (1.00, 0.05, 0.70),   # hot pink
    (0.00, 0.85, 1.00),   # electric cyan
    (1.00, 0.40, 0.00),   # neon orange
    (0.55, 0.00, 1.00),   # deep violet
    (0.10, 1.00, 0.45),   # acid green
]


# ─────────────────────────────────────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes) + list(bpy.data.materials) \
                 + list(bpy.data.lights) + list(bpy.data.cameras) \
                 + list(bpy.data.curves):
        try:
            type(block).bl_rna  # exists check
            bpy.data.batch_remove([block])
        except Exception:
            pass


def link(node_tree, a, b):
    node_tree.links.new(a, b)


# ─────────────────────────────────────────────────────────────────────────────
# MATERIALS
# ─────────────────────────────────────────────────────────────────────────────

def make_emission(name: str, color: tuple, strength: float = 6.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out  = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value    = (*color, 1.0)
    emit.inputs['Strength'].default_value = strength
    link(nt, emit.outputs['Emission'], out.inputs['Surface'])
    return mat


def make_metal(name: str, base: tuple, roughness: float = 0.15):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out  = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*base, 1.0)
    bsdf.inputs['Metallic'].default_value   = 0.9
    bsdf.inputs['Roughness'].default_value  = roughness
    link(nt, bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def make_ground_material():
    mat = bpy.data.materials.new("Ground_Wet")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out   = nt.nodes.new('ShaderNodeOutputMaterial')
    mix   = nt.nodes.new('ShaderNodeMixShader')
    bsdf  = nt.nodes.new('ShaderNodeBsdfPrincipled')
    glass = nt.nodes.new('ShaderNodeBsdfGlass')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    bump  = nt.nodes.new('ShaderNodeBump')

    # Dark tarmac base
    bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.015, 1.0)
    bsdf.inputs['Metallic'].default_value   = 0.0
    bsdf.inputs['Roughness'].default_value  = 0.05

    # Thin water layer on top
    glass.inputs['Color'].default_value     = (0.6, 0.8, 1.0, 1.0)
    glass.inputs['Roughness'].default_value = 0.0
    glass.inputs['IOR'].default_value       = 1.33

    # Puddle mask via noise
    noise.inputs['Scale'].default_value     = 4.0
    noise.inputs['Detail'].default_value    = 8.0
    noise.inputs['Roughness'].default_value = 0.7
    bump.inputs['Strength'].default_value   = 0.3
    link(nt, noise.outputs['Fac'],    bump.inputs['Height'])
    link(nt, noise.outputs['Fac'],    mix.inputs['Fac'])
    link(nt, bump.outputs['Normal'],  bsdf.inputs['Normal'])
    link(nt, bsdf.outputs['BSDF'],    mix.inputs[1])
    link(nt, glass.outputs['BSDF'],   mix.inputs[2])
    link(nt, mix.outputs['Shader'],   out.inputs['Surface'])
    return mat


# ─────────────────────────────────────────────────────────────────────────────
# SCENE OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

def create_ground():
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Ground"
    obj.data.materials.append(make_ground_material())
    return obj


def create_building(loc: tuple, w: float, d: float, h: float):
    rng = random.Random(hash(loc))

    # ── main tower ──────────────────────────────────────────────────────────
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], h / 2))
    tower = bpy.context.active_object
    tower.name = f"Bld_{loc[0]:.0f}_{loc[1]:.0f}"
    tower.scale = (w, d, h)
    bpy.ops.object.transform_apply(scale=True)

    base_color = (
        rng.uniform(0.005, 0.03),
        rng.uniform(0.005, 0.03),
        rng.uniform(0.02,  0.07),
    )
    tower.data.materials.append(make_metal(f"Bld_Mat_{tower.name}", base_color, rng.uniform(0.05, 0.25)))

    # ── neon horizontal accent strips ────────────────────────────────────────
    num_strips = rng.randint(1, 3)
    for _ in range(num_strips):
        strip_z = rng.uniform(h * 0.15, h * 0.92)
        color   = rng.choice(NEON_PALETTE)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], strip_z))
        strip = bpy.context.active_object
        strip.scale = (w + 0.12, d + 0.12, 0.06)
        bpy.ops.object.transform_apply(scale=True)
        strip.data.materials.append(make_emission(f"Neon_{tower.name}_{_}", color, 10.0))

    # ── window grid (front face only) ────────────────────────────────────────
    cols   = max(1, int(w / 1.2))
    floors = max(1, int(h / 1.8))
    for fl in range(1, floors, 2):
        for col_i in range(cols):
            if rng.random() < 0.35:
                continue
            win_z = fl * 1.8 + rng.uniform(-0.1, 0.1)
            win_x = loc[0] - w / 2 + (col_i + 0.5) * (w / cols)
            win_y = loc[1] + d / 2 + 0.03
            color = rng.choice(NEON_PALETTE)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(win_x, win_y, win_z))
            win = bpy.context.active_object
            win.scale = (0.22, 0.03, 0.35)
            bpy.ops.object.transform_apply(scale=True)
            win.data.materials.append(
                make_emission(f"Win_{tower.name}_{fl}_{col_i}", color, rng.uniform(1.5, 4.0))
            )

    return tower


def create_city():
    rng = random.Random(SEED)
    half = (GRID * SPACING) / 2
    centre = GRID // 2

    for row in range(GRID):
        for col in range(GRID):
            if col == centre:          # central road gap
                continue
            dist = math.hypot(col - centre, row - centre)
            x = -half + col * SPACING + rng.uniform(-0.4, 0.4)
            y = -half + row * SPACING + rng.uniform(-0.4, 0.4)
            h = rng.uniform(6, 18) * (1.0 + max(0, (GRID / 2 - dist)) * 0.35)
            w = rng.uniform(1.8, 3.8)
            d = rng.uniform(1.8, 3.8)
            create_building((x, y, 0), w, d, h)


def create_flying_vehicles():
    rng = random.Random(SEED + 1)
    for i in range(6):
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        bpy.ops.curve.primitive_bezier_circle_add(
            radius=rng.uniform(8, 20),
            location=(rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(10, 28))
        )
        path = bpy.context.active_object
        path.name = f"FlightPath_{i}"
        path.data.path_duration = 250

        bpy.ops.mesh.primitive_capsule_add(
            radius=0.2, depth=1.2,
            location=path.location
        )
        vehicle = bpy.context.active_object
        vehicle.name = f"Speeder_{i}"
        color = rng.choice(NEON_PALETTE)
        vehicle.data.materials.append(make_emission(f"Speeder_Mat_{i}", color, 12.0))

        # Follow-path constraint
        fc = vehicle.constraints.new('FOLLOW_PATH')
        fc.target = path
        fc.use_curve_follow = True
        fc.offset = rng.uniform(0, 100)


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA
# ─────────────────────────────────────────────────────────────────────────────

def setup_camera():
    bpy.ops.object.camera_add(
        location=(28, -38, 12),
        rotation=Euler((math.radians(72), 0, math.radians(34)), 'XYZ')
    )
    cam = bpy.context.active_object
    cam.name = "CinematicCam"
    bpy.context.scene.camera = cam

    cam.data.lens              = 28       # wide-angle drama
    cam.data.dof.use_dof       = True
    cam.data.dof.focus_distance = 42
    cam.data.dof.aperture_fstop = 1.8


# ─────────────────────────────────────────────────────────────────────────────
# LIGHTING
# ─────────────────────────────────────────────────────────────────────────────

def setup_lighting():
    # Cold moonlight
    bpy.ops.object.light_add(type='SUN', location=(30, 30, 40))
    moon = bpy.context.active_object
    moon.name = "Moonlight"
    moon.data.color  = (0.45, 0.55, 1.0)
    moon.data.energy = 0.4
    moon.rotation_euler = Euler((math.radians(40), 0, math.radians(50)), 'XYZ')

    # Three coloured bounce lights at street level
    accent_lights = [
        ((-18,  0, 6), (1.0, 0.0, 0.7), "Light_Magenta"),
        (( 18,  0, 6), (0.0, 0.8, 1.0), "Light_Cyan"),
        ((  0, 18, 6), (1.0, 0.4, 0.0), "Light_Orange"),
    ]
    for pos, color, name in accent_lights:
        bpy.ops.object.light_add(type='AREA', location=pos)
        lt = bpy.context.active_object
        lt.name  = name
        lt.data.color  = color
        lt.data.energy = 800
        lt.data.size   = 12
        lt.rotation_euler = Euler((math.radians(45), 0, 0), 'XYZ')


# ─────────────────────────────────────────────────────────────────────────────
# WORLD (atmosphere)
# ─────────────────────────────────────────────────────────────────────────────

def setup_world():
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("CyberpunkWorld")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out     = nt.nodes.new('ShaderNodeOutputWorld')
    bg      = nt.nodes.new('ShaderNodeBackground')
    vol_abs = nt.nodes.new('ShaderNodeVolumePrincipled')

    # Near-black sky with faint blue tint
    bg.inputs['Color'].default_value    = (0.001, 0.001, 0.006, 1.0)
    bg.inputs['Strength'].default_value = 0.05
    link(nt, bg.outputs['Background'], out.inputs['Surface'])

    # Atmospheric haze via volume
    vol_abs.inputs['Density'].default_value           = 0.004
    vol_abs.inputs['Anisotropy'].default_value        = 0.3
    vol_abs.inputs['Emission Color'].default_value    = (0.3, 0.1, 0.5, 1.0)
    vol_abs.inputs['Emission Strength'].default_value = 0.002
    link(nt, vol_abs.outputs['Volume'], out.inputs['Volume'])


# ─────────────────────────────────────────────────────────────────────────────
# RENDER SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

def setup_render():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'

    # Hardware auto-detect
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        try:
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'OPTIX'
            sc.cycles.device = 'GPU'
        except Exception:
            sc.cycles.device = 'CPU'

    sc.cycles.samples               = 128
    sc.cycles.use_denoising         = True
    sc.render.resolution_x          = 1920
    sc.render.resolution_y          = 1080
    sc.render.film_transparent      = False

    # Filmic + bloom via compositor
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look           = 'High Contrast'
    sc.view_settings.exposure       = 0.3

    sc.use_nodes = True
    comp_nt = sc.node_tree
    comp_nt.nodes.clear()

    render_layers = comp_nt.nodes.new('CompositorNodeRLayers')
    glare         = comp_nt.nodes.new('CompositorNodeGlare')
    composite     = comp_nt.nodes.new('CompositorNodeComposite')

    glare.glare_type = 'FOG_GLOW'
    glare.quality    = 'HIGH'
    glare.threshold  = 0.8
    glare.size       = 8
    glare.mix        = 0.5

    link(comp_nt, render_layers.outputs['Image'], glare.inputs['Image'])
    link(comp_nt, glare.outputs['Image'],          composite.inputs['Image'])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n── Cyberpunk City Generator ──────────────────────")
    clear_scene()
    print("  [1/7] Scene cleared")

    create_ground()
    print("  [2/7] Wet ground created")

    create_city()
    print(f"  [3/7] {GRID}×{GRID} building grid generated")

    create_flying_vehicles()
    print("  [4/7] Flying vehicles placed")

    setup_camera()
    print("  [5/7] Cinematic camera ready")

    setup_lighting()
    print("  [6/7] Neon lighting set up")

    setup_world()
    setup_render()
    print("  [7/7] World atmosphere + Cycles render configured")

    print("\n  ✓  Done!  Press F12 to render.")
    print("  Tip: Viewport → Overlays → Disable Grid for a cleaner preview.")
    print("────────────────────────────────────────────────────\n")


main()
