"""
Operators for Scale Render Addon
Eval, Render Active, and Render All functionality
"""

import bpy
import os
from bpy.types import Operator

from . import core
from . import lighting


class SCALE_RENDER_OT_eval(Operator):
    """Set up camera and resolution for the active collection without rendering"""
    bl_idname = "scale_render.eval"
    bl_label = "Eval"
    bl_description = "Preview framing and resolution without rendering"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def execute(self, context):
        props = context.scene.scale_render_props

        # Get active collection
        collection = core.get_target_collection(context, props.collection_prefix)

        if collection is None:
            self.report({'ERROR'}, f"No collections found matching prefix '{props.collection_prefix}'")
            return {'CANCELLED'}

        # Check that collection has mesh objects
        obj = core.get_primary_object(collection)
        if obj is None:
            self.report({'ERROR'}, f"No mesh objects found in collection '{collection.name}'")
            return {'CANCELLED'}

        # Validate collection dimensions (handles multiple meshes)
        valid, msg = core.validate_collection_dimensions(collection)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        # Calculate combined dimensions of all meshes in collection
        width, height, depth = core.get_collection_dimensions(collection)

        # Calculate resolution
        res_x, res_y = core.calculate_resolution(
            width, height,
            props.scale_factor,
            props.padding_px
        )

        # Validate resolution
        valid, msg = core.validate_resolution(res_x, res_y)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        elif msg:  # Warning message
            self.report({'WARNING'}, msg)

        # Set render resolution
        context.scene.render.resolution_x = res_x
        context.scene.render.resolution_y = res_y
        context.scene.render.resolution_percentage = 100

        # Set up render settings (transparent, PNG)
        core.setup_render_settings()

        # Get or create camera
        camera = core.get_or_create_camera(context)

        # Position camera to frame entire collection
        location, rotation = core.calculate_camera_position(
            collection,
            props.scale_factor,
            props.padding_px
        )

        camera.location = location
        camera.rotation_euler = rotation

        # Set camera as active
        context.scene.camera = camera

        # Set up lighting (uses collection center)
        lighting_info = lighting.setup_lighting_for_collection(collection)

        # Update viewport to show camera view
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'CAMERA'
                        break

        # Report results
        self.report({'INFO'},
            f"Eval: {collection.name} | {width:.1f}×{height:.1f}mm → {res_x}×{res_y}px | {lighting_info}")

        return {'FINISHED'}


class SCALE_RENDER_OT_render_active(Operator):
    """Render the active collection at calculated scale"""
    bl_idname = "scale_render.render_active"
    bl_label = "Render Active"
    bl_description = "Render the current collection at proper scale"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def execute(self, context):
        props = context.scene.scale_render_props

        # Validate output path
        valid, msg, output_dir = core.validate_output_path(props.output_folder)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        # First run eval to set everything up
        bpy.ops.scale_render.eval()

        # Get collection name for filename
        collection = core.get_target_collection(context, props.collection_prefix)
        if collection is None:
            self.report({'ERROR'}, "No valid collection found")
            return {'CANCELLED'}

        filename = core.get_output_filename(collection.name, props.collection_prefix)
        filepath = os.path.join(output_dir, filename)

        # Check overwrite mode
        should_render, final_path = core.resolve_output_filepath(filepath, props.overwrite_mode)

        if not should_render:
            self.report({'INFO'}, f"Skipped (file exists): {filename}")
            return {'FINISHED'}

        # Set output path
        context.scene.render.filepath = final_path

        # Render
        bpy.ops.render.render(write_still=True)

        # Report with actual filename (might be auto-numbered)
        actual_filename = os.path.basename(final_path)
        self.report({'INFO'}, f"Rendered: {actual_filename}")

        return {'FINISHED'}


class SCALE_RENDER_OT_render_all(Operator):
    """Batch render all collections matching the prefix"""
    bl_idname = "scale_render.render_all"
    bl_label = "Render All"
    bl_description = "Batch render all matching collections"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def execute(self, context):
        props = context.scene.scale_render_props
        
        # Get all matching collections
        collections = core.get_filtered_collections(props.collection_prefix)
        
        if not collections:
            self.report({'ERROR'}, f"No collections found matching prefix '{props.collection_prefix}'")
            return {'CANCELLED'}

        # Validate output path
        valid, msg, output_dir = core.validate_output_path(props.output_folder)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}
        
        # Set up render settings
        core.setup_render_settings()

        # Get or create camera
        camera = core.get_or_create_camera(context)
        context.scene.camera = camera

        # Track results
        successful = 0
        failed = 0
        skipped = 0
        errors = []

        # Store original visibility states
        original_states = {}
        for coll in collections:
            original_states[coll.name] = {
                'hide_viewport': coll.hide_viewport,
                'hide_render': coll.hide_render
            }

        # Set up progress indicator
        wm = context.window_manager
        wm.progress_begin(0, len(collections))

        # Process each collection
        for i, collection in enumerate(collections):
            wm.progress_update(i)
            print(f"Rendering {i+1}/{len(collections)}: {collection.name}")

            try:
                # Check that collection has mesh objects
                obj = core.get_primary_object(collection)

                if obj is None:
                    errors.append(f"{collection.name}: No mesh objects found")
                    failed += 1
                    continue

                # Validate collection dimensions (handles multiple meshes)
                valid, msg = core.validate_collection_dimensions(collection)
                if not valid:
                    errors.append(f"{collection.name}: {msg}")
                    failed += 1
                    continue

                # Set visibility - show only this collection
                core.set_collection_visibility(collection, collections)

                # Calculate combined dimensions of all meshes
                width, height, depth = core.get_collection_dimensions(collection)
                res_x, res_y = core.calculate_resolution(
                    width, height,
                    props.scale_factor,
                    props.padding_px
                )

                # Validate resolution
                valid, msg = core.validate_resolution(res_x, res_y)
                if not valid:
                    errors.append(f"{collection.name}: {msg}")
                    failed += 1
                    continue

                # Set resolution
                context.scene.render.resolution_x = res_x
                context.scene.render.resolution_y = res_y

                # Position camera to frame entire collection
                location, rotation = core.calculate_camera_position(
                    collection,
                    props.scale_factor,
                    props.padding_px
                )
                camera.location = location
                camera.rotation_euler = rotation

                # Set up lighting (uses collection center)
                lighting.setup_lighting_for_collection(collection)

                # Set output path and check overwrite mode
                filename = core.get_output_filename(collection.name, props.collection_prefix)
                filepath = os.path.join(output_dir, filename)

                # Check overwrite mode
                should_render, final_path = core.resolve_output_filepath(filepath, props.overwrite_mode)

                if not should_render:
                    skipped += 1
                    print(f"  ⊘ {filename} (skipped - file exists)")
                    continue

                context.scene.render.filepath = final_path

                # Render
                bpy.ops.render.render(write_still=True)

                successful += 1
                actual_filename = os.path.basename(final_path)
                print(f"  ✓ {actual_filename} ({res_x}×{res_y})")

            except (RuntimeError, ValueError, TypeError) as e:
                errors.append(f"{collection.name}: {str(e)}")
                failed += 1
                print(f"  ✗ Error: {str(e)}")
            except KeyboardInterrupt:
                # Allow user to cancel
                wm.progress_end()
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

        # End progress indicator
        wm.progress_end()

        # Restore visibility
        core.restore_collection_visibility(collections, original_states)

        # Show light rig again
        lighting.show_light_rig(show=True)

        # Report summary
        summary = f"Batch complete: {successful} rendered"
        if skipped > 0:
            summary += f", {skipped} skipped"
        if failed > 0:
            summary += f", {failed} failed"

        if errors:
            for err in errors:
                print(f"Error: {err}")

        self.report({'INFO'}, summary)

        return {'FINISHED'}


# Registration
classes = (
    SCALE_RENDER_OT_eval,
    SCALE_RENDER_OT_render_active,
    SCALE_RENDER_OT_render_all,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
