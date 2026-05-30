import bpy
import os
import shutil
from .utils import utils_blender
import functools
from . import version
from .utils import utils_common

class ChooseFileForPreferencesOperator(bpy.types.Operator):
    bl_idname = "object.choose_file_for_preferences"
    bl_label = "Choose File"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filename: bpy.props.StringProperty()
    directory: bpy.props.StringProperty()

    #files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    def execute(self, context):
        if self.filepath == "":
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}
        
        if os.path.exists(self.filepath) == False or os.path.isfile(self.filepath) == False:
            self.report({'ERROR'}, "Invalid file selected")
            return {'CANCELLED'}

        # Copy the file to the plugin directory
        plugin_dir = utils_blender.ThirdPartyFolderPath()
        os.makedirs(plugin_dir, exist_ok=True)
        texconv_path = os.path.join(plugin_dir, "texconv.exe")
        shutil.copy(self.filepath, texconv_path)

        preferences = utils_blender.get_preferences()
        if preferences is not None:
            preferences.texconv_path = texconv_path
        else:
            self.report({'WARNING'}, "Preferences object not found; texconv copied but path not saved.")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Choose File for Preferences")

class InstallModulesOperator(bpy.types.Operator):
    bl_idname = "object.install_modules_sgb"
    bl_label = "Install Modules"

    #files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    def execute(self, context):
        preferences = utils_blender.get_preferences()
        # Install scipy
        # Use the addon's installer helper so packages are installed into
        # Blender's user scripts/modules dir and the path is appended.
        success, msg = utils_common.ensure_package('scipy')
        preferences.scipy_installed = success
        if not success:
            self.report({'ERROR'}, f"Failed to install scipy: {msg}")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Install Modules")

class SGBPreferences(bpy.types.AddonPreferences):
    # Use the real loaded addon module name so Preferences always bind,
    # regardless of folder naming (e.g. starfield_blender_extension vs starfieldblenderextension).
    bl_idname = __package__

    starfield_data_path: bpy.props.StringProperty(
        name="Starfield Data Path",
        subtype='FILE_PATH',
        description="The absolute path to your Starfield data folder.",
        default="C:\\SteamLibrary\\steamapps\\common\\Starfield\\Data"
    )

    texconv_path: bpy.props.StringProperty(
        name="Texconv Path",
        subtype="FILE_PATH",
        default=os.path.join(utils_blender.ThirdPartyFolderPath(), "texconv.exe"),
        description="Path to texconv.exe"
    )

    scipy_installed: bpy.props.BoolProperty(
        name="Scipy",
        default=False,
        description="Whether scipy is installed"
    )

    def _check_scipy_installed(self):
        # Ensure our user modules path is visible to the import system
        try:
            modules_path = utils_common.get_modules_path()
            utils_common.append_modules_to_sys_path(modules_path)
        except Exception:
            pass

        try:
            import importlib
            importlib.invalidate_caches()
            import scipy
            self.scipy_installed = True
        except Exception:
            self.scipy_installed = False

    def draw(self, context):
        layout = self.layout

        scene = getattr(context, "scene", None)

        sublayout = layout.column(heading="Default Export Path")
        if scene is not None and hasattr(scene, "export_mesh_folder_path"):
            sublayout.enabled = True
            sublayout.prop(scene, "export_mesh_folder_path", text="")
        else:
            sublayout.enabled = False
            sublayout.label(text="Unavailable until addon scene properties are registered")

        sublayout = layout.column(heading="Starfield Data Path")
        sublayout.enabled = True
        sublayout.prop(self, "starfield_data_path", text="")

        sublayout = layout.column(heading="Texconv Path")
        sublayout.enabled = True
        sublayout.prop(self, "texconv_path", text="")
        layout.operator("object.choose_file_for_preferences")

        self._check_scipy_installed()

        row = layout.row()
        row.enabled = False
        row.label(text="Required Modules:")
        row.prop(self, "scipy_installed")

        row = layout.row()
        row.operator("object.install_modules_sgb")
        row.enabled = not all([self.scipy_installed])

        sublayout = layout.column(heading="Debug Mode")
        if scene is not None and hasattr(scene, "sgb_debug_mode"):
            sublayout.enabled = True
            sublayout.prop(scene, "sgb_debug_mode", toggle=True)
        else:
            sublayout.enabled = False
            sublayout.label(text="Unavailable until addon scene properties are registered")



def register():
    bpy.utils.register_class(SGBPreferences)
    bpy.utils.register_class(ChooseFileForPreferencesOperator)
    bpy.utils.register_class(InstallModulesOperator)

def unregister():
    bpy.utils.unregister_class(SGBPreferences)
    bpy.utils.unregister_class(ChooseFileForPreferencesOperator)
    bpy.utils.unregister_class(InstallModulesOperator)