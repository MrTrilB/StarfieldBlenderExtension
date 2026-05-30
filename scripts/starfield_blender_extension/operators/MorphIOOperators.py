import bpy
import os

from .. import MorphIO

from ..utils import utils_common as utils, utils_blender	
from ..utils import bs_plugin_data

class ImportCustomMorph(bpy.types.Operator):
	bl_idname = "import_scene.custom_morph"
	bl_label = "Import Custom Morph"
	
	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filename: bpy.props.StringProperty(default='morph.dat')
	filter_glob: bpy.props.StringProperty(default="*.dat", options={'HIDDEN'})

	def assets_folder_update(self, context):
		context.scene.assets_folder = self.assets_folder

	assets_folder: bpy.props.StringProperty(subtype="FILE_PATH", update=assets_folder_update)

	use_colors: bpy.props.BoolProperty(
		name="Import colors",
		description="Import colors as attributes.",
		default=False
	)

	base_vertex_bytecolor: bpy.props.IntProperty(
		name="Base Vertex Byte Color",
		description="Base vertex byte color for morph data.",
		default=191,
		min=0,
		max=255
	)

	use_normals: bpy.props.BoolProperty(
		name="Import normals",
		description="Import normals as attributes.",
		default=False
	)

	debug_delta_normal: bpy.props.BoolProperty(
		name="Debug Delta Normals",
		description="Debug option. DO NOT USE.",
		default=False
	)
	debug_delta_tangent: bpy.props.BoolProperty(
		name="Debug Delta Tangents",
		description="Debug option. DO NOT USE.",
		default=False
	)

	def draw(self, context):
		layout = self.layout
		layout.label(text="Assets Folder:")
		layout.prop(self, "assets_folder", text="")
		
		layout.prop(self, "use_colors")
		box = layout.box()
		box.prop(self, "base_vertex_bytecolor")
		if self.use_colors:
			box.enabled = True
		else:
			box.enabled = False

		layout.prop(self, "use_normals")

		layout.label(text="Debug Options:")
		layout.prop(self, "debug_delta_normal")
		layout.prop(self, "debug_delta_tangent")
	
	def execute(self, context):
		try:
			return MorphIO.ImportMorphFromNumpy(self.filepath, self, self.debug_delta_normal, use_colors=self.use_colors, use_normals=self.use_normals, base_vertex_bytecolor=self.base_vertex_bytecolor)
		except Exception as e:
			self.report({'ERROR'}, f"Morph import failed: {e}")
			return {'CANCELLED'}

	def invoke(self, context, event):
		self.assets_folder = context.scene.assets_folder
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

class ExportCustomMorph(bpy.types.Operator):
	bl_idname = "export_scene.custom_morph"
	bl_label = "Export Custom Morph"
	bl_description = "Export morph target data in Starfield .dat format for shape key animations"
	
	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filename: bpy.props.StringProperty(default='morph.dat')
	filter_glob: bpy.props.StringProperty(default="*.dat", options={'HIDDEN'})

	use_world_origin = True

	use_secondary_uv: bpy.props.BoolProperty(
		name="Use Secondary UV",
		description="Use the topmost non-active UV map (if possible) as secondary UV",
		default=False
	)

	snapping_enabled: bpy.props.BoolProperty(
		name="Snap Morph Data To Selected",
		description="Snapping morph data of connecting vertices to closest verts from selected objects.",
		default=False,
	)

	snap_lerp_coeff: bpy.props.FloatProperty(
		name="Snap Lerp Coefficient",
		description="Lerp coefficient for snapping morph data of connecting vertices to closest verts from selected objects.",
		default=1.0,
		min=0.0,
		max=1.0,
		precision=4,
	)

	snapping_range: bpy.props.FloatProperty(
		name="Snapping Range",
		description="Verts from Active Object will copy morph data from verts from selected objects within Snapping Range.",
		default=0.005,
		min=0.0,
		precision=4,
	)

	snap_delta_positions: bpy.props.BoolProperty(
		name="Snap Delta Positions",
		description="Snapping morph delta positions of connecting vertices to closest verts from selected objects.",
		default=False,
	)

	snap_lerp_coeff_delta_positions: bpy.props.FloatProperty(
		name="Snap Lerp Coefficient Delta Positions",
		description="Lerp coefficient for snapping morph delta positions of connecting vertices to closest verts from selected objects.",
		default=1.0,
		min=0.0,
		max=1.0,
		precision=4,
	)

	def draw(self, context):
		layout = self.layout
		layout.prop(self, "use_secondary_uv")

		report = utils_blender.export_report(report_uv_layers=True)
		box = layout.box()
		if 'first_uv' in report and 'second_uv' in report:
			if self.use_secondary_uv:
				box.label(text=f"First UV Map: {report['first_uv'].name}")
				box.label(text=f"Second UV Map: {report['second_uv'].name}")
			else:
				box.label(text=f"UV Map: {report['first_uv'].name}")
		else:
			box.label(text="UV Map: N/A")

		layout.label(text="Morph Snapping Options:")
		layout.prop(self, "snapping_enabled")
		box = layout.box()
		box.prop(self, "snapping_range")
		box.prop(self, "snap_lerp_coeff")
		box.prop(self, "snap_delta_positions")
		box_row = box.row()
		box_row.prop(self, "snap_lerp_coeff_delta_positions")

		box_row.enabled = False
		box.enabled = False
		if self.snapping_enabled:
			box.enabled = True
			if self.snap_delta_positions:
				box_row.enabled = True

	def execute(self, context):
		_try_import_success, _rtn_str = utils._try_import("import scipy", "Scipy not installed. Install it in Plugin Preferences Panel.", raise_exception=False)
		if not _try_import_success:
			self.report({'ERROR'}, _rtn_str)
			return {'CANCELLED'}
		# Persist any changes made in the file browser back to scene settings
		settings = bs_plugin_data.scene_get_bs_fbx_export_settings(context.scene)
		settings.morph_use_secondary_uv = self.use_secondary_uv
		settings.morph_snapping_enabled = self.snapping_enabled
		settings.morph_snapping_range = self.snapping_range
		settings.morph_snap_lerp_coeff = self.snap_lerp_coeff
		settings.morph_snap_delta_positions = self.snap_delta_positions
		settings.morph_snap_lerp_coeff_delta_positions = self.snap_lerp_coeff_delta_positions

		if self.snapping_enabled:
			rtn, _ = MorphIO.ExportMorph_alt(self, context, self.filepath, self, self.snapping_range, self.snap_delta_positions, self.snap_lerp_coeff, self.snap_lerp_coeff_delta_positions)
		else:
			rtn, _ = MorphIO.ExportMorph_alt(self, context, self.filepath, self)
		return rtn

	def invoke(self, context, event):
		self.filename = "morph.dat"

		# Sync operator properties with scene settings
		settings = bs_plugin_data.scene_get_bs_fbx_export_settings(context.scene)
		self.use_secondary_uv = settings.morph_use_secondary_uv
		self.snapping_enabled = settings.morph_snapping_enabled
		self.snapping_range = settings.morph_snapping_range
		self.snap_lerp_coeff = settings.morph_snap_lerp_coeff
		self.snap_delta_positions = settings.morph_snap_delta_positions
		self.snap_lerp_coeff_delta_positions = settings.morph_snap_lerp_coeff_delta_positions

		_obj = context.active_object
		if _obj:
			self.filename = utils.sanitize_filename(_obj.name) + '.dat'
		else:
			self.filename = "morph.dat"

		if os.path.isdir(os.path.dirname(self.filepath)):
			self.filepath = os.path.join(os.path.dirname(self.filepath),self.filename)

		# Prefer external geometry export directory then general export
		# directory. If configured, export immediately without file dialog.
		export_dir = None
		try:
			export_dir = settings.external_geometry_export_directory
		except Exception:
			export_dir = None

		if not export_dir:
			export_dir = getattr(settings, 'export_directory', '')

		if export_dir:
			export_dir = os.path.expanduser(os.path.expandvars(export_dir))
			if os.path.isdir(export_dir):
				self.filepath = os.path.join(export_dir, self.filename)
				return self.execute(context)
			else:
				pass

		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
__classes__ = [
	ImportCustomMorph,
    ExportCustomMorph,
]

def menu_func_import_morph(self, context):
	self.layout.operator(
		ImportCustomMorph.bl_idname,
		text="Starfield Morph File (.dat)",
	)

def menu_func_export_morph(self, context):
	self.layout.operator(
		ExportCustomMorph.bl_idname,
		text="Starfield Morph File (.dat)",
	)

def register():
    for cls in __classes__:
        bpy.utils.register_class(cls)
		
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_morph)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_morph)
		
def unregister():
    for cls in __classes__:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_morph)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_morph)