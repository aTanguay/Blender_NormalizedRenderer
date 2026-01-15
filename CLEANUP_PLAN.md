# Scale Render Addon - Cleanup & Enhancement Plan

## Executive Summary

The codebase is well-structured and functional, but has opportunities for:
1. **Code deduplication** (DRY violations)
2. **Error handling improvements** (validation, user feedback)
3. **Feature completeness** (missing documented features)
4. **Code quality** (type hints, documentation)
5. **User experience** (better feedback, validation)

---

## Priority 1: Critical Issues

### 1.1 Code Duplication - `get_or_create_camera()`

**Problem:** Identical method duplicated in two operators (`SCALE_RENDER_OT_eval` and `SCALE_RENDER_OT_render_all`)

**Location:**
- `operators.py:108-124` (in `SCALE_RENDER_OT_eval`)
- `operators.py:300-314` (in `SCALE_RENDER_OT_render_all`)

**Solution:** Extract to `core.py` as utility function

```python
# In core.py
def get_or_create_camera():
    """Get existing scale render camera or create one."""
    cam_name = "SCALE_RENDER_Camera"

    if cam_name in bpy.data.objects:
        return bpy.data.objects[cam_name]

    # Create camera data
    cam_data = bpy.data.cameras.new(name=cam_name)
    cam_data.lens = FOCAL_LENGTH
    cam_data.sensor_width = SENSOR_WIDTH

    # Create camera object
    camera = bpy.data.objects.new(name=cam_name, object_data=cam_data)
    bpy.context.scene.collection.objects.link(camera)

    return camera
```

**Impact:** Reduces code by ~30 lines, single source of truth

---

### 1.2 Code Duplication - `get_target_collection()`

**Problem:** Nearly identical method duplicated in two operators

**Location:**
- `operators.py:93-106` (in `SCALE_RENDER_OT_eval`)
- `operators.py:168-179` (in `SCALE_RENDER_OT_render_active`)

**Solution:** Extract to `core.py` as utility function

```python
# In core.py
def get_target_collection(context, prefix):
    """Get the collection to work with - active or first matching."""
    # First, try to get collection from active object
    if context.active_object:
        for coll in context.active_object.users_collection:
            if prefix == "" or coll.name.startswith(prefix):
                return coll

    # Fall back to first matching collection
    collections = get_filtered_collections(prefix)
    if collections:
        return collections[0]

    return None
```

**Impact:** Reduces code by ~20 lines, consistent behavior

---

### 1.3 Missing Error Handling - Dimension Validation

**Problem:** No validation for objects with zero dimensions (documented in PLANNING.MD:171)

**Location:** `core.py:get_object_dimensions()` and operator execution paths

**Solution:** Add validation function

```python
# In core.py
def validate_object_dimensions(obj):
    """
    Validate that object has non-zero dimensions.

    Returns:
        (valid, message) tuple - valid is bool, message is error string if invalid
    """
    width, height, depth = get_object_dimensions(obj)

    if width <= 0 or height <= 0 or depth <= 0:
        return False, f"Object has invalid dimensions: {width:.2f}×{height:.2f}×{depth:.2f}mm"

    # Check for unreasonably small objects (< 1mm)
    if width < 1 or height < 1:
        return False, f"Object too small (< 1mm): {width:.2f}×{height:.2f}mm"

    # Check for unreasonably large objects (> 10 meters)
    if width > 10000 or height > 10000 or depth > 10000:
        return False, f"Object too large (> 10m): {width:.2f}×{height:.2f}×{depth:.2f}mm"

    return True, ""
```

Call in operators before processing.

**Impact:** Prevents crashes/undefined behavior, better user feedback

---

### 1.4 Missing Resolution Limits

**Problem:** No validation for output resolution (could create massive images)

**Location:** `core.py:calculate_resolution()`

**Solution:** Add resolution validation

```python
# In core.py
MAX_RESOLUTION = 16384  # Common GPU texture limit

def validate_resolution(width_px, height_px):
    """
    Validate that resolution is within reasonable bounds.

    Returns:
        (valid, message) tuple
    """
    if width_px > MAX_RESOLUTION or height_px > MAX_RESOLUTION:
        return False, f"Resolution too large: {width_px}×{height_px}px (max: {MAX_RESOLUTION}px)"

    if width_px < 1 or height_px < 1:
        return False, f"Resolution too small: {width_px}×{height_px}px"

    # Warn about very large images (> 8K)
    if width_px > 8192 or height_px > 8192:
        return True, f"Warning: Large resolution {width_px}×{height_px}px may be slow"

    return True, ""
```

**Impact:** Prevents memory issues, better user experience

---

## Priority 2: Error Handling Improvements

### 2.1 Weak Exception Handling in Batch Render

**Problem:** Generic `except Exception as e` catches everything, including system errors

**Location:** `operators.py:279-282`

**Current:**
```python
except Exception as e:
    errors.append(f"{collection.name}: {str(e)}")
    failed += 1
    print(f"  ✗ Error: {str(e)}")
```

**Solution:** Be more specific about caught exceptions

```python
except (RuntimeError, ValueError, TypeError) as e:
    errors.append(f"{collection.name}: {str(e)}")
    failed += 1
    print(f"  ✗ Error: {str(e)}")
except KeyboardInterrupt:
    # Allow user to cancel
    self.report({'WARNING'}, f"Batch cancelled by user. {successful} completed, {failed} failed")
    core.restore_collection_visibility(collections, original_states)
    lighting.show_light_rig(show=True)
    return {'CANCELLED'}
except Exception as e:
    # Unexpected errors should still be reported but not swallowed
    errors.append(f"{collection.name}: UNEXPECTED ERROR: {str(e)}")
    failed += 1
    print(f"  ✗ UNEXPECTED ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
```

**Impact:** Better debugging, respects user cancellation

---

### 2.2 No Validation of Output Directory Path

**Problem:** User could enter invalid path (relative without .blend saved, permissions issue)

**Location:** All operators that use `props.output_folder`

**Solution:** Add validation function

```python
# In core.py
def validate_output_path(output_folder, context):
    """
    Validate that output folder path is usable.

    Returns:
        (valid, message, resolved_path) tuple
    """
    import os

    # Resolve relative paths
    resolved = bpy.path.abspath(output_folder)

    # Check if blend file is saved (needed for relative paths)
    if output_folder.startswith("//") and not bpy.data.is_saved:
        return False, "Save .blend file before using relative path (//)", None

    # Check if path is absolute or blend file is saved
    if not os.path.isabs(resolved) and not bpy.data.is_saved:
        return False, "Use absolute path or save .blend file first", None

    # Check if parent directory exists (for creating output dir)
    parent = os.path.dirname(resolved)
    if parent and not os.path.exists(parent):
        return False, f"Parent directory does not exist: {parent}", None

    # Check write permissions (try to create if doesn't exist)
    try:
        os.makedirs(resolved, exist_ok=True)
    except PermissionError:
        return False, f"No write permission: {resolved}", None
    except Exception as e:
        return False, f"Cannot create directory: {str(e)}", None

    return True, "", resolved
```

**Impact:** Better user feedback, prevents render failures

---

### 2.3 Missing Feedback When No Matching Collections

**Problem:** Silent failure if collection filter matches nothing until operator runs

**Location:** `panel.py:76` shows count but doesn't warn

**Solution:** Add visual warning in UI

```python
# In panel.py, in draw() method after line 77
collections = core.get_filtered_collections(props.collection_prefix)
count_label = layout.label(text=f"{len(collections)} collections match prefix")

if len(collections) == 0 and props.collection_prefix != "":
    box = layout.box()
    box.alert = True  # Red warning box
    box.label(text="No collections found!", icon='ERROR')
    box.label(text=f"Create collection starting with '{props.collection_prefix}'")
```

**Impact:** Immediate visual feedback, reduces confusion

---

## Priority 3: Missing Features

### 3.1 File Overwrite Options (PLANNING.MD:172)

**Problem:** Current behavior always overwrites. Plan mentions "option for skip/increment"

**Location:** Output path setting in all render operators

**Solution:** Add property to control behavior

```python
# In __init__.py, add to ScaleRenderProperties
overwrite_mode: EnumProperty(
    name="If File Exists",
    description="What to do when output file already exists",
    items=[
        ('OVERWRITE', "Overwrite", "Replace existing file"),
        ('SKIP', "Skip", "Skip rendering if file exists"),
        ('INCREMENT', "Increment", "Add number suffix (_001, _002, etc.)"),
    ],
    default='OVERWRITE',
)

# In core.py, add utility
def resolve_output_path(base_path, overwrite_mode):
    """
    Resolve output path based on overwrite mode.

    Returns:
        (should_render, final_path) tuple
    """
    if overwrite_mode == 'OVERWRITE':
        return True, base_path

    if overwrite_mode == 'SKIP' and os.path.exists(base_path):
        return False, base_path

    if overwrite_mode == 'INCREMENT':
        if not os.path.exists(base_path):
            return True, base_path

        # Find next available number
        base, ext = os.path.splitext(base_path)
        counter = 1
        while os.path.exists(f"{base}_{counter:03d}{ext}"):
            counter += 1
        return True, f"{base}_{counter:03d}{ext}"

    return True, base_path
```

**Impact:** User control, prevents accidental overwrites

---

### 3.2 Render Progress Feedback

**Problem:** No progress indication during batch render (can take minutes)

**Location:** `operators.py:229` (render all loop)

**Solution:** Use Blender's progress reporting

```python
# In render_all execute(), wrap loop:
wm = context.window_manager
wm.progress_begin(0, len(collections))

for i, collection in enumerate(collections):
    wm.progress_update(i)
    # ... existing render logic ...

wm.progress_end()
```

**Impact:** Better UX for long batch operations

---

### 3.3 Camera Distance Display

**Problem:** Info panel shows "Estimated camera distance" but doesn't display it prominently

**Location:** `panel.py:50` - calculates but UI label says "Camera dist"

**Solution:** Already implemented correctly! Just verify clarity

**Action:** No change needed, but consider adding units "(mm)" to label

---

## Priority 4: Code Quality Improvements

### 4.1 Missing Type Hints

**Problem:** No type hints make code harder to understand and maintain

**Location:** All functions in all modules

**Solution:** Add type hints incrementally, starting with core.py

```python
from typing import Tuple, List, Optional, Dict, Any
from mathutils import Vector, Euler

def get_object_dimensions(obj: bpy.types.Object) -> Tuple[float, float, float]:
    """
    Get world-space bounding box dimensions of an object.
    Returns (width, height, depth) in Blender units (assumed mm).
    """
    # ... existing code ...

def calculate_camera_position(
    obj: bpy.types.Object,
    scale_factor: float,
    padding_px: int
) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Calculate camera position to properly frame the object.

    Returns:
        (location, rotation_euler) for camera
    """
    # ... existing code ...
```

**Impact:** Better IDE support, clearer interfaces, catches bugs

---

### 4.2 Magic Numbers in Lighting

**Problem:** Hardcoded values without explanation

**Location:** `lighting.py:64,69,78` - light positions

**Solution:** Add constants with explanatory comments

```python
# Light positions relative to reference object (200mm)
# Values in mm from object center
KEY_LIGHT_OFFSET = Vector((150, -200, 250))   # Front-right, elevated 45°
FILL_LIGHT_OFFSET = Vector((-200, -150, 100)) # Front-left, lower angle
RIM_LIGHT_OFFSET = Vector((100, 200, 200))    # Behind, edge separation

# Light characteristics
KEY_LIGHT_SIZE = 2.0   # Smaller for sharper shadows
FILL_LIGHT_SIZE = 3.0  # Larger for softer fill
RIM_LIGHT_SIZE = 1.5   # Small for edge highlight
```

**Impact:** More maintainable, easier to adjust lighting

---

### 4.3 Inconsistent Comments

**Problem:** Some modules well-commented, others sparse

**Location:** Varies by module

**Solution:** Add docstrings to all public functions, clarify complex math

Example areas needing better comments:
- `core.py:98-106` - FOV calculation needs explanation
- `lighting.py:136-152` - Intensity scaling formula needs justification

**Impact:** Easier onboarding, better maintainability

---

### 4.4 No Unit Tests

**Problem:** No automated testing, manual testing only

**Location:** N/A (missing)

**Solution:** Add basic test file structure (out of scope for V1 but document)

```python
# tests/test_core.py (future addition)
import unittest
from unittest.mock import MagicMock
import sys
sys.path.insert(0, '..')

# Would test:
# - calculate_resolution() with various inputs
# - get_output_filename() with various prefixes
# - validate_object_dimensions() edge cases
# - Camera position calculations
```

**Impact:** Regression prevention, faster development

---

## Priority 5: User Experience Enhancements

### 5.1 Better Visual Feedback

**Problem:** Minimal visual distinction between sections in panel

**Location:** `panel.py` - UI layout

**Solution:** Add more visual structure

```python
# In draw() method, enhance section headers
box = layout.box()
row = box.row()
row.label(text="Settings", icon='SETTINGS')
# Add separator lines, better spacing

# Add collapsible sections for advanced settings
layout.prop(props, "show_advanced", icon='TRIA_DOWN' if props.show_advanced else 'TRIA_RIGHT')
if props.show_advanced:
    # Advanced options here
```

**Impact:** Cleaner, more professional UI

---

### 5.2 Tooltips on Info Display

**Problem:** Calculated values shown but not explained

**Location:** `panel.py:48-50` - info labels

**Solution:** Add hover tooltips (not easily possible with current label approach)

**Alternative:** Add small info icons with explanations

```python
col.label(text=f"Size: {obj_info['width']:.1f} × {obj_info['height']:.1f} × {obj_info['depth']:.1f} mm")
row = col.row()
row.label(text=f"Output: {obj_info['res_x']} × {obj_info['res_y']} px")
row.label(text="", icon='INFO')  # Visual hint that this is calculated
```

**Impact:** Better user understanding

---

### 5.3 Keyboard Shortcuts

**Problem:** No keyboard shortcuts for common operations

**Location:** Operator registration

**Solution:** Add default keymaps (opt-in feature)

```python
# In __init__.py or separate keymaps.py
addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        # Ctrl+Shift+E for Eval
        kmi = km.keymap_items.new('scale_render.eval', 'E', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

        # Ctrl+Shift+R for Render Active
        kmi = km.keymap_items.new('scale_render.render_active', 'R', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
```

**Impact:** Faster workflow for power users

---

## Priority 6: Documentation

### 6.1 Add Docstring Examples

**Problem:** Functions have docstrings but no usage examples

**Location:** All core functions

**Solution:** Add examples to complex functions

```python
def calculate_camera_position(obj, scale_factor, padding_px):
    """
    Calculate camera position to properly frame the object.

    Uses 85mm focal length with slight downward angle.
    Camera looks at object from front (negative Y axis).

    Example:
        >>> obj = bpy.data.objects['MyCube']
        >>> location, rotation = calculate_camera_position(obj, 10.0, 10)
        >>> camera.location = location
        >>> camera.rotation_euler = rotation

    Args:
        obj: Blender object to frame
        scale_factor: Pixels per millimeter
        padding_px: Pixels to add on each edge

    Returns:
        (location, rotation_euler) for camera
    """
    # ... existing code ...
```

**Impact:** Easier to use as API, better onboarding

---

### 6.2 Add README.md

**Problem:** No installation/quick start guide

**Location:** Root directory (missing)

**Solution:** Create concise README

```markdown
# Scale Render - Blender Addon

Render objects at consistent pixel-per-millimeter scale for product visualization.

## Installation

1. Download/clone this repository
2. In Blender: Edit > Preferences > Add-ons > Install
3. Select scale_render_addon folder or zip
4. Enable "Scale Render" addon

## Quick Start

1. Model object at real-world scale (mm)
2. Create collection named `RENDER_ObjectName`
3. Move object to collection
4. Open sidebar (N key) > Scale Render tab
5. Click "Eval" to preview framing
6. Click "Render Active" to render

## Documentation

- `PLANNING.MD` - Complete design specification
- `CLAUDE.MD` - Development guide for contributors

## License

[Specify license]
```

**Impact:** Easier adoption, looks professional

---

## Implementation Roadmap

### Phase 1: Critical Fixes (4-6 hours)
1. ✅ Extract `get_or_create_camera()` to core.py
2. ✅ Extract `get_target_collection()` to core.py
3. ✅ Add dimension validation
4. ✅ Add resolution limits
5. ✅ Improve batch error handling

### Phase 2: Error Handling (2-3 hours)
1. ✅ Add output path validation
2. ✅ Add UI warning for no collections
3. ✅ Add better error messages

### Phase 3: Features (3-4 hours)
1. ✅ Add overwrite mode options
2. ✅ Add progress feedback for batch render
3. ✅ Test edge cases

### Phase 4: Quality (4-6 hours)
1. ✅ Add type hints to core.py
2. ✅ Add type hints to lighting.py
3. ✅ Extract magic numbers to constants
4. ✅ Improve comments and docstrings

### Phase 5: Polish (2-3 hours)
1. ✅ Enhance UI visual structure
2. ✅ Add README.md
3. ✅ Final testing

**Total Estimated Time: 15-22 hours**

---

## Testing Strategy

After each phase:

1. **Manual testing in Blender:**
   - Load test scene with various object sizes
   - Test all three operators (Eval, Render Active, Render All)
   - Test edge cases (empty collections, invalid paths, etc.)

2. **Code review:**
   - Check for remaining duplication
   - Verify error handling paths
   - Ensure consistency across modules

3. **User testing:**
   - Have someone unfamiliar try the addon
   - Note confusing UI elements
   - Gather feedback on error messages

---

## Notes

- All changes maintain backward compatibility
- No breaking changes to existing .blend files
- Follows existing code style and patterns
- Respects design decisions in PLANNING.MD
- Focuses on quality and maintainability, not feature creep

---

## Out of Scope (V2+)

These are good ideas but beyond cleanup scope:
- Multiple camera angles
- Custom focal length override
- JSON manifest export
- Depth pass outputs
- Asset browser integration

Defer to V2 planning after V1 is solid.
