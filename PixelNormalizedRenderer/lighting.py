"""
Lighting system for Scale Render Addon
Handles default scaling light rig and per-collection overrides
"""

import bpy
import math
from mathutils import Vector
from typing import Tuple

from . import core


# Constants
LIGHT_RIG_NAME = "SCALE_RENDER_LightRig"
REFERENCE_HEIGHT = 200.0  # mm - base calibration size for light rig scaling

# Base light energies (calibrated for 200mm tall object)
BASE_KEY_ENERGY = 1000.0
BASE_FILL_ENERGY = 300.0
BASE_RIM_ENERGY = 500.0

# Light positions relative to reference object (in mm from center)
# Values tuned for three-point lighting on product renders
KEY_LIGHT_OFFSET = Vector((150, -200, 250))   # Front-right, elevated 45°
FILL_LIGHT_OFFSET = Vector((-200, -150, 100)) # Front-left, lower angle
RIM_LIGHT_OFFSET = Vector((100, 200, 200))    # Behind, edge separation

# Light characteristics
KEY_LIGHT_SIZE = 2.0   # Smaller for sharper shadows
FILL_LIGHT_SIZE = 3.0  # Larger for softer fill
RIM_LIGHT_SIZE = 1.5   # Small for edge highlight

# Light rotation angles (in degrees, converted to radians in code)
KEY_LIGHT_ROTATION = (45, 0, 30)
FILL_LIGHT_ROTATION = (60, 0, -45)
RIM_LIGHT_ROTATION = (135, 0, 20)


def collection_has_lights(collection: bpy.types.Collection) -> bool:
    """
    Check if a collection contains any light objects.

    If lights are found, the addon will use those instead of the default rig.

    Args:
        collection: Collection to check

    Returns:
        True if collection contains one or more lights
    """
    for obj in collection.objects:
        if obj.type == 'LIGHT':
            return True
    return False


def count_collection_lights(collection: bpy.types.Collection) -> int:
    """
    Count light objects in a collection.

    Args:
        collection: Collection to count lights in

    Returns:
        Number of light objects found
    """
    count = 0
    for obj in collection.objects:
        if obj.type == 'LIGHT':
            count += 1
    return count


def get_or_create_light_rig() -> bpy.types.Object:
    """
    Get existing light rig or create a new one.

    Creates a three-point lighting setup (key/fill/rim) parented to an empty.
    All positions and energies are calibrated for a 200mm tall reference object.

    Returns:
        The rig empty object (parent of all lights)
    """
    # Check if rig already exists
    if LIGHT_RIG_NAME in bpy.data.objects:
        return bpy.data.objects[LIGHT_RIG_NAME]
    
    # Create the rig empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    rig_empty = bpy.context.active_object
    rig_empty.name = LIGHT_RIG_NAME
    
    # Create key light (front-right, above)
    key_light = create_area_light(
        name="SCALE_RENDER_Key",
        energy=BASE_KEY_ENERGY,
        size=KEY_LIGHT_SIZE,
        location=KEY_LIGHT_OFFSET,
        rotation=tuple(math.radians(a) for a in KEY_LIGHT_ROTATION)
    )
    key_light.parent = rig_empty

    # Create fill light (front-left, lower)
    fill_light = create_area_light(
        name="SCALE_RENDER_Fill",
        energy=BASE_FILL_ENERGY,
        size=FILL_LIGHT_SIZE,
        location=FILL_LIGHT_OFFSET,
        rotation=tuple(math.radians(a) for a in FILL_LIGHT_ROTATION)
    )
    fill_light.parent = rig_empty

    # Create rim light (behind, for edge separation)
    rim_light = create_area_light(
        name="SCALE_RENDER_Rim",
        energy=BASE_RIM_ENERGY,
        size=RIM_LIGHT_SIZE,
        location=RIM_LIGHT_OFFSET,
        rotation=tuple(math.radians(a) for a in RIM_LIGHT_ROTATION)
    )
    rim_light.parent = rig_empty
    
    return rig_empty


def create_area_light(
    name: str,
    energy: float,
    size: float,
    location: Tuple[float, float, float],
    rotation: Tuple[float, float, float]
) -> bpy.types.Object:
    """
    Create an area light with specified parameters.

    Args:
        name: Name for the light object
        energy: Light energy/intensity
        size: Size of area light (square)
        location: (x, y, z) position
        rotation: (x, y, z) Euler rotation in radians

    Returns:
        Created light object
    """
    # Create light data
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_data.size = size
    light_data.shape = 'SQUARE'
    
    # Create light object
    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    
    # Link to scene
    bpy.context.scene.collection.objects.link(light_obj)
    
    # Set transform
    light_obj.location = location
    light_obj.rotation_euler = rotation
    
    return light_obj


def scale_light_rig_for_collection(collection: bpy.types.Collection) -> None:
    """
    Scale the default light rig to match the collection's combined size.

    Handles collections with multiple mesh objects by using the combined
    bounding box dimensions.

    Adjusts both position scale and light intensities to compensate for
    inverse square falloff. Intensity scales with the square of the distance.

    Args:
        collection: Collection to scale rig for
    """
    from . import core  # Import here to avoid circular dependency

    rig = get_or_create_light_rig()

    # Get collection dimensions and center
    width, height, depth = core.get_collection_dimensions(collection)
    collection_center = core.get_collection_center(collection)

    # Calculate scale factor based on height vs reference
    scale_factor = height / REFERENCE_HEIGHT

    # Prevent extreme scales
    scale_factor = max(0.1, min(scale_factor, 20.0))

    # Position rig at collection center
    rig.location = collection_center

    # Scale the rig
    rig.scale = (scale_factor, scale_factor, scale_factor)

    # Adjust light intensities to compensate for distance (inverse square)
    intensity_multiplier = scale_factor ** 2

    for child in rig.children:
        if child.type == 'LIGHT':
            light_data = child.data
            base_name = child.name.replace("SCALE_RENDER_", "")

            if "Key" in base_name:
                light_data.energy = BASE_KEY_ENERGY * intensity_multiplier
            elif "Fill" in base_name:
                light_data.energy = BASE_FILL_ENERGY * intensity_multiplier
            elif "Rim" in base_name:
                light_data.energy = BASE_RIM_ENERGY * intensity_multiplier

            # Also scale the light size
            light_data.size = 2.0 * scale_factor


def scale_light_rig(target_obj: bpy.types.Object) -> None:
    """
    Scale the default light rig to match the target object size.

    NOTE: Deprecated in favor of scale_light_rig_for_collection.
    Kept for backward compatibility.

    Adjusts both position scale and light intensities to compensate for
    inverse square falloff. Intensity scales with the square of the distance.

    Args:
        target_obj: Object to scale rig for
    """
    rig = get_or_create_light_rig()

    # Get object dimensions
    width, height, depth = core.get_object_dimensions(target_obj)
    obj_center = core.get_object_center(target_obj)

    # Calculate scale factor based on object height vs reference
    scale_factor = height / REFERENCE_HEIGHT

    # Prevent extreme scales
    scale_factor = max(0.1, min(scale_factor, 20.0))

    # Position rig at object center
    rig.location = obj_center

    # Scale the rig
    rig.scale = (scale_factor, scale_factor, scale_factor)

    # Adjust light intensities to compensate for distance (inverse square)
    intensity_multiplier = scale_factor ** 2

    for child in rig.children:
        if child.type == 'LIGHT':
            light_data = child.data
            base_name = child.name.replace("SCALE_RENDER_", "")

            if "Key" in base_name:
                light_data.energy = BASE_KEY_ENERGY * intensity_multiplier
            elif "Fill" in base_name:
                light_data.energy = BASE_FILL_ENERGY * intensity_multiplier
            elif "Rim" in base_name:
                light_data.energy = BASE_RIM_ENERGY * intensity_multiplier

            # Also scale the light size
            light_data.size = 2.0 * scale_factor


def show_light_rig(show=True):
    """
    Show or hide the default light rig.
    """
    if LIGHT_RIG_NAME not in bpy.data.objects:
        if show:
            get_or_create_light_rig()
        return
    
    rig = bpy.data.objects[LIGHT_RIG_NAME]
    rig.hide_viewport = not show
    rig.hide_render = not show
    
    # Also hide/show children
    for child in rig.children:
        child.hide_viewport = not show
        child.hide_render = not show


def setup_lighting_for_collection(collection: bpy.types.Collection) -> str:
    """
    Set up lighting for rendering a collection.

    Uses collection lights if available, otherwise scales default rig
    based on combined dimensions of all meshes in the collection.

    This is the main entry point for lighting configuration.

    Args:
        collection: Collection being rendered

    Returns:
        Description of lighting setup for UI feedback
    """
    from . import core  # Import here to avoid circular dependency

    if collection_has_lights(collection):
        # Use collection's own lights
        show_light_rig(show=False)
        light_count = count_collection_lights(collection)
        return f"Using collection lights ({light_count} found)"
    else:
        # Use and scale default rig based on collection dimensions
        show_light_rig(show=True)
        scale_light_rig_for_collection(collection)
        return "Using scaled default lighting"


def setup_lighting_for_object(target_obj: bpy.types.Object, collection: bpy.types.Collection) -> str:
    """
    Set up lighting for rendering a specific object.

    NOTE: Deprecated in favor of setup_lighting_for_collection.
    Kept for backward compatibility.

    Uses collection lights if available, otherwise scales default rig.

    Args:
        target_obj: Object being rendered
        collection: Collection containing the object

    Returns:
        Description of lighting setup for UI feedback
    """
    if collection_has_lights(collection):
        # Use collection's own lights
        show_light_rig(show=False)
        light_count = count_collection_lights(collection)
        return f"Using collection lights ({light_count} found)"
    else:
        # Use and scale default rig
        show_light_rig(show=True)
        scale_light_rig(target_obj)
        return "Using scaled default lighting"


def delete_light_rig():
    """
    Remove the default light rig entirely.
    Useful for cleanup or reset.
    """
    if LIGHT_RIG_NAME not in bpy.data.objects:
        return
    
    rig = bpy.data.objects[LIGHT_RIG_NAME]
    
    # Delete children first
    for child in rig.children:
        if child.type == 'LIGHT':
            bpy.data.lights.remove(child.data)
        bpy.data.objects.remove(child)
    
    # Delete rig empty
    bpy.data.objects.remove(rig)
