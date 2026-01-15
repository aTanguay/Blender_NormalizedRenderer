<div align="center">

# Scale Render

### Pixel-perfect product renders at consistent real-world scale

[![Blender](https://img.shields.io/badge/Blender-4.0+-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-[LICENSE]-blue.svg)](#license)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](#version-history)

*Perfect for product visualization, e-commerce, catalogs, and technical documentation*

</div>

---

## Table of Contents

- [Why Scale Render?](#why-scale-render)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Lighting System](#lighting-system)
- [Output Specifications](#output-specifications)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Technical Specifications](#technical-specifications)
- [Contributing](#contributing)

---

## Why Scale Render?

**The Problem:** Traditional rendering outputs images with arbitrary resolutions. A small keychain and a large speaker might both render at 1920×1080, making real-world size impossible to infer.

**The Solution:** Scale Render maintains a consistent scale across all objects. By default, **10 pixels = 1 millimeter**.

- 120mm cola can → 1,200px tall
- 600mm subwoofer → 6,000px tall
- 60mm watch → 600px tall

Every image conveys real-world size through its resolution.

## Features

✨ **Consistent Scaling** - Every object renders at the same pixel-per-millimeter ratio
📷 **Automatic Camera** - Smart positioning with 12° hero shot angle
💡 **Adaptive Lighting** - Three-point rig that scales with object size
🎨 **Custom Light Support** - Automatically detects and uses collection lights
⚡ **Batch Rendering** - Process multiple objects with one click
📁 **Smart File Management** - Overwrite, skip, or auto-number outputs
🎯 **Transparent PNGs** - 16-bit RGBA ready for compositing

## Installation

### Method 1: Download Release
1. Download the latest release from the [Releases page](../../releases)
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the downloaded `.zip` file
4. Enable the **"Scale Render"** checkbox

### Method 2: Clone Repository
```bash
git clone https://github.com/yourusername/Blender_NormalizedRenderer.git
cd Blender_NormalizedRenderer
```
Then follow steps 2-4 above, selecting the `scale_render_addon` folder.

**Access the addon:** Press `N` in the 3D Viewport and select the **"Scale Render"** tab.

## Quick Start

### 5-Minute Tutorial

**1. Model at Real Scale**
   - Create or import your object at actual millimeter dimensions
   - Example: Standard cola can = 122mm tall × 66mm diameter

**2. Organize in Collections**
   - Create a collection named `RENDER_YourObject`
   - Move your object into it (addon finds the largest mesh automatically)

**3. Open Scale Render Panel**
   - Press `N` in 3D Viewport → **"Scale Render"** tab

**4. Preview Setup**
   - Click **"Eval"** to position camera and calculate resolution
   - Viewport switches to camera view automatically

**5. Render**
   - **Single object:** Click **"Render Active"**
   - **Multiple objects:** Click **"Render All"** (batch mode)
   - Find outputs in `//renders/` (relative to your .blend file)

### Output Example

```
Collection:  RENDER_Coffee_Mug
Object Size: 90mm wide × 100mm tall
Scale:       10 px/mm
Padding:     10px per edge

Output:      Coffee_Mug.png
Resolution:  920 × 1,020 pixels
```

## Configuration

All settings available in the Scale Render panel:

| Setting | Description | Default |
|---------|-------------|---------|
| **Scale (px/mm)** | Pixels per millimeter in output | `10.0` |
| **Padding (px)** | Extra pixels added to each edge | `10` |
| **Output Folder** | Save location (use `//` for relative paths) | `//renders/` |
| **If File Exists** | Conflict handling: Overwrite / Skip / Auto-number | `Overwrite` |
| **Collection Prefix** | Only render collections starting with this | `RENDER_` |

> **Tip:** Use `//` prefix for paths relative to your .blend file location

## Lighting System

### 💡 Automatic Mode (Default)

The addon creates a professional three-point lighting rig that:
- ✅ Scales intensity based on object size
- ✅ Compensates for inverse-square falloff
- ✅ Positions dynamically relative to object
- ✅ Provides consistent product lighting

**No setup required** - just render!

### 🎨 Custom Mode

Want full control? Add your own lights:
1. Add light objects directly to your render collection
2. The addon **automatically detects** them
3. Default rig is **disabled** for that collection
4. Your custom lighting is used instead

**Example:** Add area lights for soft shadows, or a rim light for edge separation.

---

## Output Specifications

| Property | Value |
|----------|-------|
| **Format** | PNG with alpha channel |
| **Color Depth** | 16-bit RGBA |
| **Background** | Transparent |
| **Resolution** | Object size × scale + padding |
| **Aspect Ratio** | Matches object proportions exactly |
| **Filename** | Collection name (prefix stripped) |

## Best Practices

### 🎯 Before You Start
- ✅ **Save your .blend file** (required for relative paths like `//renders/`)
- ✅ **Set units to millimeters** (Scene Properties → Units)
- ✅ **Model at real-world scale** (measure reference objects)

### 🚀 Workflow Tips
- 🔍 **Test with "Eval" first** - Preview framing without rendering
- 📝 **Name collections clearly** - Collection name becomes the filename
- ⏩ **Batch efficiently** - Set "If File Exists" to "Skip" to avoid re-renders
- 💡 **Add custom lights** - Place lights in collections for special treatment

### ⚠️ Automatic Validation

The addon checks for:
- Object dimensions (1mm - 10m supported)
- Output resolution (max 16,384px, warns above 8K)
- Path accessibility and write permissions
- Blend file saved (for relative paths)

## Troubleshooting

<details>
<summary><b>"Save .blend file before using relative path"</b></summary>

**Solution:** Save your Blender file first, or use an absolute path like `/Users/name/renders/`
</details>

<details>
<summary><b>"No collections found matching prefix"</b></summary>

**Causes:**
- Collection names don't start with the prefix (case-sensitive)
- Collections are empty

**Solutions:**
- Verify collection names start with `RENDER_`
- Or change prefix in settings (even empty string works)
</details>

<details>
<summary><b>"Object too small (< 1mm)" or "Object too large (> 10m)"</b></summary>

**Cause:** Object is scaled incorrectly

**Solutions:**
- Check object dimensions in Properties → Object
- May need to scale up/down by 1000× (common when switching units)
- Verify units are set to millimeters
</details>

<details>
<summary><b>Resolution warning "may render slowly"</b></summary>

**Cause:** Large objects create huge images (10m object = 100,000px at 10px/mm)

**Solutions:**
- Reduce scale factor (try 5px/mm or lower)
- Split large objects into multiple views
- Render smaller sections individually
</details>

<details>
<summary><b>Camera clips through object</b></summary>

**Solutions:**
- Verify object is at correct real-world scale
- Check for extreme depth (very flat/thin objects)
- Test with "Eval" to preview camera position
</details>

<details>
<summary><b>Lighting too bright/dark</b></summary>

**Solutions:**
- Default rig calibrated for 200mm objects
- For very small/large objects, add custom lights to collection
- Adjust World → Surface strength for ambient light
</details>

---

## Technical Specifications

<details>
<summary><b>Camera System</b></summary>

- **Focal Length:** 85mm (portrait lens for natural perspective)
- **Sensor Size:** 36mm (full-frame equivalent)
- **Elevation Angle:** 12° downward (hero shot aesthetic)
- **Distance:** Dynamically calculated per object for pixel-perfect framing
- **FOV Calculation:** Accounts for aspect ratio and perspective projection
</details>

<details>
<summary><b>Lighting System</b></summary>

- **Type:** Three-point lighting (key, fill, rim)
- **Scaling:** Rig scales with object height
- **Intensity:** Inverse-square law compensation
- **Calibration:** Reference height of 200mm
- **Override:** Automatic detection of custom lights per collection
</details>

<details>
<summary><b>Render Engine Compatibility</b></summary>

- ✅ **Cycles** (recommended for photorealistic output)
- ✅ **Eevee** (faster preview renders)
- ✅ **Workbench** (basic shading)

The addon works with any render engine - lighting and camera setup is engine-agnostic.
</details>

---

## Project Structure

```
scale_render_addon/
├── __init__.py          # Addon registration & properties
├── core.py              # Camera math & resolution calculation
├── operators.py         # Eval, Render Active, Render All
├── panel.py             # UI panel (3D Viewport sidebar)
├── lighting.py          # Adaptive lighting system
├── PLANNING.md          # Complete design specification
├── CLAUDE.md            # Developer documentation
└── README.md            # This file
```

---

## Requirements

- **Blender:** 4.0 or higher
- **Dependencies:** None (pure Python + Blender API)
- **Platform:** Windows, macOS, Linux

---

## Contributing

Contributions welcome! See [CLAUDE.md](scale_render_addon/CLAUDE.md) for:
- Architecture overview
- Development workflow
- Code style guidelines
- Testing procedures

**Found a bug?** Open an [issue](../../issues)
**Have a feature idea?** Start a [discussion](../../discussions)

---

## License

[Specify your license here - e.g., MIT, GPL-3.0, etc.]

---

## Version History

**1.0.0** - Initial Release
- Core scaling system
- Automatic camera positioning
- Adaptive lighting with custom overrides
- Batch rendering
- Smart file management

---

## Acknowledgments

Created by **Andy** for consistent product visualization workflows.

Built with the [Blender Python API](https://docs.blender.org/api/current/).
