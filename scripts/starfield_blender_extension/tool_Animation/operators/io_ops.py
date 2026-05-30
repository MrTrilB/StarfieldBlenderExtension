import bpy
import os
import math
import mathutils

from ..utils.registry import sanitize_name, get_registered_rig_path
from ..utils.calumi_adapter import get_adapter


# Coordinate system correction (from sf_animation_io)
bone_axis_correction_full = mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z')
bone_axis_correction_inv = mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z')


def apply_bone_axis_correction(matrix):
    """Apply axis correction like sf_animation_io does."""
    return bone_axis_correction_full @ matrix @ bone_axis_correction_inv


def create_bone_hierarchy(armature_data, skel_rig, parent_bone_name=None, mesh_offset=mathutils.Vector((0, 0, 0)), bone_position_overrides=None):
    """Recursively create bones with proper matrix transformations like sf_animation_io."""
    if bone_position_overrides is None:
        bone_position_overrides = {}

    edit_bones = armature_data.edit_bones
    bones_created = {}

    # Get bones for this level
    if parent_bone_name is None:
        # Root bones
        current_bones = [b for b in skel_rig.bones if b.parent_index == -1 or b.parent_name is None]
    else:
        # Child bones
        current_bones = [b for b in skel_rig.bones if b.parent_name == parent_bone_name]

    for bone in current_bones:
        # Store original bone name for override lookup before any modifications
        original_bone_name = bone.bone_name

        # Ensure bone has a valid name
        if not bone.bone_name or bone.bone_name.strip() == "":
            bone.bone_name = f"Bone_{bone.index}"

        # Ensure unique name
        base_name = bone.bone_name
        counter = 1
        while bone.bone_name in edit_bones:
            bone.bone_name = f"{base_name}_{counter}"
            counter += 1

        edit_bone = edit_bones.new(bone.bone_name)
        bones_created[bone.bone_name] = edit_bone

        print(f"Processing bone '{bone.bone_name}' (original: '{original_bone_name}'), checking overrides: {original_bone_name in bone_position_overrides}")

        using_override_position = original_bone_name in bone_position_overrides

        # Determine bone position
        if using_override_position:
            # Use specific override position from matching empty
            bone_pos = bone_position_overrides[original_bone_name]
            print(f"Using override position for bone '{bone.bone_name}' (original: '{original_bone_name}'): {bone_pos}")
        elif bone.translation and len(bone.translation) == 3:
            # Apply mesh offset to position bones relative to the mesh
            bone_pos = mathutils.Vector(bone.translation) + mesh_offset
            print(f"Using rig position for bone '{bone.bone_name}': {bone.translation} + offset {mesh_offset} = {bone_pos}")
        else:
            # Use mesh offset as fallback
            bone_pos = mesh_offset
            print(f"Using fallback position for bone '{bone.bone_name}': {bone_pos}")

        tra = mathutils.Matrix.Translation(bone_pos)

        # Set up rotation matrix
        if hasattr(bone, 'rotation') and bone.rotation:
            # Assuming rotation is stored as (x, y, z, w) quaternion
            if len(bone.rotation) == 4:
                rot_quat = mathutils.Quaternion(bone.rotation)
                rot = rot_quat.to_matrix().to_4x4()
            else:
                rot = mathutils.Matrix.Rotation(0, 4, 'X')  # Identity rotation
        else:
            rot = mathutils.Matrix.Rotation(0, 4, 'X')  # Identity rotation

        scale = mathutils.Matrix.Scale(1.000, 4, [1.0, 1.0, 1.0])

        # Combine transformations: translation @ rotation @ scale
        edit_bone.matrix = tra @ rot @ scale

        # Set bone properties
        edit_bone.length = 0.07
        edit_bone.roll = 0

        # Set parent
        if parent_bone_name and parent_bone_name in edit_bones:
            edit_bone.parent = edit_bones[parent_bone_name]
            # Only compose with parent matrix for rig-local positions.
            # Override positions are already absolute in armature space.
            if not using_override_position:
                edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

        print(f"Created bone '{bone.bone_name}' at position: {bone_pos}")

        # Recursively create children
        create_bone_hierarchy(armature_data, skel_rig, bone.bone_name, mesh_offset, bone_position_overrides)

    return bones_created


def ensure_armature_has_rig_bones(context, adapter, armature_obj, rig_path):
    """Populate an armature with bones from the selected rig when empty."""
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return False

    if len(armature_obj.data.bones) > 0:
        return True

    rig_data = adapter.import_rig(rig_path) if rig_path else None
    if rig_data is None:
        print(f"Unable to auto-build armature bones for AF import. rig_path={rig_path}")
        return False

    view_layer = context.view_layer
    previous_active = view_layer.objects.active

    try:
        view_layer.objects.active = armature_obj
        armature_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        create_bone_hierarchy(
            armature_obj.data,
            rig_data["rig"],
            mesh_offset=mathutils.Vector((0, 0, 0)),
            bone_position_overrides={},
        )

        for edit_bone in armature_obj.data.edit_bones:
            corrected_matrix = apply_bone_axis_correction(edit_bone.matrix)
            corrected_matrix.translation = edit_bone.matrix.translation
            edit_bone.matrix = corrected_matrix

        bpy.ops.object.mode_set(mode='OBJECT')
        return True

    except Exception as e:
        print(f"Failed creating armature from rig for AF import: {e}")
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        return False

    finally:
        if previous_active and previous_active.name in bpy.data.objects:
            view_layer.objects.active = previous_active


def _supports_legacy_action_fcurves(action):
    return hasattr(action, "fcurves")


def _get_or_create_action_group(action, group_name):
    if not group_name or not hasattr(action, "groups"):
        return None

    group = action.groups.get(group_name)
    if group is None:
        group = action.groups.new(name=group_name)
    return group


def _get_or_create_fcurve(target, fcurve_cache, data_path, index, group_name):
    if not hasattr(target, 'fcurves') or target.fcurves is None:
        return None

    key = (data_path, index)
    if key in fcurve_cache:
        return fcurve_cache[key]

    fcurve = target.fcurves.find(data_path, index=index)
    if fcurve is None:
        fcurve = target.fcurves.new(data_path=data_path, index=index)

    if group_name:
        action_group = _get_or_create_action_group(target, group_name)
        if action_group is not None and hasattr(fcurve, "group"):
            fcurve.group = action_group

    fcurve_cache[key] = fcurve
    return fcurve


def _translation_entry_to_vector(entry):
    if "value" in entry:
        tx, ty, tz = entry["value"]
    else:
        tx = entry.get("x", 0.0)
        ty = entry.get("y", 0.0)
        tz = entry.get("z", 0.0)
    return mathutils.Vector((tx, ty, tz))


def _get_bone_rest_translation_in_parent_space(pose_bone):
    bone = pose_bone.bone
    if bone.parent:
        parent_local_inv = bone.parent.matrix_local.inverted()
        return (parent_local_inv @ bone.matrix_local).translation
    return bone.matrix_local.translation


def apply_af_animation_to_armature(
    context,
    armature_obj,
    anim_data,
    set_frame_end=True,
    keep_root_centered=True,
    compensate_object_scale=False,
):
    """Apply imported AF keyframes onto a Blender armature action."""
    scene = context.scene
    scene_payload = anim_data.get("scene", {}) if anim_data else {}
    animations = anim_data.get("animations") or scene_payload.get("animations") or []

    if not animations:
        return {
            "applied_bones": 0,
            "missing_bones": [],
            "keyframes": 0,
            "max_frame": 0,
            "animation_name": anim_data.get("name", "imported_animation"),
        }

    animation = animations[0]
    animation_name = sanitize_name(animation.get("name") or anim_data.get("name") or "imported_animation")

    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name=animation_name)
    armature_obj.animation_data.action = action

    # In Blender 5, ensure the action is in a slot for Dope Sheet visibility
    print(f"Animation data has slots: {hasattr(armature_obj.animation_data, 'slots')}")
    slot = None
    if hasattr(armature_obj.animation_data, 'slots'):
        try:
            slot = armature_obj.animation_data.slots.new(action=action)
            print(f"Created action slot for action '{action.name}': {slot}")
        except Exception as e:
            print(f"Failed to create action slot: {e}")

    fcurve_cache = {}
    use_direct_fcurves = hasattr(slot, 'fcurves') if slot else False
    print(f"Using direct fcurves: {use_direct_fcurves}, slot has fcurves: {hasattr(slot, 'fcurves') if slot else False}")

    if not use_direct_fcurves:
        print(f"Action has fcurves: {hasattr(action, 'fcurves')}, fcurves: {getattr(action, 'fcurves', 'N/A')}")

    if not use_direct_fcurves:
        print("Action.fcurves unavailable in this Blender version; using object.keyframe_insert fallback")
        # Let Blender create/manage the action slot while keying in newer animation APIs.
        # Keeping a manually assigned action here can prevent channels from materializing.
        # armature_obj.animation_data.action = None
        # try:
        #     bpy.data.actions.remove(action)
        # except Exception:
        #     pass
        # action = None

    missing_bones = []
    applied_bones = 0
    total_keyframes = 0
    inserted_channel_points = 0
    max_frame = 0

    pose_bones = armature_obj.pose.bones
    armature_bones = armature_obj.data.bones

    scale_compensation = mathutils.Vector((1.0, 1.0, 1.0))
    if compensate_object_scale:
        armature_scale = armature_obj.scale.copy()
        for axis in range(3):
            scale_value = armature_scale[axis]
            if abs(scale_value) > 1e-8:
                scale_compensation[axis] = scale_value

        if (
            abs(scale_compensation.x - 1.0) > 1e-8
            or abs(scale_compensation.y - 1.0) > 1e-8
            or abs(scale_compensation.z - 1.0) > 1e-8
        ):
            print(
                "Applying AF translation compensation for armature object scale: "
                f"{tuple(scale_compensation)}"
            )

    for block in animation.get("blocks", []):
        bone_name = block.get("bone_name", "")
        bone_index = block.get("bone_index", -1)

        pose_bone = pose_bones.get(bone_name) if bone_name else None
        if pose_bone is None and isinstance(bone_index, int) and 0 <= bone_index < len(armature_bones):
            fallback_name = armature_bones[bone_index].name
            pose_bone = pose_bones.get(fallback_name)

        if pose_bone is None:
            if bone_name:
                missing_bones.append(bone_name)
            continue

        applied_bones += 1
        pose_bone.rotation_mode = 'QUATERNION'
        safe_bone_name = pose_bone.name.replace('\\', '\\\\').replace('"', '\\"')
        rot_path = f'pose.bones["{safe_bone_name}"].rotation_quaternion'
        loc_path = f'pose.bones["{safe_bone_name}"].location'

        translation_sequence = block.get("translation_sequence", [])
        is_root_bone = pose_bone.bone.parent is None if pose_bone and pose_bone.bone else False
        root_translation_offset = None
        rest_translation = _get_bone_rest_translation_in_parent_space(pose_bone)
        treat_translation_as_absolute = False

        first_translation_entry = None
        if translation_sequence:
            first_translation_entry = min(
                translation_sequence,
                key=lambda entry: int(entry.get("frame", 0))
            )

        if keep_root_centered and is_root_bone and first_translation_entry is not None:
            if "value" in first_translation_entry:
                otx, oty, otz = first_translation_entry["value"]
            else:
                otx = first_translation_entry.get("x", 0.0)
                oty = first_translation_entry.get("y", 0.0)
                otz = first_translation_entry.get("z", 0.0)

            root_translation_offset = mathutils.Vector((otx, oty, otz))

        # AF files may encode translation either as pose delta (Blender-compatible)
        # or as absolute rest-space values (needs rest translation subtraction).
        # Detect this per-bone from the first keyframe.
        if first_translation_entry is not None and not (keep_root_centered and is_root_bone):
            first_translation = _translation_entry_to_vector(first_translation_entry)
            dist_to_zero = first_translation.length
            dist_to_rest = (first_translation - rest_translation).length
            if rest_translation.length > 1e-6 and (dist_to_rest + 1e-6) < dist_to_zero:
                treat_translation_as_absolute = True
                print(
                    f"AF translation for bone '{pose_bone.name}' appears absolute; "
                    f"subtracting rest translation {tuple(rest_translation)}"
                )

        for rot_entry in block.get("rotation_sequence", []):
            frame = int(rot_entry.get("frame", 0))
            if "value" in rot_entry:
                x, y, z, w = rot_entry["value"]
            else:
                x = rot_entry.get("x", 0.0)
                y = rot_entry.get("y", 0.0)
                z = rot_entry.get("z", 0.0)
                w = rot_entry.get("w", 1.0)

            if use_direct_fcurves:
                for axis_index, axis_value in enumerate((w, x, y, z)):
                    fcurve = _get_or_create_fcurve(slot, fcurve_cache, rot_path, axis_index, pose_bone.name)
                    if fcurve is not None:
                        fcurve.keyframe_points.insert(frame=frame, value=float(axis_value), options={'FAST'})
                        inserted_channel_points += 1
            else:
                pose_bone.rotation_quaternion = mathutils.Quaternion((w, x, y, z))
                if armature_obj.keyframe_insert(data_path=rot_path, frame=frame, group=pose_bone.name):
                    inserted_channel_points += 4

            max_frame = max(max_frame, frame)
            total_keyframes += 1

        for trn_entry in translation_sequence:
            frame = int(trn_entry.get("frame", 0))
            if "value" in trn_entry:
                tx, ty, tz = trn_entry["value"]
            else:
                tx = trn_entry.get("x", 0.0)
                ty = trn_entry.get("y", 0.0)
                tz = trn_entry.get("z", 0.0)

            if root_translation_offset is not None:
                tx -= root_translation_offset.x
                ty -= root_translation_offset.y
                tz -= root_translation_offset.z

            if compensate_object_scale:
                tx *= scale_compensation.x
                ty *= scale_compensation.y
                tz *= scale_compensation.z

            if treat_translation_as_absolute:
                tx -= rest_translation.x
                ty -= rest_translation.y
                tz -= rest_translation.z

            if use_direct_fcurves:
                for axis_index, axis_value in enumerate((tx, ty, tz)):
                    fcurve = _get_or_create_fcurve(slot, fcurve_cache, loc_path, axis_index, pose_bone.name)
                    if fcurve is not None:
                        fcurve.keyframe_points.insert(frame=frame, value=float(axis_value), options={'FAST'})
                        inserted_channel_points += 1
            else:
                pose_bone.location = (tx, ty, tz)
                if armature_obj.keyframe_insert(data_path=loc_path, frame=frame, group=pose_bone.name):
                    inserted_channel_points += 3

            max_frame = max(max_frame, frame)
            total_keyframes += 1

    if use_direct_fcurves:
        for fcurve in fcurve_cache.values():
            fcurve.update()
    else:
        # Action is lazily created by Blender's keying system in newer APIs.
        action = armature_obj.animation_data.action if armature_obj.animation_data else None
        if action is not None and action.name != animation_name:
            action.name = animation_name
        if hasattr(action, 'fcurves') and action.fcurves:
            for fcurve in action.fcurves:
                fcurve.update()
        print(
            "Blender fallback keying action status: "
            f"action={'None' if action is None else action.name}, "
            f"inserted_channel_points={inserted_channel_points}"
        )

    if set_frame_end and max_frame > 0:
        scene.frame_end = max(scene.frame_end, max_frame)

    return {
        "applied_bones": applied_bones,
        "missing_bones": missing_bones,
        "keyframes": total_keyframes,
        "channel_points": inserted_channel_points,
        "fcurve_count": len(action.fcurves) if (hasattr(action, 'fcurves') and action and action.fcurves) else -1,
        "fcurve_api_used": use_direct_fcurves,
        "max_frame": max_frame,
        "animation_name": animation_name,
    }


class BGS_STARFIELD_OT_import_rig(bpy.types.Operator):
    bl_idname = "import_scene.bgs_starfield_rig"
    bl_label = "Import Starfield Rig (.rig)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.rig", options={'HIDDEN'})

    import_reference: bpy.props.BoolProperty(
        name="Import Reference Mesh",
        description="Import reference mesh if available (looks for .fbx file with same name as .rig file)",
        default=True
    )

    use_existing_mesh: bpy.props.BoolProperty(
        name="Use Selected Mesh as Reference",
        description="Position rig relative to selected mesh object in scene",
        default=False
    )

    def execute(self, context):
        if not os.path.isfile(self.filepath) or not self.filepath.lower().endswith('.rig'):
            self.report({'ERROR'}, "Please select a valid .rig file")
            return {'CANCELLED'}

        adapter = get_adapter()
        if not adapter.is_loaded():
            self.report({'ERROR'}, "CALUMI.Animation.dll not loaded. Please ensure the addon is properly installed.")
            return {'CANCELLED'}

        rig_data = adapter.import_rig(self.filepath)
        if rig_data is None:
            self.report({'ERROR'}, f"Failed to import rig from {self.filepath}. Check the console for details.")
            return {'CANCELLED'}

        rig_name = sanitize_name(os.path.splitext(os.path.basename(self.filepath))[0])

        # Track reference objects for post-import auto-connection
        reference_mesh_objects = []
        bone_empty_objects = {}

        # Check for existing mesh reference
        reference_mesh_obj = None
        if self.use_existing_mesh:
            # Use the active object if it's a mesh
            active_obj = context.view_layer.objects.active
            selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

            if active_obj and active_obj.type == 'MESH':
                reference_mesh_obj = active_obj
                reference_mesh_objects = selected_meshes if selected_meshes else [active_obj]
                self.report({'INFO'}, f"Using existing mesh '{reference_mesh_obj.name}' as reference")
            else:
                # Check selected objects for a mesh
                if selected_meshes:
                    reference_mesh_obj = selected_meshes[0]
                    reference_mesh_objects = selected_meshes
                    self.report({'INFO'}, f"Using selected mesh '{reference_mesh_obj.name}' as reference")
                else:
                    self.report({'WARNING'}, "No mesh object selected/active for reference")

        # Import reference mesh from file if requested and no existing mesh is being used
        mesh_obj = None
        if self.import_reference and not reference_mesh_obj:
            reference_path = os.path.splitext(self.filepath)[0] + '.fbx'
            if os.path.isfile(reference_path):
                try:
                    # Import FBX without animation to get just the mesh
                    existing_objects = set(context.scene.objects)
                    bpy.ops.import_scene.fbx(filepath=reference_path, use_anim=False)

                    # Find the newly imported objects
                    new_objects = set(context.scene.objects) - existing_objects
                    mesh_objects = [obj for obj in new_objects if obj.type == 'MESH']
                    reference_mesh_objects = list(mesh_objects)

                    # Remove any imported armatures (we only want the mesh)
                    armature_objects = [obj for obj in new_objects if obj.type == 'ARMATURE']
                    for armature in armature_objects:
                        bpy.data.objects.remove(armature)

                    if mesh_objects:
                        # Prefer the densest mesh as alignment reference when multiple parts exist.
                        mesh_obj = max(mesh_objects, key=lambda obj: len(obj.data.vertices))
                        if len(mesh_objects) == 1:
                            mesh_obj.name = f"{rig_name}_reference"
                            self.report({'INFO'}, f"Imported reference mesh: {mesh_obj.name}")
                        else:
                            self.report({'INFO'}, f"Imported {len(mesh_objects)} reference mesh parts")
                    else:
                        self.report({'WARNING'}, "Reference FBX file found but no mesh objects were imported")

                except Exception as e:
                    self.report({'WARNING'}, f"Failed to import reference mesh: {str(e)}")

        # Use existing mesh if available, otherwise use imported mesh
        final_reference_obj = reference_mesh_obj or mesh_obj

        # Get mesh position for bone offset if using reference
        mesh_offset = mathutils.Vector((0, 0, 0))
        bone_position_overrides = {}  # bone_name -> position

        if final_reference_obj:
            # Get the mesh's world position as base offset
            mesh_world_pos = final_reference_obj.location
            mesh_offset = mesh_world_pos
            print(f"Using mesh world position as base offset: {mesh_offset}")

            # Try to find empty objects that match bone names for precise positioning
            scene_objects = context.scene.objects
            skel_rig = rig_data["rig"]

            for bone in skel_rig.bones:
                if bone.bone_name:
                    # Look for empty objects with matching names
                    for obj in scene_objects:
                        if obj.type == 'EMPTY' and obj.name == bone.bone_name:
                            # Use the empty's world position (accounting for parenting)
                            world_pos = obj.matrix_world.translation.copy()
                            # Transform to mesh local space
                            mesh_matrix_inv = final_reference_obj.matrix_world.inverted()
                            local_pos = mesh_matrix_inv @ world_pos
                            bone_position_overrides[bone.bone_name] = local_pos
                            bone_empty_objects[bone.bone_name] = obj
                            print(f"Found matching empty for bone '{bone.bone_name}' at mesh local position {local_pos}")
                            print(f"Empty name: {repr(obj.name)}, Bone name: {repr(bone.bone_name)}")
                            break

            if bone_position_overrides:
                print(f"Found {len(bone_position_overrides)} bone position overrides from empties")
                print(f"Override bone names: {list(bone_position_overrides.keys())}")
                print("Using empty positions instead of rig data for bone placement")
            else:
                print("No bone empties found, using rig data positions")

        # Create armature from rig data
        armature_data = bpy.data.armatures.new(name=f"{rig_name}_data")
        armature_obj = bpy.data.objects.new(name=rig_name, object_data=armature_data)
        context.collection.objects.link(armature_obj)
        context.view_layer.objects.active = armature_obj
        armature_obj.select_set(True)

        # Align armature to the full mesh transform so armature-space matches mesh local-space
        if final_reference_obj:
            armature_obj.matrix_world = final_reference_obj.matrix_world.copy()
            print(
                "Positioned armature using mesh world transform: "
                f"loc={armature_obj.location}, rot={armature_obj.rotation_euler}, scale={armature_obj.scale}"
            )

        # Enter edit mode to create bones
        bpy.ops.object.mode_set(mode='EDIT')

        skel_rig = rig_data["rig"]

        # Create bones with positions relative to armature (not world space)
        # Remove mesh_offset since armature is already positioned at mesh location
        create_bone_hierarchy(armature_data, skel_rig, mesh_offset=mathutils.Vector((0, 0, 0)), bone_position_overrides=bone_position_overrides)

        # Apply axis correction to all bones (like sf_animation_io RigPostProcess)
        # Preserve translation to avoid drifting override-positioned bones.
        for edit_bone in armature_data.edit_bones:
            corrected_matrix = apply_bone_axis_correction(edit_bone.matrix)
            corrected_matrix.translation = edit_bone.matrix.translation
            edit_bone.matrix = corrected_matrix

        # Final snap pass: enforce exact head placement for bones with empty-derived overrides.
        # This removes any residual drift from hierarchy/correction math.
        if bone_position_overrides:
            snapped_count = 0
            for bone_name, target_pos in bone_position_overrides.items():
                if bone_name in armature_data.edit_bones:
                    edit_bone = armature_data.edit_bones[bone_name]
                    delta = mathutils.Vector(target_pos) - edit_bone.head.copy()
                    if delta.length > 1e-6:
                        edit_bone.head += delta
                        edit_bone.tail += delta
                    snapped_count += 1
            print(f"Final snap pass applied to {snapped_count} bones using empty overrides")

        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Ensure armature is visible (Blender 5.0 compatibility)
        armature_obj.hide_viewport = False
        # armature_obj.display_type = 'OCTAHEDRAL'  # Not valid for objects in Blender 5.0
        armature_data.display_type = 'OCTAHEDRAL'

        # Switch to pose mode to make bones visible
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.object.mode_set(mode='OBJECT')

        rig_props = armature_obj.bgs_starfield_animation_rig_props
        rig_props.is_rig = True
        rig_props.rig_name = rig_name

        rig_bind_collection = None

        # Scale to match reference mesh when available and then connect mesh to this armature
        if final_reference_obj:
            if bone_position_overrides:
                print("Skipping rig auto-scale because override positions already define target placement")
            else:
                # Scale the rig to match mesh size when using raw rig-space data
                rig_bounds = self._get_rig_bounds(armature_obj)
                rig_size = rig_bounds['size']

                mesh_bounds = self._get_mesh_bounds(final_reference_obj)
                mesh_size = mesh_bounds['size']

                if rig_size.length > 0 and mesh_size.length > 0:
                    scale_factor = mesh_size.length / rig_size.length
                    armature_obj.scale = mathutils.Vector((scale_factor, scale_factor, scale_factor))
                    print(f"Scaled rig by factor {scale_factor} to match mesh size")
                    print(f"Rig size: {rig_size.length}, Mesh size: {mesh_size.length}")

            # Connect all known mesh parts (selected or imported), falling back to the chosen reference object.
            target_meshes = reference_mesh_objects if reference_mesh_objects else [final_reference_obj]
            parent_to_armature = True
            bone_named_objects = {}

            # When rigging onto an existing mesh, create rig-bound duplicates in a new collection
            # so the original model hierarchy remains untouched for export workflows.
            if self.use_existing_mesh and reference_mesh_obj and target_meshes:
                rig_bind_collection = self._create_rig_bind_collection(context, rig_name)
                duplicated_objects = self._duplicate_mesh_hierarchy_for_rig_binding(
                    target_meshes,
                    rig_bind_collection,
                    name_suffix="_bound",
                )
                duplicated_meshes = [
                    duplicate_obj
                    for source_obj, duplicate_obj in duplicated_objects.items()
                    if source_obj and source_obj.type == 'MESH'
                ]

                armature_bone_names = set(bone.name for bone in armature_obj.data.bones)
                bone_named_objects = {obj.name: obj for obj in context.scene.objects if obj.type == 'EMPTY' and obj.name in armature_bone_names}

                if duplicated_meshes:
                    target_meshes = duplicated_meshes
                    self.report(
                        {'INFO'},
                        f"Created {len(duplicated_meshes)} rig-bound mesh duplicate(s) in collection '{rig_bind_collection.name}'"
                    )

            self._connect_meshes_to_armature(target_meshes, armature_obj, parent_to_armature=parent_to_armature)

            if bone_named_objects:
                self._connect_named_objects_to_bones(
                    bone_named_objects,
                    armature_obj,
                    keep_parentage=True,
                )
                print(
                    f"Connected {len(bone_named_objects)} duplicate mesh anchors to matching rig bones "
                    "while preserving duplicate hierarchy"
                )

        # If there are empties named like bones, parent them to the matching bones automatically.
        # This keeps empty-driven mesh part hierarchies attached to the imported rig.
        # if bone_empty_objects:
        #     self._connect_named_empties_to_bones(bone_empty_objects, armature_obj)

        self.report({'INFO'}, f"Rig '{rig_name}' imported successfully with {len(skel_rig.bones)} bones")
        return {'FINISHED'}

    def _position_rig_to_mesh(self, armature_obj, mesh_obj):
        """Position and scale the rig armature to match the reference mesh."""
        # Calculate mesh bounding box
        mesh_bounds = self._get_mesh_bounds(mesh_obj)
        mesh_center = mathutils.Vector(mesh_bounds['center'])
        mesh_size = mesh_bounds['size']

        print(f"Mesh bounds: center={mesh_center}, size={mesh_size}")

        # Calculate rig bounds (approximate from bone positions)
        rig_bounds = self._get_rig_bounds(armature_obj)
        rig_size = rig_bounds['size']

        print(f"Rig bounds: size={rig_size}")

        # For now, just position the rig at the mesh location without scaling
        # Scaling rigs can break bone proportions and relationships
        armature_obj.location = mesh_center

        print(f"Rig positioned at {mesh_center}")

        # Optional: Could also match rotation if needed
        # armature_obj.rotation_euler = mesh_obj.rotation_euler

    def _get_mesh_bounds(self, mesh_obj):
        """Calculate the bounding box and center of a mesh object."""
        # Get mesh in world space
        mesh = mesh_obj.data
        matrix_world = mesh_obj.matrix_world

        # Calculate bounds
        min_bounds = [float('inf')] * 3
        max_bounds = [float('-inf')] * 3

        for vert in mesh.vertices:
            world_pos = matrix_world @ vert.co
            for i in range(3):
                min_bounds[i] = min(min_bounds[i], world_pos[i])
                max_bounds[i] = max(max_bounds[i], world_pos[i])

        center = [(min_bounds[i] + max_bounds[i]) / 2 for i in range(3)]
        size = [max_bounds[i] - min_bounds[i] for i in range(3)]

        return {
            'min': min_bounds,
            'max': max_bounds,
            'center': center,
            'size': mathutils.Vector(size)
        }

    def _get_rig_bounds(self, armature_obj):
        """Calculate approximate bounds of the rig from bone positions."""
        # Get armature in edit mode to access bone positions
        original_mode = armature_obj.mode
        bpy.context.view_layer.objects.active = armature_obj

        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        min_bounds = [float('inf')] * 3
        max_bounds = [float('-inf')] * 3

        for edit_bone in armature_obj.data.edit_bones:
            # Check head position
            for i in range(3):
                min_bounds[i] = min(min_bounds[i], edit_bone.head[i])
                max_bounds[i] = max(max_bounds[i], edit_bone.head[i])

            # Check tail position
            for i in range(3):
                min_bounds[i] = min(min_bounds[i], edit_bone.tail[i])
                max_bounds[i] = max(max_bounds[i], edit_bone.tail[i])

        # Restore original mode
        if original_mode != 'EDIT':
            bpy.ops.object.mode_set(mode=original_mode)

        center = [(min_bounds[i] + max_bounds[i]) / 2 for i in range(3)]
        size = [max_bounds[i] - min_bounds[i] for i in range(3)]

        return {
            'min': min_bounds,
            'max': max_bounds,
            'center': center,
            'size': mathutils.Vector(size)
        }

    def _create_rig_bind_collection(self, context, rig_name):
        """Create a dedicated collection for rig-bound mesh duplicates."""
        base_name = f"{sanitize_name(rig_name)}_bound"
        collection_name = base_name
        counter = 1

        while collection_name in bpy.data.collections:
            collection_name = f"{base_name}_{counter}"
            counter += 1

        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
        return collection

    def _link_object_to_collection(self, obj, collection):
        """Link an object to a collection if not already linked."""
        if not obj or not collection:
            return

        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)

    def _duplicate_mesh_hierarchy_for_rig_binding(self, mesh_objects, target_collection, name_suffix="_bound"):
        """Duplicate mesh objects and their parent hierarchy into target collection."""
        objects_to_duplicate = []
        seen = set()
        allowed_types = {'MESH'}

        for mesh_obj in mesh_objects:
            if not mesh_obj or mesh_obj.type != 'MESH':
                continue

            current = mesh_obj
            while current:
                if current.type not in allowed_types:
                    break
                if current not in seen:
                    objects_to_duplicate.append(current)
                    seen.add(current)
                current = current.parent

        source_to_duplicate = {}

        # Create duplicates first.
        for source_obj in objects_to_duplicate:
            duplicate_obj = source_obj.copy()
            if source_obj.type == 'MESH' and source_obj.data:
                duplicate_obj.data = source_obj.data.copy()

            duplicate_obj.animation_data_clear()
            duplicate_obj.name = f"{source_obj.name}{name_suffix}"

            duplicate_obj.parent = None
            duplicate_obj.matrix_world = source_obj.matrix_world.copy()

            target_collection.objects.link(duplicate_obj)
            source_to_duplicate[source_obj] = duplicate_obj

        # Rebuild parent hierarchy among duplicates while keeping world transforms.
        for source_obj, duplicate_obj in source_to_duplicate.items():
            source_parent = source_obj.parent
            if source_parent and source_parent in source_to_duplicate:
                world_matrix = duplicate_obj.matrix_world.copy()
                duplicate_obj.parent = source_to_duplicate[source_parent]
                duplicate_obj.parent_type = 'OBJECT'
                duplicate_obj.parent_bone = ""
                duplicate_obj.matrix_parent_inverse = duplicate_obj.parent.matrix_world.inverted()
                duplicate_obj.matrix_world = world_matrix

        return source_to_duplicate

    def _connect_mesh_to_armature(self, mesh_obj, armature_obj, parent_to_armature=False):
        """Ensure the mesh is driven by this armature via modifier + parent relation."""
        if not mesh_obj or mesh_obj.type != 'MESH' or not armature_obj or armature_obj.type != 'ARMATURE':
            return

        # Reuse an existing armature modifier when possible; otherwise create one.
        armature_mod = None
        for modifier in mesh_obj.modifiers:
            if modifier.type == 'ARMATURE':
                armature_mod = modifier
                break

        if armature_mod is None:
            armature_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')

        armature_mod.object = armature_obj

        if parent_to_armature:
            mesh_world_matrix = mesh_obj.matrix_world.copy()
            mesh_obj.parent = armature_obj
            mesh_obj.parent_type = 'OBJECT'
            mesh_obj.matrix_parent_inverse = armature_obj.matrix_world.inverted()
            mesh_obj.matrix_world = mesh_world_matrix
            print(f"Parented mesh '{mesh_obj.name}' to armature '{armature_obj.name}'")

        # Parent mesh to armature object only when it does not already have an intentional parent
        # (for example, an EMPTY that we later parent to a matching bone).
        # To preserve mesh parentage, don't parent to armature.
        # if mesh_obj.parent is None:
        #     mesh_obj.parent = armature_obj
        #     mesh_obj.parent_type = 'OBJECT'
        #     mesh_obj.matrix_parent_inverse = armature_obj.matrix_world.inverted()

        print(f"Connected mesh '{mesh_obj.name}' to armature '{armature_obj.name}' via Armature modifier")

    def _connect_meshes_to_armature(self, mesh_objects, armature_obj, parent_to_armature=False):
        """Connect a collection of mesh objects to the imported armature."""
        if not mesh_objects:
            return

        seen_names = set()
        for mesh_obj in mesh_objects:
            if not mesh_obj or mesh_obj.type != 'MESH' or mesh_obj.name in seen_names:
                continue
            self._connect_mesh_to_armature(mesh_obj, armature_obj, parent_to_armature=parent_to_armature)
            seen_names.add(mesh_obj.name)

    def _connect_named_empties_to_bones(self, bone_empty_objects, armature_obj):
        """Parent empties to matching bones by name while preserving world transforms."""
        if not bone_empty_objects or not armature_obj or armature_obj.type != 'ARMATURE':
            return

        armature_bone_names = set(bone.name for bone in armature_obj.data.bones)

        for bone_name, empty_obj in bone_empty_objects.items():
            if not empty_obj or empty_obj.type != 'EMPTY' or bone_name not in armature_bone_names:
                continue

            empty_world_matrix = empty_obj.matrix_world.copy()
            empty_obj.parent = armature_obj
            empty_obj.parent_type = 'BONE'
            empty_obj.parent_bone = bone_name
            empty_obj.matrix_world = empty_world_matrix

            print(f"Connected empty '{empty_obj.name}' to bone '{bone_name}' on armature '{armature_obj.name}'")

    def _connect_named_objects_to_bones(self, named_objects, armature_obj, keep_parentage=False):
        """Connect objects to matching armature bones while optionally preserving parent hierarchy."""
        if not named_objects or not armature_obj or armature_obj.type != 'ARMATURE':
            return

        armature_bone_names = set(bone.name for bone in armature_obj.data.bones)
        anchored_objects = set(obj for obj in named_objects.values() if obj is not None)

        for bone_name, obj in named_objects.items():
            if not obj or bone_name not in armature_bone_names:
                continue

            # Avoid double transforms: if this object has an ancestor that is also bone-anchored,
            # let it inherit through the existing object hierarchy instead of adding another bone driver.
            parent_anchor = obj.parent
            has_anchored_ancestor = False
            while parent_anchor:
                if parent_anchor in anchored_objects:
                    has_anchored_ancestor = True
                    break
                parent_anchor = parent_anchor.parent

            if keep_parentage and has_anchored_ancestor:
                print(
                    f"Skipping nested bone connection for '{obj.name}' (bone '{bone_name}') "
                    "because an ancestor is already bone-connected"
                )
                continue

            if keep_parentage and obj.parent is not None:
                constraint_name = f"BGS_BoneBind_{bone_name}"
                child_of = None

                for constraint in obj.constraints:
                    if constraint.type == 'CHILD_OF' and constraint.name == constraint_name:
                        child_of = constraint
                        break

                if child_of is None:
                    child_of = obj.constraints.new(type='CHILD_OF')
                    child_of.name = constraint_name

                child_of.target = armature_obj
                child_of.subtarget = bone_name

                if bone_name in armature_obj.data.bones:
                    bone_world_matrix = armature_obj.matrix_world @ armature_obj.data.bones[bone_name].matrix_local
                    child_of.inverse_matrix = bone_world_matrix.inverted() @ obj.matrix_world

                print(
                    f"Constrained object '{obj.name}' to bone '{bone_name}' "
                    "with Child Of to preserve existing parentage"
                )
            else:
                obj_world_matrix = obj.matrix_world.copy()
                obj.parent = armature_obj
                obj.parent_type = 'BONE'
                obj.parent_bone = bone_name
                obj.matrix_world = obj_world_matrix

                print(f"Parented object '{obj.name}' to bone '{bone_name}' on armature '{armature_obj.name}'")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "import_reference")
        layout.label(text="Import reference mesh (.fbx) with same name if available")
        layout.label(text="Example: MyRig.rig + MyRig.fbx in same folder")

        layout.separator()
        layout.prop(self, "use_existing_mesh")
        layout.label(text="Position rig relative to selected/active mesh in scene")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BGS_STARFIELD_OT_export_rig(bpy.types.Operator):
    bl_idname = "export_scene.bgs_starfield_rig"
    bl_label = "Export Starfield Rig (.rig)"

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filename: bpy.props.StringProperty(default='skeleton.rig')
    filter_glob: bpy.props.StringProperty(default="*.rig", options={'HIDDEN'})

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature to export")
            return {'CANCELLED'}
        if not obj.bgs_starfield_animation_rig_props.is_rig:
            self.report({'ERROR'}, "Selected armature is not marked as a Starfield rig")
            return {'CANCELLED'}

        adapter = get_adapter()
        if not adapter.is_loaded():
            self.report({'ERROR'}, "CALUMI.Animation.dll not loaded. Please ensure the addon is properly installed.")
            return {'CANCELLED'}

        # TODO: Extract rig data from armature (convert Blender armature to CALUMI SkeletonRig)
        rig_data = {"pointer": None}  # Placeholder - need to implement conversion

        success = adapter.export_rig(rig_data, self.filepath)
        if not success:
            self.report({'ERROR'}, f"Failed to export rig to {self.filepath}. Check the console for details.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Rig exported to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object and context.object.type == 'ARMATURE':
            rig_name = context.object.bgs_starfield_animation_rig_props.rig_name
            if rig_name:
                self.filename = f"{sanitize_name(rig_name)}.rig"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BGS_STARFIELD_OT_import_af(bpy.types.Operator):
    bl_idname = "import_scene.bgs_starfield_af"
    bl_label = "Import Starfield Animation (.af)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.af", options={'HIDDEN'})

    def _resolve_target_armature(self, obj):
        """Resolve an armature target from the active object (armature or mesh-driven armature)."""
        if not obj:
            return None

        if obj.type == 'ARMATURE':
            return obj

        if obj.type == 'MESH':
            for modifier in obj.modifiers:
                if modifier.type == 'ARMATURE' and modifier.object and modifier.object.type == 'ARMATURE':
                    return modifier.object

            if obj.parent and obj.parent.type == 'ARMATURE':
                return obj.parent

        return None

    def execute(self, context):
        if not os.path.isfile(self.filepath) or not self.filepath.lower().endswith('.af'):
            self.report({'ERROR'}, "Please select a valid .af file")
            return {'CANCELLED'}

        adapter = get_adapter()
        if not adapter.is_loaded():
            self.report({'ERROR'}, "CALUMI.Animation.dll not loaded. Please ensure the addon is properly installed.")
            return {'CANCELLED'}

        tool_props = context.scene.bgs_starfield_animation_tool_props
        if tool_props.selected_rig == 'NONE':
            self.report({'ERROR'}, "Register/select a rig before importing .af")
            return {'CANCELLED'}

        # CALUMI requires a rig file path in the load file-list to convert .af to UNIV scene.
        rig_path = get_registered_rig_path(tool_props.rig_registry_dir, tool_props.selected_rig)

        # Fallback discovery for common Starfield layout when registry is not populated.
        if not rig_path:
            af_dir = os.path.dirname(self.filepath)
            af_stem = os.path.splitext(os.path.basename(self.filepath))[0]
            candidate_paths = [
                os.path.join(af_dir, f"{af_stem}.rig"),
                os.path.join(af_dir, "skeleton.rig"),
                os.path.join(os.path.dirname(af_dir), "skeleton.rig"),
                os.path.join(os.path.dirname(af_dir), "characterassets", "skeleton.rig"),
            ]
            for candidate in candidate_paths:
                if os.path.isfile(candidate):
                    rig_path = candidate
                    print(f"Resolved rig path for AF import from file layout: {rig_path}")
                    break

        if not rig_path:
            self.report(
                {'ERROR'},
                "Failed to locate a .rig reference for AF import. "
                "CALUMI requires a .rig in the load file list. "
                "Place/register the matching skeleton.rig (e.g. sibling characterassets/skeleton.rig)."
            )
            return {'CANCELLED'}

        print(f"Importing AF with rig reference: af='{self.filepath}', rig='{rig_path}'")
        anim_data = adapter.import_animation(self.filepath, rig_path=rig_path)
        if anim_data is None:
            self.report({'ERROR'}, f"Failed to import animation from {self.filepath}. Check the console for details.")
            return {'CANCELLED'}

        obj = context.object
        target_obj = None

        if tool_props.import_af_mode == 'ON_ACTIVE_OBJECT':
            target_obj = self._resolve_target_armature(obj)
            if target_obj and obj and obj.type == 'MESH' and target_obj != obj:
                self.report({'INFO'}, f"Applying AF to armature '{target_obj.name}' resolved from active mesh")

        if target_obj is None:
            armature_data = bpy.data.armatures.new(name="imported_af_data")
            target_obj = bpy.data.objects.new(
                name=sanitize_name(os.path.splitext(os.path.basename(self.filepath))[0]),
                object_data=armature_data,
            )
            context.collection.objects.link(target_obj)

        # Build an armature from the selected rig when importing into a newly-created object.
        if len(target_obj.data.bones) == 0:
            built = ensure_armature_has_rig_bones(context, adapter, target_obj, rig_path)
            if not built:
                self.report(
                    {'ERROR'},
                    "AF loaded, but failed to build target armature from selected rig. "
                    "Select an existing rig armature or verify the registered rig file."
                )
                return {'CANCELLED'}

        # Ensure keyframe insertion has the right context on Blender versions where Action.fcurves
        # is unavailable and we must use pose_bone.keyframe_insert fallback.
        view_layer = context.view_layer
        previous_active = view_layer.objects.active
        previous_mode = target_obj.mode

        try:
            view_layer.objects.active = target_obj
            target_obj.select_set(True)
            if target_obj.mode != 'POSE':
                bpy.ops.object.mode_set(mode='POSE')

            # Apply extracted keyframes to target armature.
            apply_result = apply_af_animation_to_armature(
                context,
                target_obj,
                anim_data,
                set_frame_end=tool_props.set_frame_end,
            )
        finally:
            try:
                if target_obj.mode != previous_mode:
                    bpy.ops.object.mode_set(mode=previous_mode)
            except Exception:
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except Exception:
                    pass

            if previous_active and previous_active.name in bpy.data.objects:
                view_layer.objects.active = previous_active

        anim_props = target_obj.bgs_starfield_animation_clip_props
        anim_props.is_animation = True
        anim_props.animation_name = apply_result.get("animation_name") or sanitize_name(os.path.splitext(os.path.basename(self.filepath))[0])
        anim_props.source_rig_name = tool_props.selected_rig

        context.view_layer.objects.active = target_obj
        target_obj.select_set(True)

        # Ensure pose mode for Dope Sheet animation viewing
        bpy.ops.object.mode_set(mode='POSE')

        # Force UI redraw to update Dope Sheet
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        missing_count = len(apply_result.get("missing_bones", []))
        keyframe_count = apply_result.get("keyframes", 0)
        channel_points = apply_result.get("channel_points", 0)
        fcurve_count = apply_result.get("fcurve_count", -1)
        fcurve_api_used = apply_result.get("fcurve_api_used", False)
        applied_bones = apply_result.get("applied_bones", 0)
        max_frame = apply_result.get("max_frame", 0)

        print(
            "AF apply result: "
            f"animation='{anim_props.animation_name}', "
            f"applied_bones={applied_bones}, missing_bones={missing_count}, "
            f"keyframes={keyframe_count}, channel_points={channel_points}, "
            f"fcurve_count={fcurve_count}, max_frame={max_frame}"
        )

        no_channels = channel_points == 0 or (fcurve_api_used and fcurve_count == 0)

        if keyframe_count == 0 or no_channels:
            self.report(
                {'WARNING'},
                f"Animation '{anim_props.animation_name}' loaded but no channels were created. "
                f"Applied bones: {applied_bones}, missing bones: {missing_count}, "
                f"channel points: {channel_points}, fcurves: {fcurve_count}."
            )
        else:
            channel_text = (
                f"{fcurve_count} channels"
                if fcurve_count >= 0
                else f"{channel_points} channel points via Blender keyframe API"
            )
            self.report(
                {'INFO'},
                f"Animation '{anim_props.animation_name}' imported: {keyframe_count} keys, "
                f"{channel_text}, {applied_bones} bones, max frame {max_frame}"
            )

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class BGS_STARFIELD_OT_export_af(bpy.types.Operator):
    bl_idname = "export_scene.bgs_starfield_af"
    bl_label = "Export Starfield Animation (.af)"

    filepath: bpy.props.StringProperty(options={'HIDDEN'})
    filename: bpy.props.StringProperty(default='untitled.af')
    filter_glob: bpy.props.StringProperty(default="*.af", options={'HIDDEN'})

    def execute(self, context):
        obj = context.object
        tool_props = context.scene.bgs_starfield_animation_tool_props

        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select an armature animation to export")
            return {'CANCELLED'}
        if not obj.bgs_starfield_animation_clip_props.is_animation:
            self.report({'ERROR'}, "Armature is not marked as Starfield animation")
            return {'CANCELLED'}
        if tool_props.selected_rig == 'NONE':
            self.report({'ERROR'}, "Select a registered rig for export")
            return {'CANCELLED'}

        adapter = get_adapter()
        if not adapter.is_loaded():
            self.report({'ERROR'}, "CALUMI.Animation.dll not loaded. Please ensure the addon is properly installed.")
            return {'CANCELLED'}

        # TODO: Extract animation data from armature (convert Blender animation to CALUMI Animation)
        anim_data = {"pointer": None, "rig_path": None}  # Placeholder - need to implement conversion

        success = adapter.export_animation(anim_data, self.filepath)
        if not success:
            self.report({'ERROR'}, f"Failed to export animation to {self.filepath}. Check the console for details.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Animation exported to {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.object and context.object.type == 'ARMATURE':
            anim_name = context.object.bgs_starfield_animation_clip_props.animation_name
            if anim_name:
                self.filename = f"{sanitize_name(anim_name)}.af"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
