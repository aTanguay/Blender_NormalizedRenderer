# Scale Render Addon - Claude Code Instructions

## Project Overview

Blender addon for pixel-perfect product renders at consistent real-world scale. **10 pixels = 1 millimeter** (configurable).

## File Structure

```
PixelNormalizedRenderer/
├── __init__.py      # Registration, properties
├── core.py          # Camera math, resolution, collections
├── operators.py     # Eval, Render Active, Render All
├── panel.py         # UI panel, collection menu
└── lighting.py      # Three-point rig, scaling
```

## Key Constants

- `core.FOCAL_LENGTH`: 85mm
- `core.SENSOR_WIDTH`: 36mm
- `core.ELEVATION_ANGLE`: 12°
- `lighting.REFERENCE_HEIGHT`: 200mm

## Architecture

### Data Flow
```
User selects collection → panel.py updates selection
User clicks Eval → operators.py calls core.py for camera math
                → lighting.py scales rig
                → Viewport updates to camera view
```

### Properties (stored on scene)
- `scale_render_props.scale_factor` - px/mm ratio
- `scale_render_props.padding_px` - edge padding
- `scale_render_props.selected_collection` - StringProperty (not Enum - avoids caching bugs)
- `scale_render_props.collection_prefix` - filter for batch

## Development Notes

### Collection Selector
Uses StringProperty + custom Menu instead of dynamic EnumProperty to avoid Blender's enum caching issues.

### Camera Positioning
Iterative frustum checking ensures all 8 bounding box corners fit in frame. See `core.py:calculate_camera_position()`.

### Multi-Mesh Support
Collections can have multiple meshes - treated as single composite bounding box.

### Visibility Isolation
Selecting/evaluating a collection hides all other `RENDER_` prefixed collections.

## Testing

1. Create collection `RENDER_TestObject`
2. Add mesh at real-world mm scale
3. Select from dropdown, click Eval
4. Verify camera frames object with padding

## Documentation

- `README.md` - User-facing overview
- `DEVNOTES.md` - Technical details for developers
- `PLANNING.md` - Design decisions and spec
