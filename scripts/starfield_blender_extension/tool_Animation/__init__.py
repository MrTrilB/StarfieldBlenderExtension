import bpy

from .ui.properties import (
    BGSStarfieldAnimationToolProperties,
    BGSStarfieldRigObjectProperties,
    BGSStarfieldAnimationObjectProperties,
)
from .ui.panels import (
    VIEW3D_PT_bgs_starfield_animation_tools,
    VIEW3D_PT_bgs_starfield_animation_setup,
    VIEW3D_PT_bgs_starfield_animation_rig,
    VIEW3D_PT_bgs_starfield_animation_clip,
)
from .operators.setup_ops import (
    BGS_STARFIELD_OT_animation_mark_new_rig,
    BGS_STARFIELD_OT_animation_mark_new_clip,
    BGS_STARFIELD_OT_animation_select_registry_dir,
    BGS_STARFIELD_OT_animation_open_registry_dir,
    BGS_STARFIELD_OT_animation_register_rig_file,
)
from .operators.edit_ops import (
    BGS_STARFIELD_OT_animation_duplicate_action,
    BGS_STARFIELD_OT_animation_apply_action_edits,
)
from .operators.io_ops import (
    BGS_STARFIELD_OT_import_rig,
    BGS_STARFIELD_OT_export_rig,
    BGS_STARFIELD_OT_import_af,
    BGS_STARFIELD_OT_export_af,
)


classes = [
    BGSStarfieldAnimationToolProperties,
    BGSStarfieldRigObjectProperties,
    BGSStarfieldAnimationObjectProperties,
    BGS_STARFIELD_OT_animation_mark_new_rig,
    BGS_STARFIELD_OT_animation_mark_new_clip,
    BGS_STARFIELD_OT_animation_select_registry_dir,
    BGS_STARFIELD_OT_animation_open_registry_dir,
    BGS_STARFIELD_OT_animation_register_rig_file,
    BGS_STARFIELD_OT_animation_duplicate_action,
    BGS_STARFIELD_OT_animation_apply_action_edits,
    BGS_STARFIELD_OT_import_rig,
    BGS_STARFIELD_OT_export_rig,
    BGS_STARFIELD_OT_import_af,
    BGS_STARFIELD_OT_export_af,
    VIEW3D_PT_bgs_starfield_animation_tools,
    VIEW3D_PT_bgs_starfield_animation_setup,
    VIEW3D_PT_bgs_starfield_animation_rig,
    VIEW3D_PT_bgs_starfield_animation_clip,
]


def menu_func_import(self, context):
    self.layout.operator(BGS_STARFIELD_OT_import_rig.bl_idname, text="Starfield Rig (.rig)")
    self.layout.operator(BGS_STARFIELD_OT_import_af.bl_idname, text="Starfield Animation (.af)")


def menu_func_export(self, context):
    self.layout.operator(BGS_STARFIELD_OT_export_rig.bl_idname, text="Starfield Rig (.rig)")
    self.layout.operator(BGS_STARFIELD_OT_export_af.bl_idname, text="Starfield Animation (.af)")


def register():
    print("Registering tool_Animation")

    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            print(f"Class {cls.__name__} already registered")

    bpy.types.Scene.bgs_starfield_animation_tool_props = bpy.props.PointerProperty(type=BGSStarfieldAnimationToolProperties)
    bpy.types.Object.bgs_starfield_animation_rig_props = bpy.props.PointerProperty(type=BGSStarfieldRigObjectProperties)
    bpy.types.Object.bgs_starfield_animation_clip_props = bpy.props.PointerProperty(type=BGSStarfieldAnimationObjectProperties)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    del bpy.types.Object.bgs_starfield_animation_clip_props
    del bpy.types.Object.bgs_starfield_animation_rig_props
    del bpy.types.Scene.bgs_starfield_animation_tool_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
