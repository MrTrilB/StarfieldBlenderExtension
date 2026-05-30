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

import math

import bpy

from pprint import pprint

from ..utils import bgs
from ..utils import bs_plugin_data


class BGS_STARFIELD_PT_vertex_groups(bpy.types.Panel):
    bl_label = "BGS"
    bl_idname = bs_plugin_data.bl_id_with_project_suffix(
        "BGS_STARFIELD_PT_vertex_groups")
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_category = 'BGS Starfield'

    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE',
                      'BLENDER_WORKBENCH', 'BLENDER_WORKBENCH_NEXT'}

    blender_vertex_group_draw = None

    def draw(self, context):
        if BGS_STARFIELD_PT_vertex_groups.blender_vertex_group_draw is not None:
            BGS_STARFIELD_PT_vertex_groups.blender_vertex_group_draw(self, context)

        layout = self.layout
        ob = context.active_object
        group = ob.vertex_groups.active
        if ob != None and group != None:
            layout.context_pointer_set("obj", ob)
            layout.context_pointer_set("vertex_group", group)

            bgs_vertex_group_partition = None
            for i in range(
                    0, len(bs_plugin_data.object_get_bgs_vertex_group_partitions(ob).partitions)):
                itr_vertex_group_partition = bs_plugin_data.object_get_bgs_vertex_group_partitions(
                    ob).partitions[i]
                if itr_vertex_group_partition.vertex_group_index == group.index:
                    bgs_vertex_group_partition = itr_vertex_group_partition
                    break

            if bgs_vertex_group_partition == None:
                layout.operator(bs_plugin_data.bl_id_with_project_suffix(
                    "bgs_starfield.add_vertex_group_partition"), icon='ADD')
            else:
                layout.prop(bgs_vertex_group_partition,
                            "partition_value", text="BGS Partition Value (W)")
                if int(bgs_vertex_group_partition.partition_value) == bgs.custom_enum_value():
                    layout.prop(bgs_vertex_group_partition,
                                "custom_partition_value", text="Custom Partition Value")
                layout.prop(bgs_vertex_group_partition,
                            "is_1st_person", text="1st Person")
                layout.operator(bs_plugin_data.bl_id_with_project_suffix(
                    "bgs_starfield.remove_vertex_group_partition"), icon='REMOVE')


def register_custom():
    try:
        BGS_STARFIELD_PT_vertex_groups.blender_vertex_group_draw = bpy.types.DATA_PT_vertex_groups.draw
        bpy.types.DATA_PT_vertex_groups.draw = BGS_STARFIELD_PT_vertex_groups.draw

    except BaseException as e:
        print("vertex_group register_custom failed(%s)" % (e))


def unregister_custom():
    try:
        bpy.types.DATA_PT_vertex_groups.draw = BGS_STARFIELD_PT_vertex_groups.blender_vertex_group_draw
    except BaseException as e:
        print("vertex_groups unregister_custom failed(%s)" % (e))


def register():
    bpy.utils.register_class(BGS_STARFIELD_PT_vertex_groups)
    register_custom()

def unregister():
    bpy.utils.unregister_class(BGS_STARFIELD_PT_vertex_groups)
    unregister_custom()
