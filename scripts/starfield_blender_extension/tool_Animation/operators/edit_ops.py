import bpy
import math
import mathutils


class BGS_STARFIELD_OT_animation_duplicate_action(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.duplicate_action"
    bl_label = "Duplicate Action"
    bl_description = "Duplicate active action so edits are non-destructive"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature with animation")
            return {'CANCELLED'}

        if not obj.animation_data or not obj.animation_data.action:
            self.report({'ERROR'}, "Active armature has no action to duplicate")
            return {'CANCELLED'}

        source_action = obj.animation_data.action
        duplicated_action = source_action.copy()
        duplicated_action.name = f"{source_action.name}_edit"
        obj.animation_data.action = duplicated_action

        self.report({'INFO'}, f"Created editable action copy: {duplicated_action.name}")
        return {'FINISHED'}


class BGS_STARFIELD_OT_animation_apply_action_edits(bpy.types.Operator):
    bl_idname = "bgs_starfield_animation.apply_action_edits"
    bl_label = "Apply Animation Edits"
    bl_description = "Apply timing/root-motion edits to the active action"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature with animation")
            return {'CANCELLED'}

        if not obj.animation_data or not obj.animation_data.action:
            self.report({'ERROR'}, "Active armature has no action to edit")
            return {'CANCELLED'}

        action = obj.animation_data.action
        tool_props = context.scene.bgs_starfield_animation_tool_props

        frame_offset = int(tool_props.edit_frame_offset)
        time_scale = float(tool_props.edit_time_scale)
        root_offset = mathutils.Vector(tool_props.edit_root_motion_offset)

        if time_scale <= 0.0:
            self.report({'ERROR'}, "Time Scale must be greater than 0")
            return {'CANCELLED'}

        changed_keyframes = 0

        # Timing edits (scale then offset frames).
        if abs(time_scale - 1.0) > 1e-8 or frame_offset != 0:
            for fcurve in action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.co.x = (keyframe.co.x * time_scale) + frame_offset
                    keyframe.handle_left.x = (keyframe.handle_left.x * time_scale) + frame_offset
                    keyframe.handle_right.x = (keyframe.handle_right.x * time_scale) + frame_offset
                    changed_keyframes += 1
                fcurve.update()

        # Root motion offset edits.
        if root_offset.length > 0.0:
            root_bone_names = [bone.name for bone in obj.data.bones if bone.parent is None]
            for root_name in root_bone_names:
                data_path = f'pose.bones["{root_name}"].location'
                for axis_index, axis_offset in enumerate(root_offset):
                    if abs(axis_offset) < 1e-12:
                        continue

                    fcurve = action.fcurves.find(data_path, index=axis_index)
                    if not fcurve:
                        continue

                    for keyframe in fcurve.keyframe_points:
                        keyframe.co.y += axis_offset
                        keyframe.handle_left.y += axis_offset
                        keyframe.handle_right.y += axis_offset
                        changed_keyframes += 1
                    fcurve.update()

        if changed_keyframes == 0:
            self.report({'WARNING'}, "No keyframes changed. Check edit values and selected action.")
            return {'CANCELLED'}

        if tool_props.edit_set_scene_range:
            min_frame = None
            max_frame = None
            for fcurve in action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    frame = keyframe.co.x
                    min_frame = frame if min_frame is None else min(min_frame, frame)
                    max_frame = frame if max_frame is None else max(max_frame, frame)

            if min_frame is not None and max_frame is not None:
                context.scene.frame_start = int(math.floor(min_frame))
                context.scene.frame_end = int(math.ceil(max_frame))

        self.report({'INFO'}, f"Applied edits to {changed_keyframes} keyframes in '{action.name}'")
        return {'FINISHED'}
