# Claude × Blender MCP — Prompt Library

Use these prompts directly in **Claude Desktop** once the Blender MCP
connector is active (N-panel → BlenderMCP → Connect to Claude).

---

## 1. Run the Cyberpunk City example

```
Read the file blender-claude/scenes/cyberpunk_city.py and execute it
in the connected Blender session via blender_execute_code.
Report how many objects were created and confirm the render settings.
```

---

## 2. Variant — Rainy Night + Puddle Reflections

```
In the current Blender scene:
1. Select every object named "Ground" and replace its material with a
   Principled BSDF where Base Color = (0.01, 0.01, 0.015),
   Metallic = 0, Roughness = 0.04, IOR = 1.33, so it looks like a
   wet tarmac road reflecting neon lights.
2. Add a ParticleSystem named "Rain" to the Ground object:
   - 5000 particles, physics type Hair, emit downward (Z = -1),
     length 0.4 m, very thin radius.
3. Report the total polygon count of the scene.
```

---

## 3. Custom UI Panel — Quick Physics Toolbar

```
Inject a custom Blender panel into the 3D Viewport sidebar (N-panel)
named "Quick Physics" with tab label "QP". It should contain:
  • Button "Make Ground"  → sets active object as passive rigid body
  • Button "Make Body"    → sets active object as active rigid body,
                            mass = 1 kg
  • Button "Run Sim"      → plays animation from frame 1
  • Button "Clear Sim"    → removes all rigid body settings in scene
Write the full bpy.types.Panel + bpy.types.Operator classes and
register them live.
```

---

## 4. Scene Optimizer / Polygon Audit

```
Audit the current Blender scene:
1. List every mesh object, its polygon count, and its approximate
   screen-space size (bounding-box diagonal in world space).
2. For any object with poly count > 15 000 that has a bounding-box
   diagonal smaller than 2 m, add a Decimate modifier targeting 40%
   of original polygons.
3. Print a before/after polygon total.
```

---

## 5. Procedural DNA Strand

```
Clear the scene and build a scientifically accurate 3D double-helix
DNA model using only bpy primitives:
  - 20 base-pair rungs, pitch 3.4 Å (scale to 0.34 m per rung)
  - Two sugar-phosphate backbone tubes, helix radius 1 m,
    one cyan emissive, one magenta emissive
  - Horizontal base-pair rods connecting the backbones,
    alternating white/yellow emissive
  - Camera pointing at the centre, 50mm lens
  - Render resolution 1080×1920 (portrait) for a poster look
```

---

## 6. Geometry Nodes Explainer

```
Select the active object in my scene (which has a Geometry Nodes
modifier). Read every node in the modifier's node tree and generate
a Markdown table:

| Node name | Node type | What it does |

Then add bpy.types.GeometryNodeFrame labels directly inside the
node tree grouping related nodes by function.
```

---

## Tips

- Always permit the Python execution pop-up that Claude shows before running.
- For long scripts (>100 lines) paste them in Blender's Text Editor first
  and tell Claude to run `bpy.ops.text.run_script()` on them — it's faster.
- Add "use only mesh primitives, no external assets" to keep scenes portable.
