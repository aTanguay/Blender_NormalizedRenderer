# Scale Render - Blender Addon

A Blender addon that renders objects at consistent pixel-per-millimeter scale for product visualization workflows.

## Core Concept

**10 pixels = 1 millimeter** (configurable)

A 120mm tall cola can renders to 1200px tall. A 600mm tall subwoofer renders to 6000px tall. Every object renders at the same scale, making real-world size directly inferable from image resolution.

## Features

- **Consistent scaling** across all objects
- **Automatic camera positioning** with hero shot aesthetic (12° downward angle)
- **Smart lighting system** - automatic three-point lighting that scales with object size
- **Per-collection override** - use custom lights when needed
- **Batch rendering** with progress feedback
- **File management** - overwrite, skip, or auto-number existing files
- **Transparent PNG output** ready for compositing

## Installation

1. **Download** this addon (as .zip or clone repository)
2. **In Blender:** Edit > Preferences > Add-ons > Install
3. **Select** the `scale_render_addon` folder or zip file
4. **Enable** the "Scale Render" checkbox

The addon will appear in the 3D Viewport sidebar (press `N` key).

## Quick Start

### Basic Workflow

1. **Model your object** at real-world scale in millimeters
   - Example: A standard soda can is 122mm tall
   - Set Blender units to millimeters if needed

2. **Create a collection** for your object
   - Name it with the `RENDER_` prefix (configurable)
   - Example: `RENDER_Cola_Can`

3. **Move object to collection**
   - The addon will find the largest mesh object in the collection

4. **Open the Scale Render panel**
   - Press `N` in the 3D Viewport
   - Select the "Scale Render" tab

5. **Click "Eval"** to preview
   - Camera positions automatically
   - Resolution updates
   - Viewport switches to camera view

6. **Click "Render Active"** to render
   - Outputs to `//renders/` by default (relative to .blend file)
   - Filename: `Cola_Can.png` (prefix stripped)

7. **Multiple objects?** Use **"Render All"**
   - Batch renders all collections matching the prefix
   - Shows progress indicator
   - Continues on errors, reports summary

## Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Scale (px/mm)** | Pixels per millimeter in output | 10.0 |
| **Padding (px)** | Pixels added to each edge | 10 |
| **Output Folder** | Where to save renders | `//renders/` |
| **If File Exists** | Overwrite / Skip / Auto-number | Overwrite |
| **Collection Prefix** | Only render collections starting with | `RENDER_` |

## Lighting

### Automatic Lighting

By default, the addon creates a three-point lighting rig that:
- Scales automatically based on object size
- Adjusts intensity to compensate for distance
- Provides professional product lighting

### Custom Lighting

To use your own lights:
1. Add light objects to the collection
2. The addon automatically detects them
3. Default rig is disabled for that object
4. Full control over lighting setup

## Output

- **Format:** PNG with transparency (RGBA, 16-bit)
- **Resolution:** Exact pixel-per-mm scale + padding
- **Aspect ratio:** Matches object proportions (not forced to standard ratios)
- **Naming:** Collection name with prefix stripped

### Example

Collection: `RENDER_Coffee_Mug`
- Object: 90mm wide × 100mm tall
- Scale: 10 px/mm
- Padding: 10px

Output: `Coffee_Mug.png` at 920×1020 pixels

## Validation

The addon validates:
- ✓ Object dimensions (1mm - 10m range)
- ✓ Output resolution (max 16384px, warns at 8K)
- ✓ Output path accessibility
- ✓ Blend file saved (for relative paths)

## Tips

1. **Save your .blend file first** if using relative output paths (`//renders/`)

2. **Model at real scale** - measure your reference objects and model accurately

3. **Use consistent units** - set Blender to millimeters for clarity

4. **Name collections clearly** - the collection name becomes the filename

5. **Test with "Eval" first** - preview framing before rendering

6. **Skip test renders** - set "If File Exists" to "Skip" to avoid re-rendering

7. **Custom lighting** - add lights to collections that need special treatment

## Troubleshooting

### "Save .blend file before using relative path"
- Save your Blender file first, or use an absolute path for output

### "No collections found matching prefix"
- Check collection names start with the prefix (case-sensitive)
- Or set prefix to empty string to render all collections

### "Object too small (< 1mm)"
- Check your object scale - may need to scale up 1000x
- Ensure Blender units are set correctly

### Resolution warning "may render slowly"
- Large objects create large images (e.g., 10m = 100,000px at 10px/mm)
- Reduce scale factor or add size limits to your workflow

### Camera clips through object
- Verify object is at real-world scale
- Check for extreme depth values

## Technical Details

- **Camera:** 85mm focal length (portrait lens aesthetic)
- **Sensor:** 36mm full-frame equivalent
- **Angle:** 12° downward elevation for hero shot feel
- **Distance:** Calculated per-object for exact framing
- **Lighting:** Three-point rig with inverse-square compensation

## File Structure

```
scale_render_addon/
├── __init__.py          # Addon registration
├── core.py              # Camera math & utilities
├── operators.py         # Eval, Render Active, Render All
├── panel.py             # UI panel
├── lighting.py          # Light rig system
├── PLANNING.MD          # Detailed design spec
├── CLAUDE.MD            # Development guide
└── README.md            # This file
```

## Documentation

- **PLANNING.MD** - Complete design specification
- **CLAUDE.MD** - Development guide for contributors
- **CLEANUP_PLAN.md** - Code quality improvement roadmap

## Requirements

- **Blender 4.0+** (tested on 4.0)
- No external dependencies

## Version

**1.0.0** - Initial release

## Author

Andy

## License

[Specify your license here]

## Contributing

See `CLAUDE.MD` for development guidelines and architecture documentation.

## Support

For issues and feature requests, see the project repository.
