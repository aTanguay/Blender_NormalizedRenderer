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
    Get world-space bounding box dimensions of an object in millimeters.

    Args:
        obj: Blender object to measure

    Returns:
        (width, height, depth) in millimeters, accounting for scene unit scale
    """
    # Get world-space bounding box corners
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    xs = [v.x for v in bbox_corners]
    ys = [v.y for v in bbox_corners]
    zs = [v.z for v in bbox_corners]

    # Get dimensions in Blender Units
    width = max(xs) - min(xs)   # X dimension
    depth = max(ys) - min(ys)   # Y dimension (into screen)
    height = max(zs) - min(zs)  # Z dimension (vertical)

    # Convert to millimeters using scene unit scale
    # bpy.context.scene.unit_settings.scale_length is the multiplier
    # If set to 0.001, then 1 BU = 1 meter = 1000mm
    # If set to 1.0, then 1 BU = 1 meter = 1000mm (default)
    # If set to 0.01, then 1 BU = 1 cm = 10mm
    unit_scale = bpy.context.scene.unit_settings.scale_length

    # Blender's default is: 1 BU = 1 meter when scale_length = 1.0
    # So we need to convert: BU -> meters -> millimeters
    meters_per_bu = unit_scale
    mm_per_meter = 1000.0

    width_mm = width * meters_per_bu * mm_per_meter
    height_mm = height * meters_per_bu * mm_per_meter
    depth_mm = depth * meters_per_bu * mm_per_meter

    return width_mm, height_mm, depth_mm


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
    collection: bpy.types.Collection,
    scale_factor: float,
    padding_px: int
) -> Tuple[Vector, Tuple[float, float, float]]:
    """
    Calculate camera position to properly frame all objects in a collection.

    Uses 85mm focal length with 12° downward angle for hero shot aesthetic.
    Camera positions in front of objects (negative Y), looking toward positive Y.

    This function ensures ALL corners of the bounding box are visible in the
    camera frame, accounting for perspective projection and elevation angle.

    Args:
        collection: Blender collection containing objects to frame
        scale_factor: Pixels per mm
        padding_px: Pixels to add on each edge

    Returns:
        (location, rotation_euler) for camera
    """
    # Get bounding box corners (not just dimensions)
    min_corner, max_corner, mesh_objects = get_collection_bounds(collection)

    if min_corner is None:
        # Fallback to origin if no valid objects
        return Vector((0, -1, 0.5)), (math.radians(78), 0, 0)

    center = get_collection_center(collection)
    width, height, depth = get_collection_dimensions(collection)

    print(f"DEBUG core.py: width={width}mm, height={height}mm, depth={depth}mm")
    print(f"DEBUG core.py: min_corner={min_corner}, max_corner={max_corner}")
    print(f"DEBUG core.py: center={center}")

    # Calculate padding in Blender Units
    unit_scale = bpy.context.scene.unit_settings.scale_length
    meters_per_bu = unit_scale
    mm_per_meter = 1000.0
    padding_mm = padding_px / scale_factor
    padding_bu = padding_mm / mm_per_meter / meters_per_bu

    # Calculate FOV from focal length (85mm lens on 36mm sensor)
    # This is the HALF angle for easier math
    half_fov_h = math.atan(SENSOR_WIDTH / (2 * FOCAL_LENGTH))

    # Calculate aspect ratio of our output
    res_w, res_h = calculate_resolution(width, height, scale_factor, padding_px)
    aspect = res_w / res_h

    # Vertical half-FOV based on horizontal FOV and aspect
    half_fov_v = math.atan(math.tan(half_fov_h) / aspect)

    print(f"DEBUG core.py: half_fov_h={math.degrees(half_fov_h):.2f}°, half_fov_v={math.degrees(half_fov_v):.2f}°")
    print(f"DEBUG core.py: aspect={aspect:.4f}, res={res_w}x{res_h}")

    # Generate all 8 corners of the bounding box (with padding)
    bbox_corners = [
        Vector((min_corner.x - padding_bu, min_corner.y, min_corner.z - padding_bu)),  # front-bottom-left
        Vector((max_corner.x + padding_bu, min_corner.y, min_corner.z - padding_bu)),  # front-bottom-right
        Vector((min_corner.x - padding_bu, min_corner.y, max_corner.z + padding_bu)),  # front-top-left
        Vector((max_corner.x + padding_bu, min_corner.y, max_corner.z + padding_bu)),  # front-top-right
        Vector((min_corner.x - padding_bu, max_corner.y, min_corner.z - padding_bu)),  # back-bottom-left
        Vector((max_corner.x + padding_bu, max_corner.y, min_corner.z - padding_bu)),  # back-bottom-right
        Vector((min_corner.x - padding_bu, max_corner.y, max_corner.z + padding_bu)),  # back-top-left
        Vector((max_corner.x + padding_bu, max_corner.y, max_corner.z + padding_bu)),  # back-top-right
    ]

    # We need to find a camera distance such that ALL corners fit in view
    # The camera is positioned along the -Y axis from the center, elevated by ELEVATION_ANGLE
    #
    # For each corner, we need to ensure it's within the frustum.
    # We'll use an iterative approach: start with an estimate and verify all corners fit.

    # Initial estimate: use the simple perpendicular calculation
    frame_width_bu = (max_corner.x - min_corner.x) + (padding_bu * 2)
    frame_height_bu = (max_corner.z - min_corner.z) + (padding_bu * 2)

    dist_for_width = (frame_width_bu / 2) / math.tan(half_fov_h)
    dist_for_height = (frame_height_bu / 2) / math.tan(half_fov_v)
    camera_distance = max(dist_for_width, dist_for_height)

    # Account for object depth - camera needs to see the front face
    # The front of the object is at min_corner.y, so distance should be from there
    object_front_y = min_corner.y

    # Iteratively increase distance until all corners fit
    # We check if each corner projects within the FOV angles
    max_iterations = 20
    for iteration in range(max_iterations):
        # Calculate camera position for this distance
        # Camera is at center.x, (object_front - distance), (center.z + elevation_offset)
        cam_x = center.x
        cam_y = object_front_y - camera_distance
        cam_z = center.z + (camera_distance * math.tan(ELEVATION_ANGLE))

        cam_location = Vector((cam_x, cam_y, cam_z))

        # Calculate the direction the camera is pointing (toward center)
        look_direction = (center - cam_location).normalized()

        # Check if all corners are within the frustum
        all_corners_visible = True
        max_h_angle = 0
        max_v_angle = 0

        for corner in bbox_corners:
            # Vector from camera to this corner
            to_corner = corner - cam_location

            # Project onto camera's local coordinate system
            # Camera looks along -Z (which is our look_direction)
            # Camera's local X is world X (horizontal)
            # Camera's local Y is perpendicular to look direction in the XZ plane

            # Distance along the look direction
            forward_dist = to_corner.dot(look_direction)

            if forward_dist <= 0:
                # Corner is behind the camera - definitely need more distance
                all_corners_visible = False
                break

            # Horizontal offset (X axis)
            horizontal_offset = corner.x - cam_x

            # Vertical offset - need to account for camera tilt
            # The camera is tilted down by ELEVATION_ANGLE
            # So "up" in camera space is rotated
            # Vertical offset in camera space is approximately:
            vertical_offset = (corner.z - cam_z) * math.cos(ELEVATION_ANGLE) + \
                              (corner.y - cam_y) * math.sin(ELEVATION_ANGLE)

            # Calculate angles
            h_angle = abs(math.atan2(horizontal_offset, forward_dist))
            v_angle = abs(math.atan2(vertical_offset, forward_dist))

            max_h_angle = max(max_h_angle, h_angle)
            max_v_angle = max(max_v_angle, v_angle)

            # Check if within FOV (with small margin)
            if h_angle > half_fov_h * 0.98 or v_angle > half_fov_v * 0.98:
                all_corners_visible = False

        if all_corners_visible:
            print(f"DEBUG core.py: Iteration {iteration}: All corners visible at distance {camera_distance:.4f}")
            print(f"DEBUG core.py: max_h_angle={math.degrees(max_h_angle):.2f}° (limit {math.degrees(half_fov_h):.2f}°)")
            print(f"DEBUG core.py: max_v_angle={math.degrees(max_v_angle):.2f}° (limit {math.degrees(half_fov_v):.2f}°)")
            break
        else:
            # Increase distance by 10%
            camera_distance *= 1.10
            print(f"DEBUG core.py: Iteration {iteration}: Increasing distance to {camera_distance:.4f}")

    # Add safety buffer
    camera_distance *= 1.05

    # Final camera position
    cam_x = center.x
    cam_y = object_front_y - camera_distance
    cam_z = center.z + (camera_distance * math.tan(ELEVATION_ANGLE))

    location = Vector((cam_x, cam_y, cam_z))

    print(f"DEBUG core.py: FINAL camera_distance={camera_distance:.4f}")
    print(f"DEBUG core.py: ELEVATION_ANGLE={math.degrees(ELEVATION_ANGLE):.2f}°")
    print(f"DEBUG core.py: location={location}")
    print(f"DEBUG core.py: actual distance to center={(location - center).length:.4f}")

    # Calculate rotation to point camera at object center
    # Blender cameras look down their local -Z axis
    direction = center - location
    print(f"DEBUG core.py: direction={direction}")
    direction.normalize()
    print(f"DEBUG core.py: direction (normalized)={direction}")

    # Create rotation quaternion to point -Z at the target
    # Use 'Y' as up vector to keep camera upright
    quat = direction.to_track_quat('-Z', 'Y')
    rotation = quat.to_euler('XYZ')

    print(f"DEBUG core.py: rotation (deg)=X:{math.degrees(rotation.x):.2f}° Y:{math.degrees(rotation.y):.2f}° Z:{math.degrees(rotation.z):.2f}°")

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


def get_collection_bounds(collection: bpy.types.Collection) -> Tuple[Vector, Vector, List[bpy.types.Object]]:
    """
    Get the combined bounding box of all mesh objects in a collection.

    This treats all meshes in the collection as a single composite object,
    which is the correct approach when a product is made from multiple parts.

    Args:
        collection: Collection to analyze

    Returns:
        (min_corner, max_corner, mesh_objects) tuple
        - min_corner: Vector of minimum (x, y, z) in world space
        - max_corner: Vector of maximum (x, y, z) in world space
        - mesh_objects: List of mesh objects that were included
    """
    mesh_objects = []
    all_corners = []

    for obj in collection.objects:
        # Only consider mesh objects
        if obj.type != 'MESH':
            continue

        # Skip helper objects (prefixed with '_')
        if obj.name.startswith('_'):
            continue

        mesh_objects.append(obj)

        # Get world-space bounding box corners for this object
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        all_corners.extend(bbox_corners)

    if not all_corners:
        return None, None, []

    # Find the overall min/max across all objects
    xs = [v.x for v in all_corners]
    ys = [v.y for v in all_corners]
    zs = [v.z for v in all_corners]

    min_corner = Vector((min(xs), min(ys), min(zs)))
    max_corner = Vector((max(xs), max(ys), max(zs)))

    return min_corner, max_corner, mesh_objects


def get_collection_dimensions(collection: bpy.types.Collection) -> Tuple[float, float, float]:
    """
    Get combined dimensions of all mesh objects in a collection in millimeters.

    Treats multiple meshes as a single composite object, which is correct
    for products made from multiple parts.

    Args:
        collection: Collection to measure

    Returns:
        (width, height, depth) in millimeters, or (0, 0, 0) if no valid meshes
    """
    min_corner, max_corner, mesh_objects = get_collection_bounds(collection)

    if min_corner is None:
        return 0.0, 0.0, 0.0

    # Calculate dimensions in Blender Units
    width = max_corner.x - min_corner.x
    depth = max_corner.y - min_corner.y
    height = max_corner.z - min_corner.z

    # Convert to millimeters using scene unit scale
    unit_scale = bpy.context.scene.unit_settings.scale_length
    meters_per_bu = unit_scale
    mm_per_meter = 1000.0

    width_mm = width * meters_per_bu * mm_per_meter
    height_mm = height * meters_per_bu * mm_per_meter
    depth_mm = depth * meters_per_bu * mm_per_meter

    return width_mm, height_mm, depth_mm


def get_collection_center(collection: bpy.types.Collection) -> Optional[Vector]:
    """
    Get the center point of all mesh objects in a collection.

    Args:
        collection: Collection to analyze

    Returns:
        Center point as Vector, or None if no valid meshes
    """
    min_corner, max_corner, mesh_objects = get_collection_bounds(collection)

    if min_corner is None:
        return None

    center = Vector((
        (max_corner.x + min_corner.x) / 2,
        (max_corner.y + min_corner.y) / 2,
        (max_corner.z + min_corner.z) / 2
    ))

    return center


def get_primary_object(collection: bpy.types.Collection) -> Optional[bpy.types.Object]:
    """
    Get a representative mesh object from a collection.

    NOTE: This function is deprecated in favor of using collection-level
    dimensions (get_collection_dimensions), but is kept for backward compatibility.

    When working with collections that have multiple meshes, you should use
    the collection-level functions instead.

    Args:
        collection: Collection to search

    Returns:
        First valid mesh object or None if no valid objects found
    """
    for obj in collection.objects:
        # Only consider mesh objects
        if obj.type != 'MESH':
            continue

        # Skip objects that might be light geometry or helpers
        if obj.name.startswith('_'):
            continue

        return obj

    return None


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


def validate_collection_dimensions(collection: bpy.types.Collection) -> Tuple[bool, str]:
    """
    Validate that collection has non-zero dimensions and is within reasonable bounds.

    Checks combined bounding box of all mesh objects in the collection.

    Checks for:
    - Zero or negative dimensions
    - Unreasonably small (< 1mm) - likely modeling error
    - Unreasonably large (> 10m) - may cause render issues

    Args:
        collection: Blender collection to validate

    Returns:
        (valid, message) tuple - valid is bool, message is error string if invalid
    """
    width, height, depth = get_collection_dimensions(collection)

    # Check for zero or negative dimensions
    if width <= 0 or height <= 0 or depth <= 0:
        return False, f"Collection '{collection.name}' has invalid dimensions: {width:.2f}×{height:.2f}×{depth:.2f}mm"

    # Check for unreasonably small objects (< 1mm - likely modeling error)
    if width < 1 or height < 1:
        return False, f"Collection '{collection.name}' too small (< 1mm): {width:.2f}×{height:.2f}mm"

    # Check for unreasonably large objects (> 10 meters)
    if width > 10000 or height > 10000 or depth > 10000:
        return False, f"Collection '{collection.name}' too large (> 10m): {width:.1f}×{height:.1f}×{depth:.1f}mm"

    return True, ""


def validate_object_dimensions(obj: bpy.types.Object) -> Tuple[bool, str]:
    """
    Validate that object has non-zero dimensions and is within reasonable bounds.

    NOTE: Deprecated in favor of validate_collection_dimensions.
    Use validate_collection_dimensions for multi-mesh products.

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
