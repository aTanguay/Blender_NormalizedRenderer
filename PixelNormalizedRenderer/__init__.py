"""
Scale Render Addon for Blender
Renders objects at consistent pixel-per-millimeter scale

Author: Andy
Version: 1.0.0
"""

bl_info = {
    "name": "Scale Render",
    "author": "Andy",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Scale Render",
    "description": "Render objects at consistent pixel-per-millimeter scale for product visualization",
    "category": "Render",
}


import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    StringProperty,
    PointerProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup

from . import core
from . import lighting
from . import operators
from . import panel


class ScaleRenderProperties(PropertyGroup):
    """Properties for Scale Render addon"""
    
    scale_factor: FloatProperty(
        name="Scale (px/mm)",
        description="Pixels per millimeter in output image",
        default=10.0,
        min=0.1,
        max=100.0,
        precision=1,
    )
    
    padding_px: IntProperty(
        name="Padding (px)",
        description="Pixels to add on each edge of the output",
        default=10,
        min=0,
        max=500,
    )
    
    output_folder: StringProperty(
        name="Output Folder",
        description="Directory to save rendered images",
        default="//renders/",
        subtype='DIR_PATH',
    )
    
    collection_prefix: StringProperty(
        name="Collection Prefix",
        description="Only process collections starting with this prefix (leave empty for all)",
        default="RENDER_",
    )

    overwrite_mode: EnumProperty(
        name="If File Exists",
        description="What to do when output file already exists",
        items=[
            ('OVERWRITE', "Overwrite", "Replace existing file"),
            ('SKIP', "Skip", "Skip rendering if file exists"),
            ('INCREMENT', "Auto-number", "Add number suffix (_001, _002, etc.)"),
        ],
        default='OVERWRITE',
    )


# Registration
classes = (
    ScaleRenderProperties,
)


def register():
    # Register property group
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add properties to scene
    bpy.types.Scene.scale_render_props = PointerProperty(type=ScaleRenderProperties)
    
    # Register submodules
    operators.register()
    panel.register()
    
    print("Scale Render addon registered")


def unregister():
    # Unregister submodules
    panel.unregister()
    operators.unregister()
    
    # Remove properties
    del bpy.types.Scene.scale_render_props
    
    # Unregister property group
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("Scale Render addon unregistered")


if __name__ == "__main__":
    register()
