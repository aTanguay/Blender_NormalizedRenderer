<div align="center">

# Scale Render

**Pixel-perfect product renders at consistent real-world scale**

[![Blender](https://img.shields.io/badge/Blender-4.0+-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

</div>

---

## What It Does

Scale Render maintains a consistent pixel-to-millimeter ratio across all your renders. By default, **10 pixels = 1 millimeter**.

| Object | Real Size | Output Resolution |
|--------|-----------|-------------------|
| Cola can | 120mm tall | 1,220px tall |
| Subwoofer | 600mm tall | 6,020px tall |
| Watch | 60mm tall | 620px tall |

Every image conveys real-world size through its resolution.

---

## Installation

1. Download `PixelNormalizedRenderer.zip` from [Releases](../../releases)
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the zip file and enable **"Scale Render"**

Access the panel: Press `N` in the 3D Viewport → **Scale Render** tab

---

## Quick Start

1. **Create a collection** named `RENDER_YourObject`
2. **Add your mesh** to the collection (modeled at real-world mm scale)
3. **Select the collection** from the dropdown in the Scale Render panel
4. **Click Eval** to preview camera framing
5. **Click Render Active** to render

Output saves to `//renders/` (relative to your .blend file).

---

## Features

- **Consistent scaling** - Same px/mm ratio for all objects
- **Auto camera positioning** - Frames objects with 12° hero shot angle
- **Adaptive lighting** - Three-point rig scales with object size
- **Custom lights** - Add lights to collection to override default rig
- **Batch rendering** - Render All processes every `RENDER_` collection
- **Collection isolation** - Auto-hides other collections when working

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Scale (px/mm) | 10.0 | Pixels per millimeter |
| Padding (px) | 10 | Edge padding on all sides |
| Output Folder | //renders/ | Save location |
| Collection Prefix | RENDER_ | Filter for batch rendering |

---

## Troubleshooting

**"No collections found"** - Create a collection starting with `RENDER_`

**Camera not moving** - Make sure a collection is selected in the dropdown

**Object too small/large** - Check your model is at real-world mm scale

---

## Requirements

- Blender 4.0+
- No external dependencies

---

## Contributing

See [DEVNOTES.md](DEVNOTES.md) for technical documentation.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Created by **Andy** for consistent product visualization workflows.
