# Scale Render Addon — Planning Document

## Overview

A Blender addon that renders objects at a consistent pixel-to-millimeter scale, enabling programmers and designers to infer real-world size directly from image resolution. Designed for product visualization workflows where multiple objects of varying sizes need to be rendered with consistent scaling logic.

**Core principle:** 10 pixels = 1 millimeter (configurable)

A 120mm tall cola can renders to 1200px tall. A 600mm tall subwoofer renders to 6000px tall.

---

## Target Workflow

1. Operator models object at real-world scale (mm)
2. Object is placed in its own collection
3. Operator clicks **Eval** to preview framing and adjust lighting
4. Operator clicks **Render Active** for single output
5. Repeat for all objects
6. **Render All** available for batch output when ready

---

## UI Panel

**Location:** 3D Viewport sidebar (N-panel), tab named "Scale Render"

### Controls

| Element | Type | Default | Notes |
|---------|------|---------|-------|
| Scale Factor | Float | 10.0 | Pixels per millimeter |
| Padding | Integer | 10 | Fixed pixels added to each edge |
| Output Folder | Directory picker | //renders/ | Relative to .blend file |
| Collection Filter | Text field | RENDER_ | Only process collections with this prefix (leave blank for all) |

### Buttons

| Button | Action |
|--------|--------|
| **Eval** | Positions camera, sets resolution, updates viewport — no render |
| **Render Active** | Eval + renders the active/selected collection's object |
| **Render All** | Iterates through filtered collections, renders each |

### Info Display

- Current object dimensions (W × H × D mm)
- Calculated output resolution
- Estimated camera distance

---

## Technical Implementation

### Camera Setup

- **Type:** Perspective
- **Focal length:** 85mm (baked in, portrait lens aesthetic)
- **Sensor:** Blender default (36mm width)
- **Elevation angle:** 10-15° downward (slight hero shot feel)
- **Position:** Calculated per-object to achieve proper framing

**Distance calculation:**

The camera must frame the object such that, at the calculated resolution, the object pixels match the real-world scale. With perspective and a downward angle:

```
# Vertical field of view from focal length
fov_v = 2 * atan(sensor_height / (2 * focal_length))

# Required framing height in world units (object + padding converted back)
frame_height_mm = object_height_mm + (padding_px * 2 / scale_factor)

# Horizontal distance from object center
camera_distance = (frame_height_mm / 2) / tan(fov_v / 2)

# Apply elevation angle (10-15°)
camera_z = object_center_z + (camera_distance * sin(elevation_angle))
camera_y = object_center_y - (camera_distance * cos(elevation_angle))
```

Camera aims at object center, compensating for the elevated viewpoint.

### Resolution Calculation

```
output_height = (object_height_mm * scale_factor) + (padding_px * 2)
output_width = (object_width_mm * scale_factor) + (padding_px * 2)
```

**Padding:** Fixed 10 pixels on each edge (20px total added to each dimension).

**Aspect ratio:** Output matches the object's actual proportions. A 122mm × 62mm cola can renders to 1240px × 640px (not forced to square or standard ratios).

The camera framing calculation accounts for both dimensions to ensure the object fits with proper padding on all sides.

### Collection Handling

**Detection:**
- Find all collections matching the filter prefix
- Each collection should contain one primary object (largest by bounding box if multiple)

**Visibility:**
- When rendering a collection, hide all others
- Restore visibility state after batch complete

**Naming convention:**
- Collection: `RENDER_Cola_Can`
- Output file: `Cola_Can.png`
- Strip prefix, replace underscores with spaces optional

---

## Lighting System (Hybrid Approach)

### Default Scaling Rig

A three-point light setup parented to an empty called `SCALE_RENDER_LightRig`:

- **Key:** Area light, 45° front-right, above
- **Fill:** Area light, opposite side, lower intensity
- **Rim:** Area light, behind, edge separation

**Scaling behavior:**
- Rig empty scales proportionally to object size
- Light intensity adjusts to compensate for inverse square falloff
- Base size calibrated to a "reference object" (e.g., 200mm tall)

```
rig_scale = object_height / reference_height
light_intensity = base_intensity * (rig_scale ^ 2)
```

### Per-Collection Override

If a collection contains any lights (detected by type), the default rig is **disabled** for that object. The collection's custom lights are used instead.

This allows:
- Quick renders with automatic lighting for most objects
- Full manual control for hero products or difficult shapes
- Gradual migration from auto to custom as needed

### Operator Guidance

When **Eval** is clicked:
- If using default rig: briefly note "Using scaled default lighting"
- If override detected: note "Using collection lights (X lights found)"

---

## Output Specifications

- **Format:** PNG, RGBA (transparent background)
- **Color depth:** 16-bit preferred (for web flexibility)
- **Film settings:** Transparent enabled in render settings
- **Naming:** `{collection_name_without_prefix}.png`
- **Metadata:** Consider embedding dimensions in PNG metadata (future enhancement)

---

## Error Handling

**Batch behavior:** Continue on error, log issues, render what's possible.

| Condition | Response |
|-----------|----------|
| Empty collection | Skip, log warning, continue |
| No objects in collection | Skip, log warning, continue |
| Collection filter matches nothing | Alert user, abort batch |
| Output folder doesn't exist | Create it |
| Object at origin with zero dimensions | Skip, log error, continue |
| File already exists | Overwrite (or add option for skip/increment) |

After batch completion, display summary: X successful, Y skipped with reasons.

---

## Future Enhancements (Out of Scope for V1)

- Multiple camera angles per object (front, side, 3/4)
- Resolution presets (web, print, thumbnail)
- Progress bar/cancel button for batch renders
- JSON manifest output with all dimensions and file paths
- Custom focal length override
- Depth/shadow pass outputs
- Integration with asset browser

---

## File Structure

```
scale_render_addon/
├── __init__.py          # Addon registration, bl_info
├── operators.py         # EvalOperator, RenderActiveOperator, RenderAllOperator
├── panel.py             # UI panel definition
├── core.py              # Camera math, resolution calc, collection utils
├── lighting.py          # Rig scaling, override detection
└── preferences.py       # Addon preferences (if needed)
```

---

## Dependencies

- Blender 4.0+ (for current API compatibility)
- No external Python packages required

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| Padding approach | Fixed 10 pixels per edge (not percentage) |
| Aspect ratio | Match object proportions exactly |
| Camera angle | 10-15° downward elevation (hero shot feel) |
| Background | Transparent (RGBA, film transparent enabled) |
| Batch error handling | Continue and log, don't halt |

---

## Sign-Off

All decisions locked. Ready to proceed with implementation.
