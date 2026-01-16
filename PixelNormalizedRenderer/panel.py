"""
UI Panel for Scale Render Addon
Sidebar panel in 3D Viewport
"""

import bpy
from bpy.types import Panel, Menu, Operator
from bpy.props import StringProperty

from . import core


class SCALE_RENDER_OT_select_collection(Operator):
    """Select a collection for evaluation and rendering"""
    bl_idname = "scale_render.select_collection"
    bl_label = "Select Collection"
    bl_options = {'REGISTER', 'INTERNAL'}

    collection_name: StringProperty(
        name="Collection Name",
        description="Name of collection to select",
    )

    def execute(self, context):
        props = context.scene.scale_render_props
        props.selected_collection = self.collection_name
        print(f"DEBUG panel.py: Selected collection changed to '{self.collection_name}'")

        # Isolate selected collection - hide all other RENDER_ collections
        collection = bpy.data.collections.get(self.collection_name)
        if collection:
            all_render_collections = core.get_filtered_collections(props.collection_prefix)
            core.set_collection_visibility(collection, all_render_collections)

        # Force UI redraw
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class SCALE_RENDER_MT_collection_menu(Menu):
    """Menu listing all available collections for selection"""
    bl_idname = "SCALE_RENDER_MT_collection_menu"
    bl_label = "Select Collection"

    def draw(self, context):
        layout = self.layout
        props = context.scene.scale_render_props

        collections = core.get_filtered_collections(props.collection_prefix)

        if not collections:
            layout.label(text="No collections found", icon='ERROR')
            return

        for coll in collections:
            # Check if collection has valid mesh objects
            obj = core.get_primary_object(coll)
            icon = 'OUTLINER_COLLECTION' if obj else 'ERROR'

            # Add checkmark to currently selected
            if coll.name == props.selected_collection:
                icon = 'CHECKMARK'

            op = layout.operator("scale_render.select_collection",
                                 text=coll.name,
                                 icon=icon)
            op.collection_name = coll.name


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

        # Collection selector section
        collections = core.get_filtered_collections(props.collection_prefix)

        if collections:
            box = layout.box()
            box.label(text="Collection Selector", icon='OUTLINER_COLLECTION')

            # Custom dropdown menu for collection selection
            row = box.row(align=True)
            row.menu("SCALE_RENDER_MT_collection_menu",
                     text=props.selected_collection if props.selected_collection else "Select Collection...",
                     icon='OUTLINER_COLLECTION')

        layout.separator()

        # Object info section - show both selected and last evaluated
        obj_info = self.get_selected_collection_info(context, props)

        if obj_info:
            # Show selected collection info
            box = layout.box()

            # Highlight if this collection has been evaluated
            is_evaluated = (props.selected_collection == props.last_evaluated_collection)

            if is_evaluated:
                box.label(text="✓ Evaluated Collection", icon='CHECKMARK')
            else:
                box.label(text="Selected Collection (not evaluated)", icon='OBJECT_DATA')

            col = box.column(align=True)
            col.label(text=f"Collection: {obj_info['collection']}")
            col.label(text=f"Object: {obj_info['object']}")
            col.separator()
            col.label(text=f"Size: {obj_info['width']:.1f} × {obj_info['height']:.1f} × {obj_info['depth']:.1f} mm")

            if is_evaluated:
                # Show cached evaluation results
                col.label(text=f"Output: {props.last_eval_res_x} × {props.last_eval_res_y} px")
            else:
                # Show predicted output
                col.label(text=f"Output: {obj_info['res_x']} × {obj_info['res_y']} px (predicted)")

            col.label(text=f"Camera dist: {obj_info['cam_dist']:.1f} mm")
        else:
            box = layout.box()
            box.label(text="No collection selected", icon='INFO')
            if collections:
                box.label(text=f"Select collection from dropdown above")
            else:
                box.label(text=f"Create collection starting with '{props.collection_prefix}'")
        
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
    
    def get_selected_collection_info(self, context, props):
        """Get info about the selected collection from dropdown."""
        # Check if a collection is selected
        if not props.selected_collection:
            return None

        # Find the collection by name
        target_collection = bpy.data.collections.get(props.selected_collection)

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
    SCALE_RENDER_OT_select_collection,
    SCALE_RENDER_MT_collection_menu,
    SCALE_RENDER_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
