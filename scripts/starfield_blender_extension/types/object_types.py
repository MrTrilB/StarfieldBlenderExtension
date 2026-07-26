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
from ..utils import bs_plugin_data
from ..utils import bgs


class BGS_STARFIELD_PG_node_properties(bpy.types.PropertyGroup):
    sgo_keep: bpy.props.BoolProperty(
        name="Keep Object",
        description="If enabled, this object will be kept in the export even if not a mesh.",
        default=False
    )  # type: ignore
    sgo_keep_type: bpy.props.EnumProperty(
        name="Keep Type",
        description="Type of keep operation for Starfield export.",
        items=[
            ("sgoKeep", "sgoKeep", "Standard keep for Starfield export."),
        ],
        default="sgoKeep"
    )  # type: ignore
    has_parent_attachment: bpy.props.BoolProperty(
        name="Connection Point",
        description="Enable to mark this object as a connection point for Starfield (e.g., weapon, shield, etc.)",
        default=False
    )  # type: ignore
    parent_attachment_name: bpy.props.EnumProperty(
        name="Connection Point Type",
        description="Select the type of connection point.",
        items=[
            ("Quiver", "Quiver", "Quiver attachment point"),
            ("Shield", "Shield", "Shield attachment point"),
            ("WeaponAxe", "WeaponAxe", "Axe attachment point"),
            ("WeaponBack", "WeaponBack", "Back weapon attachment point"),
            ("WeaponBow", "WeaponBow", "Bow attachment point"),
            ("WeaponDagger", "WeaponDagger", "Dagger attachment point"),
            ("WeaponMace", "WeaponMace", "Mace attachment point"),
            ("WeaponSword", "WeaponSword", "Sword attachment point"),
            ("CUSTOM", "Custom", "Custom attachment point name")
        ],
        default="Quiver"
    )  # type: ignore
    custom_parent_attachment: bpy.props.StringProperty(
        name="Custom Connection Point Name",
        description="Specify a custom connection point name.",
        default=""
    )  # type: ignore
    # Skyrim io_scene_bsfbx_skyrim reads these on Object.bgs_node. Starfield's PG
    # originally omitted them, which raised AttributeError on Export BSFBX.
    is_inventory_marker: bpy.props.BoolProperty(
        name="Inventory Marker",
        description="Mark this object as an inventory marker for BSFBX export.",
        default=False
    )  # type: ignore
    has_behaviour_graph: bpy.props.BoolProperty(
        name="Behaviour Graph",
        description="Attach a behaviour graph path for BSFBX export.",
        default=False
    )  # type: ignore
    behaviour_graph_path: bpy.props.StringProperty(
        name="Behaviour Graph Path",
        description="Path to the behaviour graph asset.",
        default=""
    )  # type: ignore
    behaviour_graph_controls_base_skeleton: bpy.props.BoolProperty(
        name="Behaviour Graph Controls Base Skeleton",
        description="Whether the behaviour graph controls the base skeleton.",
        default=False
    )  # type: ignore


partition_values = {
    "Custom": -1,
    "Head": 30,
    "Hair": 31,
    "Body": 32,
    "Hands": 33,
    "Forearms": 34,
    "Amulet": 35,
    "Ring": 36,
    "Feet": 37,
    "Calves": 38,
    "Shield": 39,
    "Tail": 40,
    "LongHair": 41,
    "Circlet": 42,
}


def partition_value_enum_items():
    items = []
    for k, v in partition_values.items():
        items.append((str(v), "%s (%d)" % (k, v), ''))
    return items


class BGS_STARFIELD_PG_vertex_group_partition(bpy.types.PropertyGroup):
    vertex_group_index: bpy.props.IntProperty(default=0)  # type: ignore
    partition_value: bpy.props.EnumProperty(
        items=partition_value_enum_items(),
        default=bgs.items_index_of(partition_value_enum_items(), "Head (30)"),
        name="Partition Value"
    )  # type: ignore
    custom_partition_value: bpy.props.IntProperty(default=0)  # type: ignore
    is_1st_person: bpy.props.BoolProperty(default=False)  # type: ignore


class BGS_STARFIELD_PG_object_vertex_group_partitions(bpy.types.PropertyGroup):
    partitions: bpy.props.CollectionProperty(
        type=BGS_STARFIELD_PG_vertex_group_partition
    )  # type: ignore


def late_register():
    bs_plugin_data.object_assign_bgs_object_data(
        bpy.props.PointerProperty(type=BGS_STARFIELD_PG_node_properties))

    # as of 3.6.5, can't add properties to vertex groups (it is a bpy_struct, not an ID)
    # adding vertex group data to the parent node
    bs_plugin_data.object_assign_bgs_vertex_group_partitions(
        bpy.props.PointerProperty(type=BGS_STARFIELD_PG_object_vertex_group_partitions))


def register():
    bpy.utils.register_class(BGS_STARFIELD_PG_node_properties)
    bpy.utils.register_class(BGS_STARFIELD_PG_vertex_group_partition)
    bpy.utils.register_class(BGS_STARFIELD_PG_object_vertex_group_partitions)
    late_register()

def unregister():
    bpy.utils.unregister_class(BGS_STARFIELD_PG_node_properties)
    bpy.utils.unregister_class(BGS_STARFIELD_PG_vertex_group_partition)
    bpy.utils.unregister_class(BGS_STARFIELD_PG_object_vertex_group_partitions)
