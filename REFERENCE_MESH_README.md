# Reference Mesh Import Feature

The Starfield Blender Extension now supports two types of reference mesh functionality for rig import:

## 1. Import Reference Mesh from File

Automatically looks for and imports reference meshes when importing rig files. This provides visual guidelines for rig placement and proportions.

### How It Works:

1. **Automatic Detection**: When importing a `.rig` file, it looks for a `.fbx` file with the same name in the same directory
   - Example: `HumanMale.rig` + `HumanMale.fbx`

2. **Smart Import**: Only imports the mesh geometry from the FBX (strips out any animation or armatures)

3. **Proper Parenting**: The imported rig armature is automatically parented to the reference mesh

## 2. Use Existing Mesh as Reference

Position and scale imported rigs to match existing mesh objects already in your Blender scene.

### How It Works:

1. **Mesh Selection**: Uses the active mesh object, or the first selected mesh if multiple are selected

2. **Bone Positioning**: Offsets all rig bones by the mesh center position during creation

3. **Proper Parenting**: Parents the rig armature to the reference mesh for proper transformation

4. **No Scaling**: Maintains original rig proportions (scaling can break bone relationships)

### Usage:

1. Select a mesh object in your scene
2. Import a `.rig` file through the Starfield Animation panel
3. Check "Use Selected Mesh as Reference" in the file browser
4. The rig will be automatically positioned and scaled to match your mesh

## Benefits

- **Visual Reference**: See the character's actual proportions and default pose
- **Rig Validation**: Verify that bones are positioned correctly relative to the mesh
- **Animation Context**: Better visual context when working with animations
- **Professional Workflow**: Matches the approach used by the reference sf_animation_io addon
- **Flexible Options**: Choose between importing reference meshes or using existing scene meshes