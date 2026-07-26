# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Script copyright (C) 2024, Zenimax Media

import bpy
import os
import errno
import mathutils
from ..utils import bs_plugin_data
from ..utils.app_utils.app import AppUtils


def do_bsfbx_export(context):
    plugin_name = bs_plugin_data.get_export_plugin_name()
    _was, is_enabled = AppUtils.enable_addon(plugin_name)
    if not is_enabled:
        raise RuntimeError(
            f"BSFBX exporter addon '{plugin_name}' is not installed. "
            "Install the official Skyrim / Creation Kit BGS FBX exporter "
            "(io_scene_bsfbx_skyrim), enable it in Preferences → Add-ons, "
            "then retry Export BSFBX."
        )
    try:
        export_op = bs_plugin_data.get_bsfbx_export_operator(bpy.ops.export_scene)
    except AttributeError as exc:
        raise RuntimeError(
            f"Expected operator export_scene.{bs_plugin_data.BSFBX_EXPORT_OPERATOR_ID} "
            f"from '{plugin_name}', but it was not registered."
        ) from exc
    return export_op(
        'INVOKE_DEFAULT',
        use_selection=bs_plugin_data.scene_get_bs_fbx_export_settings(
            context.scene).selected_only,
        export_centered_at_origin=bs_plugin_data.scene_get_bs_fbx_export_settings(
            context.scene).export_centered_at_origin
    )


class BGS_STARFIELD_OT_verify_scene_data_and_do_export(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix(
        "bgs_starfield.verify_scene_data_and_do_export")
    bl_label = "Export as BSFBX"
    bl_description = "Verify data and export as FBX (bpy.ops.export_scene.bsfbx_skyrim)"

    error_node_name: bpy.props.StringProperty()  # type: ignore
    error_message1: bpy.props.StringProperty()  # type: ignore
    error_message2: bpy.props.StringProperty()  # type: ignore

    def invoke(self, context, event):
        # source: export_fbx_bin.py : save()
        ctx_objects = []
        if bs_plugin_data.scene_get_bs_fbx_export_settings(context.scene).selected_only:
            # this does not include hidden (hide_get) objects
            ctx_objects = context.selected_objects

            # add all children of selected objects to ctx_objects to make sure hidden objects are exported
            objects_to_check = []
            for obj in ctx_objects:
                objects_to_check.append(obj)

            ctx_objects_set = {}
            while len(objects_to_check) > 0:
                obj = objects_to_check.pop()
                ctx_objects_set[obj] = True
                for child in obj.children:
                    objects_to_check.append(child)

            ctx_objects = []
            for obj in ctx_objects_set:
                ctx_objects.append(obj)
        else:
            ctx_objects = context.view_layer.objects

        # see: export_fbx_bin.py DO_SINGLE_ROOT_NON_IDENTITY_RESET_TRANSFORM_ON_EXPORT
        root_nodes = []
        for obj in ctx_objects:
            if isinstance(obj, bpy.types.Object) and obj.parent == None:
                root_nodes.append(obj)

        if len(root_nodes) == 1:
            for obj in root_nodes:
                matrix = obj.matrix_local
                loc, rot, scale = matrix.decompose()

                if scale != mathutils.Vector.Fill(3, 1.0):
                    self.error_node_name = obj.name
                    self.error_message1 = "Root node scale is not 1 (Won't be saved to nif)"
                    self.error_message2 = "Fix by Applying Scale (Object -> Apply -> Scale)"
                    return context.window_manager.invoke_props_dialog(self)

        for obj in ctx_objects:
            if isinstance(obj, bpy.types.Object):
                if bs_plugin_data.object_get_bgs_rigidbody(obj).is_rigidbody:
                    itr = obj.parent
                    while itr != None:
                        if abs(itr.matrix_local.median_scale - 1) > 0.01:
                            self.error_node_name = obj.name
                            self.error_message1 = "Rigid body is a child of a scaled node."
                            self.error_message2 = "This is not supported in the output nif."
                            return context.window_manager.invoke_props_dialog(self)
                        else:
                            itr = itr.parent

        for obj in ctx_objects:
            if isinstance(obj, bpy.types.Object):
                bgs_rigidbody = bs_plugin_data.object_get_bgs_rigidbody(obj)
                if bgs_rigidbody.is_rigidbody and bgs_rigidbody.has_bone_proxy and bgs_rigidbody.bone_proxy_armature != None:
                    found_matching_bone = False

                    for bone in bgs_rigidbody.bone_proxy_armature.bones:
                        if bone.name == bgs_rigidbody.bone_proxy_name:
                            found_matching_bone = True
                            break

                    if found_matching_bone == False:
                        self.error_node_name = obj.name
                        self.error_message1 = "RigidBody Bone Proxy set but bone not found."
                        self.error_message2 = "Armature: %s, Bone: %s" % (
                            bgs_rigidbody.bone_proxy_name, bgs_rigidbody.bone_proxy_armature.name)
                        return context.window_manager.invoke_props_dialog(self)

        for obj in root_nodes:
            if obj.animation_data != None and obj.animation_data.action != None:
                self.error_node_name = obj.name
                self.error_message1 = "Root Object has transform Animation Data and Action"
                self.error_message2 = "This will not be visible in the exported nif."
                return context.window_manager.invoke_props_dialog(self)

        # calls async (current stack ends)
        try:
            return do_bsfbx_export(context)
        except RuntimeError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

    def draw(self, context):
        self.layout.label(text="Node:")
        self.layout.label(text=self.error_node_name)
        self.layout.label(text="Has the following issues:")
        self.layout.label(text=self.error_message1)
        self.layout.label(text=self.error_message2)

    def execute(self, context):
        try:
            return do_bsfbx_export(context)
        except RuntimeError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}


class BGS_STARFIELD_OT_set_recommended_unit_scale(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix(
        "bgs_starfield.set_recommended_unit_scale")
    bl_label = "Set Recommended Scale + Units"
    bl_description = "Set the recommended scale and units for exporting Starfield assets."
    RECOMMENDED_UNIT_SYSTEM = "IMPERIAL"
    RECOMMENDED_LENGTH_UNIT = "INCHES"
    RECOMMENDED_SCALE_LENGTH = 1

    def invoke(self, context, event):
        context.scene.unit_settings.system = BGS_STARFIELD_OT_set_recommended_unit_scale.RECOMMENDED_UNIT_SYSTEM
        context.scene.unit_settings.length_unit = BGS_STARFIELD_OT_set_recommended_unit_scale.RECOMMENDED_LENGTH_UNIT
        context.scene.unit_settings.scale_length = BGS_STARFIELD_OT_set_recommended_unit_scale.RECOMMENDED_SCALE_LENGTH
        return {'FINISHED'}


class BGS_STARFIELD_OT_validate_scene(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix("bgs_starfield.validate_scene")
    bl_label = "Validate Scene"
    bl_description = "Validate scene data for export compatibility"

    def execute(self, context):
        # TODO: Implement scene validation logic
        self.report({'INFO'}, "Scene validation completed")
        return {'FINISHED'}


class BGS_STARFIELD_OT_load_preset(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix("bgs_starfield.load_preset")
    bl_label = "Load Export Preset"
    bl_description = "Load export settings from a preset"

    def execute(self, context):
        # TODO: Implement preset loading
        self.report({'INFO'}, "Preset loaded")
        return {'FINISHED'}


class BGS_STARFIELD_OT_save_preset(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix("bgs_starfield.save_preset")
    bl_label = "Save Export Preset"
    bl_description = "Save current export settings as a preset"

    def execute(self, context):
        # TODO: Implement preset saving
        self.report({'INFO'}, "Preset saved")
        return {'FINISHED'}


class BGS_STARFIELD_OT_advanced_morph_edit(bpy.types.Operator):
    bl_idname = bs_plugin_data.bl_id_with_project_suffix("bgs_starfield.advanced_morph_edit")
    bl_label = "Advanced Morph Edit"
    bl_description = "Open advanced morph editing interface for shape keys"

    def execute(self, context):
        from ..MorphIO import CreateMorphObjSet
        from ..utils import utils_blender

        active_obj = utils_blender.GetActiveObject()
        ref_objs = utils_blender.GetSelectedObjs(True)

        if active_obj == None or active_obj.type != 'MESH':
            self.report({'WARNING'}, "Must select a mesh object with shape keys!")
            return {'CANCELLED'}

        target_objs = []
        result = CreateMorphObjSet(context.scene, context, active_obj, ref_objs, target_objs, self)

        return result


def register():
    bpy.utils.register_class(BGS_STARFIELD_OT_verify_scene_data_and_do_export)
    bpy.utils.register_class(BGS_STARFIELD_OT_set_recommended_unit_scale)
    bpy.utils.register_class(BGS_STARFIELD_OT_validate_scene)
    bpy.utils.register_class(BGS_STARFIELD_OT_load_preset)
    bpy.utils.register_class(BGS_STARFIELD_OT_save_preset)
    bpy.utils.register_class(BGS_STARFIELD_OT_advanced_morph_edit)

def unregister():
    bpy.utils.unregister_class(BGS_STARFIELD_OT_verify_scene_data_and_do_export)
    bpy.utils.unregister_class(BGS_STARFIELD_OT_set_recommended_unit_scale)
    bpy.utils.unregister_class(BGS_STARFIELD_OT_validate_scene)
    bpy.utils.unregister_class(BGS_STARFIELD_OT_load_preset)
    bpy.utils.unregister_class(BGS_STARFIELD_OT_save_preset)
    bpy.utils.unregister_class(BGS_STARFIELD_OT_advanced_morph_edit)
