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


def bl_id_with_project_suffix(bl_id):
    return bl_id + "_starfield"


# Bethesda never shipped a public Starfield BSFBX Blender addon. Collider /
# rigidbody FBX for AssetWatcher comes from the Creation Kit / Skyrim Art Tools
# exporter (`io_scene_bsfbx_skyrim` → `bpy.ops.export_scene.bsfbx_skyrim`).
BSFBX_EXPORT_PLUGIN_NAME = "io_scene_bsfbx_skyrim"
BSFBX_EXPORT_OPERATOR_ID = "bsfbx_skyrim"


def get_export_plugin_name():
    return BSFBX_EXPORT_PLUGIN_NAME


def get_bsfbx_export_operator(module):
    return getattr(module, BSFBX_EXPORT_OPERATOR_ID)


def get_module_with_project_suffix(module, bl_id):
    return getattr(module, bl_id_with_project_suffix(bl_id))

# Object.bgs_node


def object_assign_bgs_object_data(pointer_prop):
    bpy.types.Object.bgs_node = pointer_prop


def object_get_bgs_object_data(obj):
    rtv = None
    try:
        rtv = obj.bgs_node
    finally:
        pass
    return rtv

# Object.bgs_vertex_group_partitions


def object_assign_bgs_vertex_group_partitions(pointer_prop):
    bpy.types.Object.bgs_vertex_group_partitions = pointer_prop


def object_get_bgs_vertex_group_partitions(obj):
    rtv = None
    try:
        rtv = obj.bgs_vertex_group_partitions
    finally:
        pass
    return rtv

# Material.bgs_props


def material_assign_bgs_props(pointer_prop):
    bpy.types.Material.bgs_props = pointer_prop


def material_get_bgs_props(material):
    rtv = None
    try:
        rtv = material.bgs_props
    finally:
        pass
    return rtv

# Object.bgs_collider


def object_assign_bgs_collider(pointer_prop):
    bpy.types.Object.bgs_collider = pointer_prop


def object_get_bgs_collider(obj):
    rtv = None
    try:
        rtv = obj.bgs_collider
    finally:
        pass
    return rtv

# Object.bgs_rigidbody


def object_assign_bgs_rigidbody(pointer_prop):
    bpy.types.Object.bgs_rigidbody = pointer_prop


def object_get_bgs_rigidbody(obj):
    rtv = None
    try:
        rtv = obj.bgs_rigidbody
    finally:
        pass
    return rtv

# Scene.animation_sequences


def scene_assign_animation_sequences(collection_prop):
    bpy.types.Scene.animation_sequences = collection_prop


def scene_get_animation_sequences(scene):
    rtv = None
    try:
        rtv = scene.animation_sequences
    finally:
        pass
    return rtv

# Scene.bs-fbx_export_settings


def scene_assign_bs_fbx_export_settings(pointer_prop):
    bpy.types.Scene.bs_fbx_export_settings = pointer_prop


def scene_get_bs_fbx_export_settings(scene):
    rtv = None
    try:
        rtv = scene.bs_fbx_export_settings
    finally:
        pass
    return rtv

# scene.export_config


def scene_assign_export_config(enum_prop):
    bpy.types.Scene.export_config = enum_prop


def scene_export_config_prop_name():
    return "export_config"


def scene_get_export_config(scene):
    rtv = None
    try:
        rtv = scene.export_config
    finally:
        pass
    return rtv

# scene.bgs_starfield_panel_tab


def scene_assign_bgs_starfield_panel_tab(enum_prop):
    bpy.types.Scene.bgs_starfield_panel_tab_starfield = enum_prop


def scene_bgs_starfield_panel_tab_prop_name():
    return "bgs_starfield_panel_tab_starfield"


def scene_get_bgs_starfield_panel_tab(scene):
    rtv = None
    try:
        rtv = scene.bgs_starfield_panel_tab_starfield
    finally:
        pass
    return rtv

# armature.bgs_armature_props


def armature_assign_bgs_props(pointer_prop):
    bpy.types.Armature.bgs_armature_props = pointer_prop


def armature_get_bgs_props(armature):
    rtv = None
    try:
        rtv = armature.bgs_armature_props
    finally:
        pass
    return rtv
