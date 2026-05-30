import bpy


class VIEW3D_PT_bgs_starfield_animation_tools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_bgs_starfield_animation_tools"
    bl_label = "BGS Starfield Animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BGS Starfield Animation'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Rig + AF workflow tools")


class VIEW3D_PT_bgs_starfield_animation_setup(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_bgs_starfield_animation_setup"
    bl_label = "Setup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BGS Starfield Animation'
    bl_parent_id = "VIEW3D_PT_bgs_starfield_animation_tools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.bgs_starfield_animation_tool_props

        box = layout.box()
        box.label(text="Registry", icon='FILE_FOLDER')
        box.prop(props, "rig_registry_dir")
        row = box.row(align=True)
        row.operator("bgs_starfield_animation.select_registry_dir", icon='FILEBROWSER')
        row.operator("bgs_starfield_animation.open_registry_dir", icon='FILE_FOLDER')

        box = layout.box()
        box.label(text="Rig Setup", icon='ARMATURE_DATA')
        row = box.row(align=True)
        row.operator("bgs_starfield_animation.mark_new_rig", icon='PLUS')
        row.operator("import_scene.bgs_starfield_rig", icon='IMPORT')
        row = box.row(align=True)
        row.operator("scene.bgs_starfield_animation_register_rig_file", icon='ADD')
        box.prop(props, "selected_rig")

        box = layout.box()
        box.label(text="Animation Setup", icon='ANIM')
        row = box.row(align=True)
        row.operator("bgs_starfield_animation.mark_new_clip", icon='PLUS')
        row.operator("import_scene.bgs_starfield_af", icon='IMPORT')
        box.prop(props, "import_af_mode")
        box.prop(props, "set_frame_end")


class VIEW3D_PT_bgs_starfield_animation_rig(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_bgs_starfield_animation_rig"
    bl_label = "Rig"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BGS Starfield Animation'
    bl_parent_id = "VIEW3D_PT_bgs_starfield_animation_tools"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj or obj.type != 'ARMATURE':
            layout.label(text="Select an armature", icon='INFO')
            return

        props = obj.bgs_starfield_animation_rig_props
        layout.prop(props, "is_rig")
        layout.prop(props, "rig_name")
        layout.prop(props, "rig_precision")

        layout.operator("export_scene.bgs_starfield_rig", icon='EXPORT')


class VIEW3D_PT_bgs_starfield_animation_clip(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_bgs_starfield_animation_clip"
    bl_label = "Animation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BGS Starfield Animation'
    bl_parent_id = "VIEW3D_PT_bgs_starfield_animation_tools"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        scene_props = context.scene.bgs_starfield_animation_tool_props

        if not obj or obj.type != 'ARMATURE':
            layout.label(text="Select an animation armature", icon='INFO')
            return

        props = obj.bgs_starfield_animation_clip_props
        layout.prop(props, "is_animation")
        layout.prop(props, "animation_name")
        layout.prop(props, "source_rig_name")

        layout.prop(scene_props, "selected_rig")
        layout.operator("export_scene.bgs_starfield_af", icon='EXPORT')

        action = obj.animation_data.action if obj.animation_data else None

        edit_box = layout.box()
        edit_box.label(text="Edit Animation", icon='GREASEPENCIL')

        if not action:
            edit_box.label(text="No active action on this armature", icon='INFO')
            return

        edit_box.label(text=f"Action: {action.name}")
        edit_box.operator("bgs_starfield_animation.duplicate_action", icon='DUPLICATE')

        edit_box.prop(scene_props, "edit_time_scale")
        edit_box.prop(scene_props, "edit_frame_offset")
        edit_box.prop(scene_props, "edit_root_motion_offset")
        edit_box.prop(scene_props, "edit_set_scene_range")

        edit_box.operator("bgs_starfield_animation.apply_action_edits", icon='CHECKMARK')
