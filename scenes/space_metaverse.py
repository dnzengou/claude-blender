"""
space_metaverse.py — geospatial persistent 3D world reference scene.

Bridges Copernicus earth-observation data and Galileo (GNSS) geolocation
into an immersive bpy world for gaming, simulation, smart-city, and
planet-exploration use cases (Earth · Moon · Mars).

Mirrors the 'Bridging Space Data & Gaming Innovation' deck:
- Geospatial backbone   → equirectangular lat/lon → world XY
- Persistent state      → JSON session log on disk
- 3D immersive world    → procedural terrain + climate overlay + sun
- Multi-planet ready    → switch via PLANET constant

Pure bpy + stdlib (math, random, time, pathlib, json). No external assets,
no native extensions. Runs on ARM/x86/Windows/Linux/macOS.

Run inside Blender:
    Text Editor → Open → space_metaverse.py → Run Script
Or via the project CLI:
    python blender_gen.py "load scenes/space_metaverse.py" --send
"""
import bpy
import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path

# ── parameters (mutate to evolve the scene) ──────────────────────────────────
PLANET = "earth"            # earth | moon | mars
TERRAIN_SCALE = 50.0        # world units edge length
TERRAIN_SUBDIV = 7          # 2^N subdivisions; 7 → 128×128
SHOW_CLIMATE = True         # Copernicus-style overlay
SHOW_MARKERS = True         # Galileo lat/lon ground markers
SHOW_GALILEO = True         # Galileo PRN constellation (24 satellites in orbit)
SHOW_NIGHT = True           # translucent night-hemisphere overlay (UTC-driven)
USE_REAL_SUN = True         # rotate sun azimuth by subsolar longitude (current UTC)

# Per-planet visual + physical constants
PLANETS = {
    "earth": dict(color=(0.18, 0.35, 0.20, 1.0), accent=(0.10, 0.30, 0.55, 1.0),
                  sun_energy=4.0, amplitude=1.5, seed=42),
    "moon":  dict(color=(0.55, 0.55, 0.55, 1.0), accent=(0.30, 0.30, 0.30, 1.0),
                  sun_energy=6.0, amplitude=2.5, seed=7),
    "mars":  dict(color=(0.55, 0.27, 0.13, 1.0), accent=(0.55, 0.20, 0.10, 1.0),
                  sun_energy=2.5, amplitude=1.8, seed=13),
}

# Galileo-style geolocation markers (label, lat_deg, lon_deg)
GEO_MARKERS = [
    ("Equator-Null", 0.0,    0.0),
    ("Paris",        48.85,  2.35),
    ("Tokyo",        35.68,  139.69),
    ("Rio",         -22.91, -43.17),
    ("Sydney",      -33.87,  151.21),
    ("McMurdo",     -77.85,  166.67),
]

STATE_PATH = str(Path.home() / ".space_metaverse_state.json")


def _build_galileo_constellation() -> list:
    """24 satellites in 3 planes × 8 slots. Approximate ground-track lat/lon
    from inclination + mean anomaly + RAAN (right-ascension of ascending node).
    Galileo: ~23,222 km altitude, 56° inclination, 14h orbital period."""
    sats = []
    for plane in range(3):
        raan = plane * 120.0       # 3 planes spaced 120° apart
        for slot in range(8):
            mean_anom = slot * 45.0
            lat = 56.0 * math.sin(math.radians(mean_anom))
            lon = ((raan + mean_anom * 2.0 + 180.0) % 360.0) - 180.0
            sats.append((f"E{plane + 1}-{slot + 1:02d}", lat, lon))
    return sats


GALILEO_PRNS = _build_galileo_constellation()


# ── persistence ──────────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load session log. Returns fresh dict on first run or corrupt file."""
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"sessions": 0, "last_planet": None, "history": []}


def save_state(state: dict) -> None:
    """Persist session log. Silent on write failure (degrade gracefully)."""
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass


# ── geospatial projection ────────────────────────────────────────────────────

def latlon_to_xy(lat_deg: float, lon_deg: float, scale: float) -> tuple:
    """Equirectangular: lon → x, lat → y. Both bounded by ±scale/2."""
    x = (lon_deg / 180.0) * (scale / 2.0)
    y = (lat_deg /  90.0) * (scale / 2.0)
    return (x, y)


def subsolar_lon_utc() -> float:
    """Approx subsolar longitude in degrees [-180, 180] for current UTC.
    Simplified: assumes equation-of-time = 0; sufficient for visualisation."""
    now = datetime.now(timezone.utc)
    hour = now.hour + now.minute / 60.0 + now.second / 3600.0
    return -15.0 * (hour - 12.0)


# ── scene primitives ─────────────────────────────────────────────────────────

def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name: str, color: tuple, emission: float = 0.0,
                  alpha: float = 1.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = 0.85
        if emission > 0 and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emission
        if alpha < 1.0 and "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
            mat.blend_method = "BLEND"
    return mat


def build_terrain(cfg: dict) -> bpy.types.Object:
    """Subdivided plane with deterministic procedural Z-displacement."""
    bpy.ops.mesh.primitive_plane_add(size=TERRAIN_SCALE, location=(0, 0, 0))
    plane = bpy.context.object
    plane.name = f"{PLANET.capitalize()}_Terrain"

    bpy.ops.object.mode_set(mode="EDIT")
    for _ in range(TERRAIN_SUBDIV):
        bpy.ops.mesh.subdivide()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Deterministic seed → reproducible terrain per planet
    random.seed(cfg["seed"])
    amp = cfg["amplitude"]
    for v in plane.data.vertices:
        nx, ny = v.co.x, v.co.y
        # 2-octave sine + small noise — proxy for Copernicus DEM
        h = (math.sin(nx * 0.3) * math.cos(ny * 0.3) * amp
             + math.sin(nx * 0.7 + 1.0) * 0.4 * amp
             + (random.random() - 0.5) * 0.2 * amp)
        v.co.z = h
    plane.data.update()

    plane.data.materials.append(make_material(f"{PLANET}_terrain", cfg["color"]))
    return plane


def add_markers(scale: float) -> None:
    """Galileo geolocation pins — emissive spheres at projected lat/lon."""
    mat = make_material("geo_marker", (1.0, 0.85, 0.15, 1.0), emission=4.0)
    for label, lat, lon in GEO_MARKERS:
        x, y = latlon_to_xy(lat, lon, scale)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.6, location=(x, y, 4.0), segments=12, ring_count=8,
        )
        marker = bpy.context.object
        marker.name = f"GEO_{label}"
        marker.data.materials.append(mat)


def add_climate_overlay(cfg: dict, scale: float) -> None:
    """Translucent emissive plane above terrain — Copernicus climate-data proxy."""
    bpy.ops.mesh.primitive_plane_add(size=scale, location=(0, 0, 8.0))
    overlay = bpy.context.object
    overlay.name = "Climate_Overlay"
    overlay.data.materials.append(
        make_material("climate_overlay", cfg["accent"], emission=0.3, alpha=0.18)
    )


def add_galileo_satellites(scale: float) -> None:
    """Galileo PRN constellation — bright cyan emissive markers at Z=14 (orbit proxy)."""
    mat = make_material("galileo_sat", (0.2, 0.85, 1.0, 1.0), emission=6.0)
    for label, lat, lon in GALILEO_PRNS:
        x, y = latlon_to_xy(lat, lon, scale)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.35, location=(x, y, 14.0), segments=8, ring_count=6,
        )
        sat = bpy.context.object
        sat.name = f"GAL_{label}"
        sat.data.materials.append(mat)


def add_night_overlay(scale: float) -> None:
    """Translucent dark plane centred on antisolar longitude (180° from subsolar)."""
    sub_lon = subsolar_lon_utc()
    night_lon = ((sub_lon + 180.0 + 180.0) % 360.0) - 180.0
    nx, _ = latlon_to_xy(0.0, night_lon, scale)
    bpy.ops.mesh.primitive_plane_add(size=scale, location=(nx, 0, 7.0))
    night = bpy.context.object
    night.scale.x = 0.5  # cover one hemisphere width
    night.name = "Night_Hemisphere"
    night.data.materials.append(make_material("night_overlay", (0.02, 0.02, 0.07, 1.0), alpha=0.55))


def add_lighting(cfg: dict) -> None:
    bpy.ops.object.light_add(type="SUN", location=(20, -20, 25))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy = cfg["sun_energy"]
    if USE_REAL_SUN:
        # Rotate sun azimuth around Z by subsolar longitude → matches current UTC
        az = math.radians(subsolar_lon_utc())
        sun.rotation_euler = (math.radians(45), 0, az)
    else:
        sun.rotation_euler = (math.radians(45), 0, math.radians(45))


def add_camera() -> None:
    bpy.ops.object.camera_add(
        location=(35, -35, 25),
        rotation=(math.radians(55), 0, math.radians(45)),
    )
    bpy.context.scene.camera = bpy.context.object


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    available = {e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in available else "BLENDER_EEVEE"


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if PLANET not in PLANETS:
        raise ValueError(f"PLANET must be one of {list(PLANETS)}, got {PLANET!r}")

    cfg = PLANETS[PLANET]
    state = load_state()

    clear_scene()
    build_terrain(cfg)
    if SHOW_MARKERS:
        add_markers(TERRAIN_SCALE)
    if SHOW_CLIMATE:
        add_climate_overlay(cfg, TERRAIN_SCALE)
    if SHOW_GALILEO and PLANET == "earth":
        add_galileo_satellites(TERRAIN_SCALE)
    if SHOW_NIGHT and PLANET == "earth":
        add_night_overlay(TERRAIN_SCALE)
    add_lighting(cfg)
    add_camera()
    configure_render()

    state["sessions"] = state.get("sessions", 0) + 1
    state["last_planet"] = PLANET
    state["last_ts"] = time.time()
    state["last_subsolar_lon"] = subsolar_lon_utc() if PLANET == "earth" else None
    state.setdefault("history", []).append(
        {"ts": time.time(), "planet": PLANET, "markers": len(GEO_MARKERS),
         "galileo": len(GALILEO_PRNS) if (SHOW_GALILEO and PLANET == "earth") else 0}
    )
    # bound history length to avoid unbounded growth
    state["history"] = state["history"][-50:]
    save_state(state)

    sats = len(GALILEO_PRNS) if (SHOW_GALILEO and PLANET == "earth") else 0
    print(f"[space_metaverse] planet={PLANET}  session={state['sessions']}  "
          f"markers={len(GEO_MARKERS)}  galileo={sats}  terrain={2**TERRAIN_SUBDIV}x")


main()
