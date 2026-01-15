# Scale Render Addon - Development Guide

## Overview

A Blender addon that renders objects at a consistent pixel-to-millimeter scale for product visualization. Core principle: **10 pixels = 1 millimeter** (configurable).

**Example:** A 120mm cola can renders to 1200px tall. A 600mm subwoofer renders to 6000px tall.

---

## Quick Reference

### File Structure

```
scale_render_addon/
├── __init__.py          # Addon registration, properties
├── operators.py         # Eval, Render Active, Render All
├── panel.py             # UI panel in 3D Viewport sidebar
├── core.py              # Camera math, resolution calc, collection utils
├── lighting.py          # Light rig scaling, override detection
├── PLANNING.MD          # Detailed design spec
└── CLAUDE.MD            # This file
```

### Key Constants

- `core.FOCAL_LENGTH`: 85mm (portrait lens)
- `core.SENSOR_WIDTH`: 36mm (full frame)
- `core.ELEVATION_ANGLE`: 12° downward (hero shot)
- `lighting.REFERENCE_HEIGHT`: 200mm (light rig calibration)

---

## Architecture Patterns

### Camera System

**Location:** `core.py:calculate_camera_position()`

The camera positions itself to frame objects at exact pixel-per-mm scale:

1. Calculate frame size needed in world units (object + padding converted to mm)
2. Compute FOV from 85mm focal length
3. Calculate distance to fit both width and height (use larger)
4. Apply 12° elevation angle for hero shot perspective
5. Point camera at object center

**Key insight:** Distance calculation must account for perspective projection and aspect ratio to ensure pixel-perfect scaling.

### Resolution System

**Location:** `core.py:calculate_resolution()`

Simple but critical:
```python
output_height = (object_height_mm * scale_factor) + (padding_px * 2)
output_width = (object_width_mm * scale_factor) + (padding_px * 2)
```

Output resolution matches object proportions exactly (not forced to standard ratios).

### Collection Handling

**Location:** `core.py:get_filtered_collections()`, `core.get_primary_object()`

- Collections with `RENDER_` prefix (configurable) are batch-processed
- Each collection contains one primary object (largest by bounding box)
- Collections without the prefix are ignored
- Output filename strips prefix: `RENDER_Cola_Can` → `Cola_Can.png`

### Lighting Strategy

**Location:** `lighting.py`

**Hybrid approach:**
1. Default rig: Three-point lighting (key/fill/rim) that scales with object size
2. Per-collection override: If collection contains lights, use those instead
3. Automatic detection: `collection_has_lights()` switches behavior

**Rig scaling:**
```python
scale_factor = object_height / REFERENCE_HEIGHT
rig.scale = (scale_factor, scale_factor, scale_factor)
light_intensity = base_intensity * (scale_factor ** 2)  # Compensate for inverse square
```

---

## Common Development Tasks

### Adding New Operators

1. Create operator class in `operators.py` inheriting from `bpy.types.Operator`
2. Set `bl_idname`, `bl_label`, `bl_description`, `bl_options`
3. Implement `execute(self, context)` method
4. Add to `classes` tuple at bottom
5. Add button in `panel.py` using `layout.operator()`

### Modifying Camera Behavior

**File:** `core.py:calculate_camera_position()`

When changing framing:
- Keep focal length at 85mm (design decision)
- Maintain elevation angle for consistent look
- Test with both small (60mm) and large (600mm) objects
- Verify padding appears consistent across sizes

### Adjusting Light Rig

**File:** `lighting.py:get_or_create_light_rig()`

Base rig positions are relative to REFERENCE_HEIGHT (200mm):
- Key: (150, -200, 250) - front-right, above
- Fill: (-200, -150, 100) - front-left, lower
- Rim: (100, 200, 200) - behind, for edge separation

Adjust base intensities for darker/brighter default look.

### Changing Output Format

**File:** `core.py:setup_render_settings()`

Current: PNG, RGBA, 16-bit, transparent background

To change format:
```python
scene.render.image_settings.file_format = 'PNG'  # or 'JPEG', 'OPEN_EXR', etc.
scene.render.image_settings.color_mode = 'RGBA'  # or 'RGB', 'BW'
scene.render.image_settings.color_depth = '16'   # or '8', '32'
```

---

## Testing Checklist

### Unit-Level Testing

Test these scenarios manually in Blender:

1. **Small object** (60mm cola can)
   - Should render ~600px tall at 10px/mm
   - Camera should frame with visible padding
   - Lighting should not be too dim

2. **Large object** (600mm subwoofer)
   - Should render ~6000px tall at 10px/mm
   - Camera should not clip through object
   - Lighting should not be too bright

3. **Wide object** (landscape poster)
   - Output should be wider than tall
   - Camera should frame full width with padding

4. **Tall object** (floor lamp)
   - Output should be much taller than wide
   - Camera distance should be appropriate

5. **Collection with custom lights**
   - Should hide default rig
   - Should report "Using collection lights (X found)"

6. **Empty collection**
   - Should skip gracefully
   - Should log warning, continue batch

### Batch Testing

Run "Render All" with mixed collection types:
- Some with custom lights, some without
- Various sizes (small to large)
- One empty collection (should skip)
- Verify all render successfully
- Check output files named correctly

### Edge Cases

- Object at origin with zero dimensions → Skip with error
- No collections matching prefix → Alert and abort
- Output folder doesn't exist → Create it
- File already exists → Overwrite (current behavior)

---

## Code Style Notes

### Current Patterns

1. **Blender API usage:**
   - Use `bpy.context.scene` for current scene
   - Use `bpy.data.objects` for object lookups
   - Use `bpy.ops.render.render()` for rendering

2. **Error handling:**
   - Batch operations continue on error (log and skip)
   - Single operations report error and cancel
   - Use `self.report({'ERROR'}, message)` for user feedback

3. **Naming conventions:**
   - Addon objects prefixed with `SCALE_RENDER_`
   - Internal helper objects prefixed with `_`
   - Collection prefix configurable (default `RENDER_`)

4. **Property access:**
   - Properties stored on `context.scene.scale_render_props`
   - Use `props = context.scene.scale_render_props` at method start

### When Writing New Code

- Follow existing patterns for consistency
- Add docstrings to new functions (existing style)
- Use type hints where helpful (not required for Blender Python)
- Keep calculations in `core.py`, UI in `panel.py`, actions in `operators.py`
- Test with real Blender scene before committing

---

## Troubleshooting

### Camera Too Close/Far

**Issue:** Objects not framed correctly at calculated resolution

**Check:**
1. `core.FOCAL_LENGTH` and `core.SENSOR_WIDTH` match camera data
2. FOV calculation in `calculate_camera_position()` is correct
3. Aspect ratio calculation matches output resolution
4. Buffer multiplier (1.05) may need adjustment

### Lighting Too Bright/Dim

**Issue:** Rendered images over/underexposed

**Check:**
1. `lighting.REFERENCE_HEIGHT` matches typical object size
2. Base intensities in `lighting.py` appropriate for scene
3. Inverse square compensation (`scale_factor ** 2`) is applied
4. Light rig positions reasonable for object size

### Wrong Resolution

**Issue:** Output doesn't match expected pixel-per-mm scale

**Check:**
1. Resolution percentage set to 100 (not 50% or other)
2. Padding calculation: `(padding_px * 2)` added to each dimension
3. Scale factor applied correctly: `int(dimension_mm * scale_factor)`
4. Object dimensions measured in world space (not local)

### Collections Not Found

**Issue:** "No collections found matching prefix"

**Check:**
1. Collection names actually start with prefix (case-sensitive)
2. Collections contain at least one object
3. Prefix string doesn't have trailing spaces
4. Collections not excluded from view layer

---

## Design Decisions (Locked)

These are finalized in PLANNING.MD. Reference when clarifying requirements:

| Decision | Rationale |
|----------|-----------|
| Fixed 10px padding per edge | Consistent visual weight, not percentage-based |
| Aspect ratio matches object | Product visualization needs real proportions |
| 10-15° downward angle | Hero shot aesthetic for product renders |
| Transparent background | Maximum flexibility for compositing |
| Continue on batch errors | Process what's possible, log issues |
| 85mm focal length | Portrait lens aesthetic, slight compression |

---

## Future Enhancements (Out of Scope)

Reference PLANNING.MD section "Future Enhancements" for V2+ features:
- Multiple camera angles per object
- Resolution presets (web, print, thumbnail)
- Progress bar/cancel for batch renders
- JSON manifest output with metadata
- Custom focal length override
- Depth/shadow pass outputs
- Asset browser integration

---

## Development Workflow

### Making Changes

1. **Read the spec:** Check PLANNING.MD for design intent
2. **Understand existing code:** Read relevant module(s)
3. **Make minimal changes:** Don't over-engineer
4. **Test in Blender:** Load addon, test with real scene
5. **Check edge cases:** Empty collections, extreme sizes, etc.

### Adding Features

1. **Determine module:** Where does this belong?
   - Camera/math → `core.py`
   - UI elements → `panel.py`
   - User actions → `operators.py`
   - Lighting → `lighting.py`

2. **Follow patterns:** Use existing code as template
3. **Update this guide:** Add to relevant section
4. **Test thoroughly:** Use testing checklist above

### Debugging

1. **Check Blender console:** Prints and errors appear there
2. **Use `print()` liberally:** Blender console shows all output
3. **Test operators individually:** Eval → Render Active → Render All
4. **Verify with simple scene:** One cube, one light, one collection

---

## Quick Start for New Developers

1. **Install addon in Blender:**
   - Edit > Preferences > Add-ons > Install
   - Select `__init__.py` or zip of folder
   - Enable "Scale Render" addon

2. **Create test scene:**
   - Add cube, scale to 120mm (1.2 BU if units are mm)
   - Create collection named `RENDER_TestCube`
   - Move cube to collection

3. **Open Scale Render panel:**
   - Press N in viewport
   - Select "Scale Render" tab

4. **Test workflow:**
   - Click "Eval" → Camera positions, resolution updates
   - Click "Render Active" → Renders current object
   - Check `//renders/` folder for output

5. **Read the code:**
   - Start with `__init__.py` (registration)
   - Read `panel.py` (understand UI)
   - Read `operators.py` (understand workflow)
   - Deep dive `core.py` and `lighting.py` as needed

---

## Support and References

- **Blender API docs:** https://docs.blender.org/api/current/
- **Design spec:** See PLANNING.MD in this folder
- **Key modules:**
  - `bpy.types`: Base classes for UI, operators
  - `bpy.ops`: Operator execution (rendering, etc)
  - `mathutils`: Vector math for camera positioning

---

**Last Updated:** 2026-01-15
**Blender Version:** 4.0+
**Addon Version:** 1.0.0
