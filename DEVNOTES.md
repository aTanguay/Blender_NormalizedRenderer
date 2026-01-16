# Scale Render - Developer Notes

Technical documentation for contributors and maintainers.

---

## Architecture Overview

### Module Structure

```
PixelNormalizedRenderer/
├── __init__.py      # Registration, properties, addon metadata
├── core.py          # Camera math, resolution, collection utilities
├── operators.py     # Eval, Render Active, Render All operators
├── panel.py         # UI panel, collection selector menu
└── lighting.py      # Three-point rig, custom light detection
```

### Data Flow

```
User clicks Eval
    ↓
operators.py: SCALE_RENDER_OT_eval.execute()
    ↓
core.py: get_collection_dimensions() → width, height, depth (mm)
    ↓
core.py: calculate_resolution() → output_width, output_height (px)
    ↓
core.py: calculate_camera_position() → location, rotation
    ↓
lighting.py: setup_lighting_for_collection() → scales rig or uses custom
    ↓
Viewport updates to camera view
```

---

## Key Constants

| Constant | Location | Value | Purpose |
|----------|----------|-------|---------|
| `FOCAL_LENGTH` | core.py | 85mm | Portrait lens aesthetic |
| `SENSOR_WIDTH` | core.py | 36mm | Full-frame equivalent |
| `ELEVATION_ANGLE` | core.py | 12° | Hero shot downward angle |
| `MAX_RESOLUTION` | core.py | 16384px | GPU texture limit |
| `REFERENCE_HEIGHT` | lighting.py | 200mm | Light rig calibration base |
| `BASE_KEY_ENERGY` | lighting.py | 1000 | Key light intensity at reference |

---

## Camera System

### Position Calculation (`core.py:calculate_camera_position`)

Uses iterative frustum checking to ensure all 8 bounding box corners fit in frame:

1. Generate all 8 corners of collection's bounding box (with padding)
2. Calculate initial distance estimate from FOV and frame size
3. Iteratively verify all corners project within camera FOV
4. Increase distance by 10% if any corner clips, repeat
5. Apply 5% safety buffer
6. Position camera at calculated distance with 12° elevation
7. Point camera at collection center using quaternion rotation

**Key insight:** Simple center-based calculations fail for objects with significant depth or off-center mass. The iterative approach handles all cases.

### FOV Calculation

```python
half_fov_h = math.atan(SENSOR_WIDTH / (2 * FOCAL_LENGTH))  # Horizontal
half_fov_v = math.atan(math.tan(half_fov_h) / aspect)       # Vertical (aspect-corrected)
```

---

## Collection Handling

### Multi-Mesh Support

Collections can contain multiple mesh objects. The addon:

1. Computes combined bounding box across all meshes
2. Treats the group as a single composite object
3. Calculates dimensions from overall min/max corners
4. Centers camera on combined centroid

### Visibility Isolation

When selecting or evaluating a collection:
- All other `RENDER_` prefix collections are hidden
- Target collection is shown
- Prevents visual clutter and render contamination

### Naming Convention

| Collection Name | Output Filename |
|-----------------|-----------------|
| `RENDER_Cola_Can` | `Cola_Can.png` |
| `RENDER_USB_Cable` | `USB_Cable.png` |

Prefix is stripped, rest becomes filename.

---

## Lighting System

### Three-Point Rig

| Light | Position | Energy | Purpose |
|-------|----------|--------|---------|
| Key | Front-right, 45° up | 1000W | Main illumination |
| Fill | Front-left, lower | 300W | Shadow softening |
| Rim | Behind | 500W | Edge separation |

### Scaling Formula

```python
scale_factor = object_height_mm / REFERENCE_HEIGHT  # 200mm base
rig.scale = (scale_factor, scale_factor, scale_factor)
light_energy = base_energy * (scale_factor ** 2)  # Inverse square compensation
```

### Custom Light Override

If collection contains any `LIGHT` type objects:
- Default rig is hidden
- Collection's lights are used as-is
- Reported in UI: "Using collection lights (X found)"

---

## Debug System

### Console Output

Eval operator produces debug banners for troubleshooting:

```
================================================================================
DEBUG operators.py: Eval execute() called
================================================================================
DEBUG operators.py: selected_collection = 'RENDER_TestObject'
DEBUG core.py: width=120.0mm, height=80.0mm, depth=60.0mm
DEBUG core.py: camera_distance=0.4523
DEBUG core.py: location=<Vector (0.0, -0.45, 0.12)>
================================================================================
EVAL COMPLETE: RENDER_TestObject | 120.0×80.0mm → 1220×820px
================================================================================
```

### Accessing Console

- **Windows:** Window → Toggle System Console
- **macOS/Linux:** Launch Blender from terminal, output appears there

---

## Property Storage

All addon properties stored on scene:

```python
props = context.scene.scale_render_props

# User settings
props.scale_factor      # Float: pixels per mm
props.padding_px        # Int: edge padding
props.output_folder     # String: save path
props.collection_prefix # String: filter prefix
props.overwrite_mode    # Enum: OVERWRITE/SKIP/INCREMENT

# State tracking
props.selected_collection        # Currently selected in dropdown
props.last_evaluated_collection  # Last successfully evaluated
props.last_eval_width/height/depth/res_x/res_y  # Cached dimensions
```

---

## Blender API Patterns

### Operator Structure

```python
class SCALE_RENDER_OT_example(Operator):
    bl_idname = "scale_render.example"
    bl_label = "Example"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        # Do work
        self.report({'INFO'}, "Done")
        return {'FINISHED'}
```

### Registration

```python
classes = (Class1, Class2, Class3)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

### Force Viewport Update

```python
camera.update_tag()
context.view_layer.update()

for area in context.screen.areas:
    if area.type == 'VIEW_3D':
        area.tag_redraw()
```

---

## Testing Checklist

### Object Sizes

| Test | Expected |
|------|----------|
| 60mm object at 10px/mm | ~620px (with padding) |
| 600mm object at 10px/mm | ~6020px (with padding) |
| Wide landscape object | Wider than tall output |
| Tall portrait object | Taller than wide output |

### Edge Cases

- [ ] Empty collection → Skip with warning
- [ ] No mesh objects → Skip with error
- [ ] Zero dimensions → Skip with error
- [ ] Collection with custom lights → Uses custom, hides rig
- [ ] File exists + SKIP mode → Skips render
- [ ] File exists + INCREMENT mode → Adds _001 suffix

### Batch Rendering

- [ ] Multiple collections render sequentially
- [ ] Visibility properly isolated per collection
- [ ] Visibility restored after batch complete
- [ ] Progress reported in console
- [ ] Summary shows success/skip/fail counts

---

## Troubleshooting

### Camera Not Moving

1. Check console for debug output
2. If no output → Operator not running, check addon enabled
3. If output but no movement → Check `camera.location` matches calculated
4. Force viewport refresh: `context.view_layer.update()`

### Wrong Resolution

1. Verify `resolution_percentage = 100`
2. Check padding: `(padding_px * 2)` added to each dimension
3. Confirm object dimensions in world space, not local

### Collection Not Found

1. Verify prefix matches exactly (case-sensitive)
2. Collection must contain at least one object
3. Check for trailing spaces in prefix field

### Lighting Issues

1. Check if collection has custom lights (overrides rig)
2. Verify rig exists: look for `SCALE_RENDER_LightRig` in outliner
3. Check rig is not hidden

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| 85mm focal length | Portrait lens aesthetic, slight compression flattering for products |
| 12° elevation | Hero shot feel without excessive foreshortening |
| Fixed 10px padding | Consistent visual weight across all sizes |
| StringProperty for selection | Avoids Blender's EnumProperty caching issues |
| Iterative camera positioning | Handles complex shapes and off-center objects |
| Continue on batch errors | Maximize output, report issues at end |

---

## Future Enhancements

Planned for future versions:

- Multiple camera angles per object
- Resolution presets (web, print, thumbnail)
- Progress bar with cancel for batch
- JSON manifest output
- Custom focal length override
- Depth/shadow pass outputs

---

## Version History

### 1.0.1 (2026-01-16)
- Fixed collection selector not updating (replaced EnumProperty with StringProperty + menu)
- Added collection isolation (hides other RENDER_ collections when selecting)
- Added iterative camera frustum checking for complex objects
- Enhanced debug output with banner separators
- Verified Blender 5.0 compatibility

### 1.0.0
- Initial release
- Core scaling system
- Three-point adaptive lighting
- Batch rendering
- Custom light override detection

---

**Blender Version:** 4.0+ (including 5.0)
**Last Updated:** 2026-01-16
