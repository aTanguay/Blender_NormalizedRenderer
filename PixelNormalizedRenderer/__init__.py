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


def get_collection_names(prefix: str):
    """
    Get list of collection names matching the prefix.

    Returns:
        List of collection name strings
    """
    collections = core.get_filtered_collections(prefix)
    return [coll.name for coll in collections]


def on_collection_prefix_changed(self, context):
    """
    Callback when collection prefix changes.
    Reset selected collection if it no longer matches the prefix.
    """
    if self.selected_collection:
        if not self.selected_collection.startswith(self.collection_prefix):
            self.selected_collection = ""

    # Force panel redraw
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


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
        update=on_collection_prefix_changed,
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

    # Using StringProperty instead of dynamic EnumProperty to avoid Blender's
    # enum caching issues. The panel will display this using a custom UI.
    selected_collection: StringProperty(
        name="Active Collection",
        description="Name of the collection to evaluate and render",
        default="",
    )

    # Cache for last evaluated collection (internal use)
    last_evaluated_collection: StringProperty(
        name="Last Evaluated Collection",
        description="Name of the collection that was last evaluated",
        default="",
    )

    last_eval_width: FloatProperty(default=0.0)
    last_eval_height: FloatProperty(default=0.0)
    last_eval_depth: FloatProperty(default=0.0)
    last_eval_res_x: IntProperty(default=0)
    last_eval_res_y: IntProperty(default=0)


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
