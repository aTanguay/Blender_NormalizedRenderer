"""
Core utilities for Scale Render Addon
Camera math, resolution calculation, collection handling
"""

import bpy
import math
from mathutils import Vector
from typing import Tuple, List, Optional


# Constants
FOCAL_LENGTH = 85.0  # mm, portrait lens
SENSOR_WIDTH = 36.0  # mm, full frame
ELEVATION_ANGLE = math.radians(12)  # 12 degrees downward
MAX_RESOLUTION = 16384  # Maximum output resolution (common GPU texture limit)


def get_object_dimensions(obj: bpy.types.Object) -> Tuple[float, float, float]:
    """
    Get world-space bounding box dimensions of an object.

    Args:
        obj: Blender object to measure

    Returns:
        (width, height, depth) in Blender units (assumed mm)
    """
    # Get world-space bounding box corners
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    xs = [v.x for v in bbox_corners]
    ys = [v.y for v in bbox_corners]
    zs = [v.z for v in bbox_corners]
    
    width = max(xs) - min(xs)   # X dimension
    depth = max(ys) - min(ys)   # Y dimension (into screen)
    height = max(zs) - min(zs)  # Z dimension (vertical)
    
    return width, height, depth


def get_object_center(obj: bpy.types.Object) -> Vector:
    """
    Get world-space center of object's bounding box.

    Args:
        obj: Blender object

    Returns:
        Center point as Vector
    """
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    xs = [v.x for v in bbox_corners]
    ys = [v.y for v in bbox_corners]
    zs = [v.z for v in bbox_corners]
    
    center = Vector((
        (max(xs) + min(xs)) / 2,
        (max(ys) + min(ys)) / 2,
        (max(zs) + min(zs)) / 2
    ))
    
    return center


def calculate_resolution(
    width_mm: float,
    height_mm: float,
    scale_factor: float,
    padding_px: int
) -> Tuple[int, int]:
    """
    Calculate output resolution based on object dimensions.

    Args:
        width_mm: Object width in mm
        height_mm: Object height in mm
        scale_factor: Pixels per mm (default 10)
        padding_px: Pixels to add on each edge

    Returns:
        (width_px, height_px) tuple
    """
    width_px = int(width_mm * scale_factor) + (padding_px * 2)
    height_px = int(height_mm * scale_factor) + (padding_px * 2)
    
    return width_px, height_px


def calculate_camera_position(
    obj: bpy.types.Object,
    scale_factor: float,
    padding_px: int
) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Calculate camera position to properly frame the object.

    Uses 85mm focal length with 12° downward angle for hero shot aesthetic.
    Camera positions in front of object (negative Y), looking toward positive Y.

    The distance calculation ensures the object fills the frame at the exact
    pixel-per-mm scale specified, accounting for perspective projection.

    Args:
        obj: Blender object to frame
        scale_factor: Pixels per mm
        padding_px: Pixels to add on each edge

    Returns:
        (location, rotation_euler) for camera
    """
    width, height, depth = get_object_dimensions(obj)
    center = get_object_center(obj)
    
    # Calculate the frame size we need in world units
    # Padding in mm = padding_px / scale_factor
    padding_mm = padding_px / scale_factor
    frame_width = width + (padding_mm * 2)
    frame_height = height + (padding_mm * 2)
    
    # Calculate FOV from focal length
    # Vertical FOV depends on aspect ratio and sensor fit
    # We'll calculate distance based on the limiting dimension
    
    # Horizontal FOV
    fov_h = 2 * math.atan(SENSOR_WIDTH / (2 * FOCAL_LENGTH))
    
    # Calculate aspect ratio of our output
    res_w, res_h = calculate_resolution(width, height, scale_factor, padding_px)
    aspect = res_w / res_h
    
    # Vertical FOV based on horizontal FOV and aspect
    fov_v = 2 * math.atan(math.tan(fov_h / 2) / aspect)
    
    # Distance needed to fit width
    dist_for_width = (frame_width / 2) / math.tan(fov_h / 2)
    
    # Distance needed to fit height
    dist_for_height = (frame_height / 2) / math.tan(fov_v / 2)
    
    # Use the larger distance to ensure both dimensions fit
    camera_distance = max(dist_for_width, dist_for_height)
    
    # Add a small buffer for safety
    camera_distance *= 1.05
    
    # Calculate camera position with elevation angle
    # Camera is in front of object (negative Y), looking toward positive Y
    # Elevation rotates camera up, so it looks slightly down
    
    cam_x = center.x
    cam_y = center.y - (camera_distance * math.cos(ELEVATION_ANGLE))
    cam_z = center.z + (camera_distance * math.sin(ELEVATION_ANGLE))
    
    location = Vector((cam_x, cam_y, cam_z))
    
    # Camera rotation: point at center
    # Base rotation is 90° around X to face forward (toward +Y)
    # Then tilt down by elevation angle
    rotation = (math.radians(90) - ELEVATION_ANGLE, 0, 0)
    
    return location, rotation


def get_filtered_collections(prefix: str) -> List[bpy.types.Collection]:
    """
    Get all collections matching the given prefix.

    Args:
        prefix: String prefix to match (e.g., "RENDER_")
                Empty string matches all collections.

    Returns:
        List of collection objects
    """
    collections = []
    
    for coll in bpy.data.collections:
        if prefix == "" or coll.name.startswith(prefix):
            # Skip empty collections
            if len(coll.objects) > 0:
                collections.append(coll)
    
    return collections


def get_primary_object(collection: bpy.types.Collection) -> Optional[bpy.types.Object]:
    """
    Get the primary (largest) mesh object from a collection.

    Selects the mesh object with the largest bounding box volume.
    Skips objects prefixed with '_' (helpers/lights).

    Args:
        collection: Collection to search

    Returns:
        Largest mesh object or None if no valid objects found
    """
    best_obj = None
    best_volume = 0
    
    for obj in collection.objects:
        # Only consider mesh objects
        if obj.type != 'MESH':
            continue
        
        # Skip objects that might be light geometry or helpers
        if obj.name.startswith('_'):
            continue
            
        width, height, depth = get_object_dimensions(obj)
        volume = width * height * depth
        
        if volume > best_volume:
            best_volume = volume
            best_obj = obj
    
    return best_obj


def get_output_filename(collection_name: str, prefix: str) -> str:
    """
    Generate output filename from collection name.

    Strips prefix and cleans up the name (spaces to underscores).

    Args:
        collection_name: Name of the collection
        prefix: Prefix to remove from name

    Returns:
        Cleaned filename with .png extension
    """
    name = collection_name
    
    if prefix and name.startswith(prefix):
        name = name[len(prefix):]
    
    # Clean up: strip whitespace, replace spaces with underscores
    name = name.strip().replace(' ', '_')
    
    return f"{name}.png"


def setup_render_settings():
    """
    Configure render settings for transparent PNG output.
    """
    scene = bpy.context.scene
    
    # Set PNG format with RGBA
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    
    # Enable transparent background
    scene.render.film_transparent = True


def set_collection_visibility(target_collection, all_collections):
    """
    Show only the target collection, hide all others.
    
    Args:
        target_collection: The collection to show
        all_collections: List of all render collections to manage
    
    Returns:
        Dict of original visibility states for restoration
    """
    original_states = {}
    
    for coll in all_collections:
        # Store original state
        original_states[coll.name] = {
            'hide_viewport': coll.hide_viewport,
            'hide_render': coll.hide_render
        }
        
        # Set visibility
        if coll == target_collection:
            coll.hide_viewport = False
            coll.hide_render = False
        else:
            coll.hide_viewport = True
            coll.hide_render = True
    
    return original_states


def restore_collection_visibility(all_collections, original_states):
    """
    Restore collection visibility to original states.
    """
    for coll in all_collections:
        if coll.name in original_states:
            coll.hide_viewport = original_states[coll.name]['hide_viewport']
            coll.hide_render = original_states[coll.name]['hide_render']


def validate_object_dimensions(obj: bpy.types.Object) -> Tuple[bool, str]:
    """
    Validate that object has non-zero dimensions and is within reasonable bounds.

    Checks for:
    - Zero or negative dimensions
    - Unreasonably small (< 1mm) - likely modeling error
    - Unreasonably large (> 10m) - may cause render issues

    Args:
        obj: Blender object to validate

    Returns:
        (valid, message) tuple - valid is bool, message is error string if invalid
    """
    width, height, depth = get_object_dimensions(obj)

    # Check for zero or negative dimensions
    if width <= 0 or height <= 0 or depth <= 0:
        return False, f"Object '{obj.name}' has invalid dimensions: {width:.2f}×{height:.2f}×{depth:.2f}mm"

    # Check for unreasonably small objects (< 1mm - likely modeling error)
    if width < 1 or height < 1:
        return False, f"Object '{obj.name}' too small (< 1mm): {width:.2f}×{height:.2f}mm"

    # Check for unreasonably large objects (> 10 meters)
    if width > 10000 or height > 10000 or depth > 10000:
        return False, f"Object '{obj.name}' too large (> 10m): {width:.1f}×{height:.1f}×{depth:.1f}mm"

    return True, ""


def validate_resolution(width_px: int, height_px: int) -> Tuple[bool, str]:
    """
    Validate that resolution is within reasonable bounds.

    Enforces max resolution of 16384px (GPU texture limit).
    Warns (but allows) resolutions > 8K.

    Args:
        width_px: Output width in pixels
        height_px: Output height in pixels

    Returns:
        (valid, message) tuple - valid is bool, message is error/warning string
    """
    if width_px > MAX_RESOLUTION or height_px > MAX_RESOLUTION:
        return False, f"Resolution too large: {width_px}×{height_px}px (max: {MAX_RESOLUTION}px per dimension)"

    if width_px < 1 or height_px < 1:
        return False, f"Resolution too small: {width_px}×{height_px}px"

    # Warn about very large images (> 8K) but allow them
    if width_px > 8192 or height_px > 8192:
        return True, f"Warning: Large resolution {width_px}×{height_px}px may render slowly"

    return True, ""


def get_or_create_camera(context: bpy.types.Context) -> bpy.types.Object:
    """
    Get existing scale render camera or create one.

    Creates camera with 85mm focal length and 36mm sensor if needed.

    Args:
        context: Blender context

    Returns:
        Camera object
    """
    cam_name = "SCALE_RENDER_Camera"

    if cam_name in bpy.data.objects:
        return bpy.data.objects[cam_name]

    # Create camera data
    cam_data = bpy.data.cameras.new(name=cam_name)
    cam_data.lens = FOCAL_LENGTH
    cam_data.sensor_width = SENSOR_WIDTH

    # Create camera object
    camera = bpy.data.objects.new(name=cam_name, object_data=cam_data)
    context.scene.collection.objects.link(camera)

    return camera


def get_target_collection(context: bpy.types.Context, prefix: str) -> Optional[bpy.types.Collection]:
    """
    Get the collection to work with - from active object or first matching.

    Tries active object's collection first, then falls back to first
    collection matching the prefix.

    Args:
        context: Blender context
        prefix: Collection prefix filter

    Returns:
        Collection object or None if not found
    """
    # First, try to get collection from active object
    if context.active_object:
        for coll in context.active_object.users_collection:
            if prefix == "" or coll.name.startswith(prefix):
                return coll

    # Fall back to first matching collection
    collections = get_filtered_collections(prefix)
    if collections:
        return collections[0]

    return None


def validate_output_path(output_folder: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate that output folder path is usable.

    Checks for:
    - Blend file saved (if using relative //)
    - Parent directory exists
    - Write permissions

    Args:
        output_folder: Path string (may be relative with //)

    Returns:
        (valid, message, resolved_path) tuple
    """
    import os

    # Resolve relative paths (// prefix means relative to .blend file)
    resolved = bpy.path.abspath(output_folder)

    # Check if blend file is saved (needed for relative paths)
    if output_folder.startswith("//") and not bpy.data.is_saved:
        return False, "Save .blend file before using relative path (//)", None

    # Check if path is absolute or blend file is saved
    if not os.path.isabs(resolved) and not bpy.data.is_saved:
        return False, "Use absolute path or save .blend file first", None

    # Check if parent directory exists (for creating output dir)
    parent = os.path.dirname(resolved) if resolved else ""
    if parent and not os.path.exists(parent):
        return False, f"Parent directory does not exist: {parent}", None

    # Try to create directory and check permissions
    try:
        os.makedirs(resolved, exist_ok=True)
    except PermissionError:
        return False, f"No write permission: {resolved}", None
    except Exception as e:
        return False, f"Cannot create directory: {str(e)}", None

    return True, "", resolved


def resolve_output_filepath(base_path: str, overwrite_mode: str) -> Tuple[bool, str]:
    """
    Resolve output file path based on overwrite mode.

    Modes:
    - OVERWRITE: Always use base_path
    - SKIP: Don't render if file exists
    - INCREMENT: Auto-number (_001, _002, etc.) if file exists

    Args:
        base_path: Desired output file path
        overwrite_mode: 'OVERWRITE', 'SKIP', or 'INCREMENT'

    Returns:
        (should_render, final_path) tuple
    """
    import os

    if overwrite_mode == 'OVERWRITE':
        return True, base_path

    if overwrite_mode == 'SKIP':
        if os.path.exists(base_path):
            return False, base_path
        return True, base_path

    if overwrite_mode == 'INCREMENT':
        if not os.path.exists(base_path):
            return True, base_path

        # Find next available number
        base, ext = os.path.splitext(base_path)
        counter = 1
        while os.path.exists(f"{base}_{counter:03d}{ext}"):
            counter += 1
        return True, f"{base}_{counter:03d}{ext}"

    return True, base_path
