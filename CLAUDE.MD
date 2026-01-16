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

### Camera Not Moving / Eval Not Working

**Issue:** Camera stays at origin or doesn't update when selecting different collections

**Common Causes:**
1. **Operator not running:** Check Blender console for debug output starting with `====`
2. **Viewport not updating:** Added `camera.update_tag()` and `context.view_layer.update()` in `operators.py:101-102`
3. **Collection not selected:** Verify dropdown has a collection selected (not "No collections found")

**Debug Steps:**
1. **Open System Console:**
   - Windows: Window → Toggle System Console
   - macOS/Linux: Check terminal where Blender was launched
2. **Look for debug banners:** Should see lines of `===` when clicking Eval
3. **Check debug output shows:**
   ```
   DEBUG operators.py: Eval execute() called
   DEBUG core.py: camera_distance=X.XXXX
   DEBUG core.py: location=<Vector (...)>
   EVAL COMPLETE: ...
   ```
4. **If no output:** Operator isn't running - check if addon is properly installed/enabled

**Recent Fix (2026-01-16):**
- Added extensive debug logging with banner separators (`===`) in `operators.py:26-28, 130-136`
- Added collection state tracking to show which collection was last evaluated
- UI now shows "✓ Evaluated Collection" vs "Selected Collection (not evaluated)"

### Camera Framing Off-Center

**Issue:** Object visible but not perfectly centered in camera view

**Root Cause:** Camera rotation calculation with elevation angle

**Current Implementation:**
1. Camera positioned at distance with 12° elevation: `core.py:182-193`
2. Direction vector calculated from camera to object center
3. Rotation set using `direction.to_track_quat('-Z', 'Y')` with explicit 'XYZ' euler order

**Key Code:** `core.py:201-214`
```python
direction = center - location
direction.normalize()
quat = direction.to_track_quat('-Z', 'Y')
rotation = quat.to_euler('XYZ')  # Explicit euler order
```

**Debug Output Added (2026-01-16):**
- Camera distance (calculated vs actual)
- Direction vector (before and after normalization)
- Rotation angles in degrees
- All values printed with 2-4 decimal precision

**If still off-center:**
1. Check debug output for direction vector - should point from camera to center
2. Verify elevation angle is being applied: should see Z-axis offset
3. Check rotation X angle ≈ 12° (the elevation angle)
4. Verify `to_track_quat` parameters: '-Z' (camera looks down -Z axis), 'Y' (up vector)

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

### Collection Selector Not Updating

**Issue:** Switching collections in dropdown doesn't trigger camera update

**Expected Behavior:**
- Selecting a collection shows "(not evaluated)" until you click Eval
- Clicking Eval calculates camera position, updates viewport, shows "✓ Evaluated"
- Switching to another collection shows "(not evaluated)" again

**Implementation:** `__init__.py:105-116` stores last evaluated collection state

**If not working:**
1. Check that `selected_collection` EnumProperty is bound to `get_collection_items()`
2. Verify `last_evaluated_collection` property is being set in `operators.py:111`
3. Check panel draw method compares these values: `panel.py:56`

---

## Blender Version Compatibility

### Blender 5.0 Compatibility (Verified 2026-01-16)

**Status:** ✅ Fully compatible - no breaking changes affect this addon

**Blender 5.0 Breaking Changes Reviewed:**
- Runtime-defined properties storage changes → Does not affect our addon
- Legacy Action API removal → Not used in this addon
- Image.bindcode deprecated → Not used in this addon
- Mathutils type changes (float32 vs float64) → Minimal impact, calculations still valid
- Animation data from Blender 2.49 discontinued → Not relevant

**Key APIs Used (All Stable):**
- `bpy.types.Camera` - No changes
- `mathutils.Vector` - Type changes don't break our calculations
- `Vector.to_track_quat()` - Still supported in 5.0
- `Quaternion.to_euler()` - Still supported in 5.0
- Camera positioning and rotation APIs unchanged

**Testing Notes:**
- If experiencing issues in Blender 5.0, verify they also occur in 4.x
- Most issues are likely logic bugs, not API compatibility problems
- Debug output system works across all Blender versions 4.0+

**References:**
- [Blender 5.0 Python API Changes](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender API Change Log](https://docs.blender.org/api/current/change_log.html)

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
   - Windows: Window → Toggle System Console
   - macOS/Linux: Terminal where Blender was launched
2. **Use `print()` liberally:** Blender console shows all output
3. **Test operators individually:** Eval → Render Active → Render All
4. **Verify with simple scene:** One cube, one light, one collection

**Debug Output System (Added 2026-01-16):**

The addon includes extensive debug logging to help diagnose issues:

```python
# operators.py - Eval operator includes:
print("=" * 80)  # Banner separators for visibility
print("DEBUG operators.py: Eval execute() called")
print(f"DEBUG operators.py: selected_collection = '{props.selected_collection}'")
# ... execution ...
print("EVAL COMPLETE: {result_msg}")
print(f"Camera final location: {camera.location}")
print(f"Camera final rotation: {camera.rotation_euler}")
print("=" * 80)

# core.py - Camera positioning includes:
print(f"DEBUG core.py: camera_distance={camera_distance:.4f}")
print(f"DEBUG core.py: ELEVATION_ANGLE={math.degrees(ELEVATION_ANGLE):.2f}°")
print(f"DEBUG core.py: center={center}")
print(f"DEBUG core.py: location={location}")
print(f"DEBUG core.py: direction (normalized)={direction}")
print(f"DEBUG core.py: rotation (deg)=X:{math.degrees(rotation.x):.2f}° ...")
```

**Reading Debug Output:**

When you click "Eval", you should see:
1. Banner of `===` lines
2. Collection name being evaluated
3. Object dimensions in mm
4. Camera distance calculation
5. Camera position (x, y, z)
6. Direction vector (should point toward object)
7. Rotation angles in degrees
8. Final camera transform confirmation

**If you see NO debug output:**
- Operator isn't running at all
- Check addon is enabled in Preferences
- Check for Python errors in console
- Verify collection is selected in dropdown

**If camera doesn't move despite debug output:**
- Check `camera.location` in final output matches calculated location
- Verify viewport is in camera view after Eval
- Try manually refreshing viewport (move mouse, orbit view)

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

## Recent Changes

### 2026-01-16 - Collection Selector & Debug Improvements

**Features Added:**
- Collection selector dropdown in UI for easy switching between collections
- Collection state tracking - shows "✓ Evaluated" vs "Selected (not evaluated)"
- Cached evaluation results stored per collection

**Debug System:**
- Added extensive debug logging with banner separators (`===`)
- Camera distance, position, direction, and rotation all logged with precision
- Eval completion confirmation with final transform values
- Helps diagnose "camera not moving" or "collection switching" issues

**Fixes:**
- Added `camera.update_tag()` and `context.view_layer.update()` to force viewport refresh
- Explicit Euler order 'XYZ' in rotation calculation
- Improved debug output formatting for readability

**Files Modified:**
- `__init__.py`: Added collection state tracking properties
- `operators.py`: Enhanced debug output, viewport update forcing
- `panel.py`: Collection selector UI, evaluation status display
- `core.py`: Improved camera positioning debug output

**Compatibility:**
- Verified Blender 5.0 compatibility - no breaking changes affect this addon

---

**Last Updated:** 2026-01-16
**Blender Version:** 4.0+ (including 5.0)
**Addon Version:** 1.0.1
