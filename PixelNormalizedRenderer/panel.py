"""
UI Panel for Scale Render Addon
Sidebar panel in 3D Viewport
"""

import bpy
from bpy.types import Panel

from . import core


class SCALE_RENDER_PT_main_panel(Panel):
    """Scale Render main panel"""
    bl_label = "Scale Render"
    bl_idname = "SCALE_RENDER_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Scale Render'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.scale_render_props
        
        # Settings section
        box = layout.box()
        box.label(text="Settings", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(props, "scale_factor")
        col.prop(props, "padding_px")

        box.prop(props, "output_folder")
        box.prop(props, "overwrite_mode")
        box.prop(props, "collection_prefix")
        
        layout.separator()
        
        # Object info section
        obj_info = self.get_active_object_info(context, props)
        
        if obj_info:
            box = layout.box()
            box.label(text="Active Object", icon='OBJECT_DATA')
            
            col = box.column(align=True)
            col.label(text=f"Collection: {obj_info['collection']}")
            col.label(text=f"Object: {obj_info['object']}")
            col.separator()
            col.label(text=f"Size: {obj_info['width']:.1f} × {obj_info['height']:.1f} × {obj_info['depth']:.1f} mm")
            col.label(text=f"Output: {obj_info['res_x']} × {obj_info['res_y']} px")
            col.label(text=f"Camera dist: {obj_info['cam_dist']:.1f} mm")
        else:
            box = layout.box()
            box.label(text="No valid object selected", icon='INFO')
            box.label(text=f"Select object in '{props.collection_prefix}*' collection")
        
        layout.separator()
        
        # Action buttons
        col = layout.column(align=True)
        col.scale_y = 1.5
        col.operator("scale_render.eval", icon='VIEWZOOM')
        
        layout.separator()
        
        col = layout.column(align=True)
        col.scale_y = 1.5
        col.operator("scale_render.render_active", icon='RENDER_STILL')
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("scale_render.render_all", icon='RENDER_ANIMATION')

        # Collection count with warning if none found
        collections = core.get_filtered_collections(props.collection_prefix)
        layout.label(text=f"{len(collections)} collections match prefix")

        if len(collections) == 0 and props.collection_prefix != "":
            box = layout.box()
            box.alert = True  # Red warning box
            col = box.column(align=True)
            col.label(text="No collections found!", icon='ERROR')
            col.label(text=f"Create collection starting with:")
            col.label(text=f"'{props.collection_prefix}'")
        elif len(collections) == 0:
            box = layout.box()
            box.alert = True
            box.label(text="No collections in scene!", icon='INFO')
    
    def get_active_object_info(self, context, props):
        """Get info about the currently active/selected collection."""
        if not context.active_object:
            return None

        # Find matching collection
        target_collection = None
        for coll in context.active_object.users_collection:
            if props.collection_prefix == "" or coll.name.startswith(props.collection_prefix):
                target_collection = coll
                break

        if not target_collection:
            return None

        # Check collection has mesh objects
        obj = core.get_primary_object(target_collection)
        if not obj:
            return None

        # Calculate collection info (handles multiple meshes)
        width, height, depth = core.get_collection_dimensions(target_collection)
        res_x, res_y = core.calculate_resolution(
            width, height,
            props.scale_factor,
            props.padding_px
        )

        location, _ = core.calculate_camera_position(
            target_collection,
            props.scale_factor,
            props.padding_px
        )
        center = core.get_collection_center(target_collection)

        if center is None:
            return None

        cam_dist = (location - center).length

        # Get count of mesh objects in collection
        mesh_count = len([o for o in target_collection.objects if o.type == 'MESH' and not o.name.startswith('_')])

        return {
            'collection': target_collection.name,
            'object': f"{mesh_count} mesh{'es' if mesh_count != 1 else ''}",
            'width': width,
            'height': height,
            'depth': depth,
            'res_x': res_x,
            'res_y': res_y,
            'cam_dist': cam_dist
        }


# Registration
classes = (
    SCALE_RENDER_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
