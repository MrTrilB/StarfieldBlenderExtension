import bpy

from ..utils.registry import get_default_registry_dir, list_registered_rigs, sanitize_name


def registered_rig_enum_items(self, context):
    items = list_registered_rigs(context.scene.bgs_starfield_animation_tool_props.rig_registry_dir)

    # Include rig armatures from the current scene so users can register rigs from selection.
    scene_rig_names = []
    if context and context.scene:
        for obj in context.scene.objects:
            if obj.type != 'ARMATURE':
                continue
            rig_props = obj.bgs_starfield_animation_rig_props
            if not rig_props.is_rig:
                continue
            rig_name = sanitize_name(rig_props.rig_name) if rig_props.rig_name else sanitize_name(obj.name)
            if rig_name and rig_name != "NONE":
                scene_rig_names.append(rig_name)

    existing_ids = {item[0] for item in items if item[0] != "NONE"}
    for rig_name in sorted(set(scene_rig_names)):
        if rig_name not in existing_ids:
            items.append((rig_name, rig_name, f"Scene rig: {rig_name}"))

    # Remove placeholder when real options exist.
    real_items = [item for item in items if item[0] != "NONE"]
    return real_items if real_items else items


class BGSStarfieldAnimationToolProperties(bpy.types.PropertyGroup):
    rig_registry_dir: bpy.props.StringProperty(
        name="Rig Registry Folder",
        description="Folder where registered .rig files are stored",
        subtype='DIR_PATH',
        default=get_default_registry_dir(),
    )

    selected_rig: bpy.props.EnumProperty(
        name="Registered Rig",
        description="Rig used for .af import/export",
        items=registered_rig_enum_items,
    )

    import_af_mode: bpy.props.EnumProperty(
        name="AF Import Mode",
        description="How imported animation should be attached in Blender",
        items=[
            ('AS_ARMATURE', "As Armature", "Create a new armature for imported animation"),
            ('ON_ACTIVE_OBJECT', "On Active Object", "Apply animation to active armature (or mesh via armature modifier)")
        ],
        default='AS_ARMATURE',
    )

    set_frame_end: bpy.props.BoolProperty(
        name="Set Scene End Frame",
        description="Set timeline end frame to imported animation range",
        default=True,
    )

    edit_frame_offset: bpy.props.IntProperty(
        name="Frame Offset",
        description="Shift all keyframes by this number of frames",
        default=0,
    )

    edit_time_scale: bpy.props.FloatProperty(
        name="Time Scale",
        description="Scale keyframe timing (2.0 = slower, 0.5 = faster)",
        default=1.0,
        min=0.001,
        soft_min=0.1,
        soft_max=4.0,
    )

    edit_root_motion_offset: bpy.props.FloatVectorProperty(
        name="Root Motion Offset",
        description="Add translation offset to root bone location keys",
        subtype='TRANSLATION',
        size=3,
        default=(0.0, 0.0, 0.0),
    )

    edit_set_scene_range: bpy.props.BoolProperty(
        name="Update Scene Range",
        description="Update timeline start/end after applying edits",
        default=True,
    )


class BGSStarfieldRigObjectProperties(bpy.types.PropertyGroup):
    is_rig: bpy.props.BoolProperty(name="Is Starfield Rig", default=False)
    rig_name: bpy.props.StringProperty(name="Rig Name", default="")
    rig_precision: bpy.props.EnumProperty(
        name="Rig Precision",
        items=[
            ('DEFAULT', "DEFAULT", "Default precision"),
            ('FIRST_PERSON', "FIRST_PERSON", "First-person precision"),
            ('SHIP', "SHIP", "Ship precision"),
        ],
        default='DEFAULT',
    )


class BGSStarfieldAnimationObjectProperties(bpy.types.PropertyGroup):
    is_animation: bpy.props.BoolProperty(name="Is Starfield Animation", default=False)
    animation_name: bpy.props.StringProperty(name="Animation Name", default="")
    source_rig_name: bpy.props.StringProperty(name="Source Rig", default="")
