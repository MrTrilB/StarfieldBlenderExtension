import bpy
import sys
import os

# Add the addon path
addon_path = r"C:\Users\Anthony\OneDrive\Modding\StarfieldBlenderExtension\temp_check_dist\starfield_blender_extension"
if addon_path not in sys.path:
    sys.path.append(addon_path)

# Enable the addon
bpy.ops.preferences.addon_enable(module="starfield_blender_extension")

# Import a rig file
rig_path = r"C:\Users\Anthony\OneDrive\Modding\StarfieldBlenderExtension\test_rigs\Starfield.rig"
bpy.ops.bgs_starfield.import_rig(filepath=rig_path)

print("Rig import completed")

# Check the armature
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':
        print(f"Armature: {obj.name}")
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in obj.data.edit_bones:
            print(f"Bone: {bone.name}, Position: {bone.head}")
        break