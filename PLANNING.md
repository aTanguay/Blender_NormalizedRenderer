# Scale Render Addon - Planning Document

## Overview

A Blender addon that renders objects at a consistent pixel-to-millimeter scale for product visualization.

**Core principle:** 10 pixels = 1 millimeter (configurable)

A 120mm tall cola can renders to 1200px tall. A 600mm tall subwoofer renders to 6000px tall.

---

## Workflow

1. Model object at real-world scale (mm)
2. Place in collection named `RENDER_ObjectName`
3. Select collection from dropdown
4. Click **Eval** to preview framing
5. Click **Render Active** or **Render All** for batch

---

## UI Panel

**Location:** 3D Viewport sidebar (N-panel), tab "Scale Render"

### Settings

| Element | Type | Default |
|---------|------|---------|
| Scale Factor | Float | 10.0 px/mm |
| Padding | Integer | 10 px per edge |
| Output Folder | Directory | //renders/ |
| Collection Prefix | Text | RENDER_ |
| If File Exists | Enum | Overwrite |

### Collection Selector

Dropdown menu listing all collections matching the prefix. Selecting a collection:
- Isolates it (hides other RENDER_ collections)
- Shows dimensions and predicted output resolution
- Marks as "not evaluated" until Eval is clicked

### Buttons

| Button | Action |
|--------|--------|
| **Eval** | Position camera, set resolution, isolate collection |
| **Render Active** | Eval + render selected collection |
| **Render All** | Batch render all matching collections |

---

## Technical Implementation

### Camera System

- **Focal length:** 85mm (portrait lens)
- **Sensor:** 36mm (full frame)
- **Elevation:** 12° downward (hero shot)
- **Framing:** Iterative frustum check ensures all 8 bbox corners visible

### Resolution

```
output_width = (object_width_mm * scale_factor) + (padding_px * 2)
output_height = (object_height_mm * scale_factor) + (padding_px * 2)
```

### Collection Handling

- Multi-mesh collections treated as single composite object
- Combined bounding box calculated across all meshes
- Visibility isolation when selecting/evaluating
- Output filename strips prefix: `RENDER_Cola` → `Cola.png`

### Lighting

- Default: Three-point rig (key/fill/rim) that scales with object
- Override: If collection contains lights, use those instead
- Intensity scales with inverse square law compensation

---

## Output

- **Format:** PNG, RGBA, 16-bit
- **Background:** Transparent
- **Resolution:** Dynamic based on object size
- **Aspect ratio:** Matches object proportions

---

## File Structure

```
PixelNormalizedRenderer/
├── __init__.py      # Registration, properties
├── core.py          # Camera math, resolution, collections
├── operators.py     # Eval, Render Active, Render All
├── panel.py         # UI panel, collection menu
└── lighting.py      # Three-point rig, scaling
```

---

## Error Handling

| Condition | Response |
|-----------|----------|
| Empty collection | Skip, log warning |
| No matching collections | Alert user |
| File exists | Based on overwrite mode |
| Resolution > 16384px | Error (GPU limit) |
| Resolution > 8192px | Warning |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Fixed 10px padding | Consistent visual weight |
| Aspect ratio matches object | Real proportions for products |
| 12° elevation | Hero shot aesthetic |
| 85mm focal length | Portrait lens compression |
| StringProperty for selection | Avoids Blender enum caching bugs |
| Iterative camera positioning | Handles complex shapes |

---

## Version History

### 1.0.1 (Current)
- Collection selector with isolation
- Iterative camera frustum checking
- Multi-mesh collection support
- Removed deprecated single-object functions

### 1.0.0
- Initial release
- Core scaling system
- Adaptive lighting
- Batch rendering

---

## Future Enhancements

- Multiple camera angles
- Resolution presets
- Progress bar for batch
- JSON manifest output
- Custom focal length
- Depth/shadow passes

---

**Status:** Production ready
**Blender:** 4.0+
