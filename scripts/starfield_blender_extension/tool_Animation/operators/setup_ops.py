import bpy
import os

from ..utils.registry import ensure_registry_dir, sanitize_name


class BGS_STARFIELD_OT_animation_select_registry_dir(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.select_registry_dir"
    bl_label = "Select Registry Folder"

    filepath: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        context.scene.bgs_starfield_animation_tool_props.rig_registry_dir = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BGS_STARFIELD_OT_animation_open_registry_dir(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.open_registry_dir"
    bl_label = "Open Registry Folder"

    def execute(self, context):
        folder = ensure_registry_dir(context.scene.bgs_starfield_animation_tool_props.rig_registry_dir)
        try:
            os.startfile(folder)
        except Exception as exc:
            self.report({'ERROR'}, f"Could not open folder: {exc}")
            return {'CANCELLED'}
        return {'FINISHED'}


class BGS_STARFIELD_OT_animation_mark_new_rig(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.mark_new_rig"
    bl_label = "Create New Rig"
    bl_description = "Mark active armature as a Starfield rig"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature object first")
            return {'CANCELLED'}

        props = obj.bgs_starfield_animation_rig_props
        props.is_rig = True
        if not props.rig_name:
            props.rig_name = sanitize_name(obj.name)

        self.report({'INFO'}, f"Marked '{obj.name}' as Starfield rig")
        return {'FINISHED'}


class BGS_STARFIELD_OT_animation_mark_new_clip(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.mark_new_clip"
    bl_label = "Create New AF"
    bl_description = "Mark active armature as a Starfield animation clip"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature object first")
            return {'CANCELLED'}

        tool_props = context.scene.bgs_starfield_animation_tool_props
        rig_props = obj.bgs_starfield_animation_rig_props
        anim_props = obj.bgs_starfield_animation_clip_props

        anim_props.is_animation = True
        if not anim_props.animation_name:
            anim_props.animation_name = sanitize_name(obj.name)

        if tool_props.selected_rig != 'NONE':
            anim_props.source_rig_name = tool_props.selected_rig
        elif rig_props.rig_name:
            anim_props.source_rig_name = rig_props.rig_name

        self.report({'INFO'}, f"Marked '{obj.name}' as Starfield animation clip")
        return {'FINISHED'}


class BGS_STARFIELD_OT_animation_register_rig_file(bpy.types.Operator):
    bl_idname = "scene.bgs_starfield_animation_register_rig_file"
    bl_label = "Register Rig From Selected"
    bl_description = "Register the selected armature rig so it can be selected for AF import/export"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature object first")
            return {'CANCELLED'}

        rig_props = obj.bgs_starfield_animation_rig_props
        rig_props.is_rig = True

        clean_name = sanitize_name(rig_props.rig_name) if rig_props.rig_name else sanitize_name(obj.name)
        if not clean_name or clean_name == "NONE":
            self.report({'ERROR'}, "Rig name cannot be empty")
            return {'CANCELLED'}

        rig_props.rig_name = clean_name

        tool_props = context.scene.bgs_starfield_animation_tool_props
        tool_props.selected_rig = clean_name
        self.report({'INFO'}, f"Registered selected rig: {clean_name}")
        return {'FINISHED'}
