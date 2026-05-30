"""
CALUMI.Animation adapter for ctypes integration.

This module provides a Python interface to the CALUMI.Animation.dll
for importing/exporting Starfield .rig and .af files.

Based on sf_animation_io implementation.
"""

import ctypes
import math
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import mathutils


class RigBone:
    """Represents a bone in a Starfield rig."""

    def __init__(self):
        self.bone_name = None
        self.rotation = None  # (x, y, z, w) quaternion
        self.translation = None  # (x, y, z) vector
        self.parent_name = None
        self.parent_index = None
        self.index = None
        self.mirror_index = -1
        self.bone_type = 0  # 0=Default, 1=Twist
        self.mapping = 0xFF


class SkelRig:
    """Represents a complete Starfield skeleton rig."""

    def __init__(self):
        self.name = "UNKNOWN_RIG"
        self.bones = []
        self.precision = "DEFAULT"  # DEFAULT, FIRST_PERSON, SHIP


class CALUMIAdapter:
    """Adapter for CALUMI.Animation.dll using ctypes."""

    def __init__(self):
        self.dll = None
        self.loaded = False
        self._load_dll()
        self._setup_functions()

    def _get_english_bone_name(self, localized_name: str) -> str:
        """Convert localized bone names to English equivalents."""
        # Basic mapping for common Starfield bone names
        # This is a placeholder - you may need to expand this based on actual bone names
        name_mapping = {
            # Add mappings as needed
            # "LocalizedName": "EnglishName",
        }

        # For now, if the name contains non-ASCII characters, try to provide a more readable version
        if any(ord(c) > 127 for c in localized_name):
            # Keep the localized name but also provide an English fallback for common patterns
            # For demonstration, just return the localized name for now
            return localized_name

        return localized_name

    def _load_dll(self) -> bool:
        """Load the CALUMI.Animation.dll."""
        try:
            # Get addon directory
            addon_dir = Path(__file__).parent.parent.parent
            dll_path = addon_dir / "CALUMI.Animation.dll"

            if not dll_path.exists():
                print(f"CALUMI.Animation.dll not found at {dll_path}")
                return False

            self.dll = ctypes.CDLL(str(dll_path))
            self.loaded = True
            print("CALUMI.Animation.dll loaded successfully")
            return True

        except Exception as e:
            print(f"Failed to load CALUMI.Animation.dll: {e}")
            return False

    def _setup_functions(self):
        """Set up ctypes function signatures based on sf_animation_io."""
        if not self.loaded:
            return

        # Rig loading function
        self._LoadSFBGSSkeletonRigFromFileC = self.dll.LoadSFBGSSkeletonRigFromFileC
        self._LoadSFBGSSkeletonRigFromFileC.restype = ctypes.c_void_p  # SkeletonRig *
        self._LoadSFBGSSkeletonRigFromFileC.argtypes = [
            ctypes.c_wchar_p,  # const wchar_t * filePath
            ctypes.c_void_p,   # StringContainer * errorMsg
        ]

        # Rig saving function
        self._SaveSkeletonRigToSFBGSFormatDirectC = self.dll.SaveSkeletonRigToSFBGSFormatDirectC
        self._SaveSkeletonRigToSFBGSFormatDirectC.restype = ctypes.c_bool
        self._SaveSkeletonRigToSFBGSFormatDirectC.argtypes = [
            ctypes.c_void_p,  # SkeletonRig * rig
            ctypes.c_wchar_p, # const wchar_t * filePath
            ctypes.c_void_p,  # StringContainer * errorMsg
        ]

        # Animation loading function
        self._LoadAnimationSceneFromSFBGSFormatC = self.dll.LoadAnimationSceneFromSFBGSFormatC
        self._LoadAnimationSceneFromSFBGSFormatC.restype = ctypes.c_void_p  # AnimationScene *
        self._LoadAnimationSceneFromSFBGSFormatC.argtypes = [
            ctypes.POINTER(ctypes.c_wchar_p),  # const wchar_t ** filePaths
            ctypes.c_int,                      # int fileCount
            ctypes.c_void_p,                   # StringContainer * errorMsg
        ]

        # Scene extraction helpers (UNIV extern "C")
        try:
            self._DeleteAnimationSceneC = self.dll.DeleteAnimationSceneC
            self._DeleteAnimationSceneC.restype = ctypes.c_bool
            self._DeleteAnimationSceneC.argtypes = [ctypes.c_void_p]

            self._GetAnimationCountC = self.dll.GetAnimationCountC
            self._GetAnimationCountC.restype = ctypes.c_size_t
            self._GetAnimationCountC.argtypes = [ctypes.c_void_p]

            self._GetAnimationC = self.dll.GetAnimationC
            self._GetAnimationC.restype = ctypes.c_void_p
            self._GetAnimationC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetAnimationTitleC = self.dll.GetAnimationTitleC
            self._GetAnimationTitleC.restype = ctypes.c_char_p
            self._GetAnimationTitleC.argtypes = [ctypes.c_void_p]

            self._GetAnimationBlockCountC = self.dll.GetAnimationBlockCountC
            self._GetAnimationBlockCountC.restype = ctypes.c_size_t
            self._GetAnimationBlockCountC.argtypes = [ctypes.c_void_p]

            self._GetAnimationBlockC = self.dll.GetAnimationBlockC
            self._GetAnimationBlockC.restype = ctypes.c_void_p
            self._GetAnimationBlockC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetAnimBlockBoneNameC = self.dll.GetAnimBlockBoneNameC
            self._GetAnimBlockBoneNameC.restype = ctypes.c_char_p
            self._GetAnimBlockBoneNameC.argtypes = [ctypes.c_void_p]

            self._GetAnimBlockBoneIndexC = self.dll.GetAnimBlockBoneIndexC
            self._GetAnimBlockBoneIndexC.restype = ctypes.c_int
            self._GetAnimBlockBoneIndexC.argtypes = [ctypes.c_void_p]

            self._GetRotationFromSqC = self.dll.GetRotationFromSqC
            self._GetRotationFromSqC.restype = ctypes.c_void_p
            self._GetRotationFromSqC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetRotationSqSizeC = self.dll.GetRotationSqSizeC
            self._GetRotationSqSizeC.restype = ctypes.c_size_t
            self._GetRotationSqSizeC.argtypes = [ctypes.c_void_p]

            self._GetTranslationFromSqC = self.dll.GetTranslationFromSqC
            self._GetTranslationFromSqC.restype = ctypes.c_void_p
            self._GetTranslationFromSqC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetTranslationSqSizeC = self.dll.GetTranslationSqSizeC
            self._GetTranslationSqSizeC.restype = ctypes.c_size_t
            self._GetTranslationSqSizeC.argtypes = [ctypes.c_void_p]

            self._GetFrameFromRotationEntryC = self.dll.GetFrameFromRotationEntryC
            self._GetFrameFromRotationEntryC.restype = ctypes.c_uint16
            self._GetFrameFromRotationEntryC.argtypes = [ctypes.c_void_p]

            self._GetFrameFromTranslationEntryC = self.dll.GetFrameFromTranslationEntryC
            self._GetFrameFromTranslationEntryC.restype = ctypes.c_uint16
            self._GetFrameFromTranslationEntryC.argtypes = [ctypes.c_void_p]

            self._GetValueFromRotationEntryC = self.dll.GetValueFromRotationEntryC
            self._GetValueFromRotationEntryC.restype = ctypes.c_void_p
            self._GetValueFromRotationEntryC.argtypes = [ctypes.c_void_p]

            self._GetValueFromTranslationEntryC = self.dll.GetValueFromTranslationEntryC
            self._GetValueFromTranslationEntryC.restype = ctypes.c_void_p
            self._GetValueFromTranslationEntryC.argtypes = [ctypes.c_void_p]

        except AttributeError as e:
            print(f"Warning: Some animation scene extraction functions not available: {e}")

        # Animation saving function
        self._SaveAnimationToSFBGSFormatWithExistingRigDirectC = self.dll.SaveAnimationToSFBGSFormatWithExistingRigDirectC
        self._SaveAnimationToSFBGSFormatWithExistingRigDirectC.restype = ctypes.c_bool
        self._SaveAnimationToSFBGSFormatWithExistingRigDirectC.argtypes = [
            ctypes.c_void_p,  # Animation * anim
            ctypes.c_wchar_p, # const wchar_t * filePath
            ctypes.c_wchar_p, # const wchar_t * rigPath
            ctypes.c_void_p,  # StringContainer * errorMsg
        ]

        # Helper functions for extracting data from pointers
        try:
            self._GetSkeletonRigBoneCountC = self.dll.GetSkeletonRigBoneCountC
            self._GetSkeletonRigBoneCountC.restype = ctypes.c_int
            self._GetSkeletonRigBoneCountC.argtypes = [ctypes.c_void_p]

            self._GetSkeletonBoneC = self.dll.GetSkeletonBoneC
            self._GetSkeletonBoneC.restype = ctypes.c_void_p
            self._GetSkeletonBoneC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_bool]

            self._GetSkeletonBoneNameC = self.dll.GetSkeletonBoneNameC
            self._GetSkeletonBoneNameC.restype = ctypes.c_char_p  # char *, not wchar_p
            self._GetSkeletonBoneNameC.argtypes = [ctypes.c_void_p]

            self._GetSkeletonBoneParentIndexC = self.dll.GetSkeletonBoneParentIndexC
            self._GetSkeletonBoneParentIndexC.restype = ctypes.c_int
            self._GetSkeletonBoneParentIndexC.argtypes = [ctypes.c_void_p]

            self._GetSkeletonBonePositionC = self.dll.GetSkeletonBonePositionC
            self._GetSkeletonBonePositionC.restype = ctypes.c_void_p
            self._GetSkeletonBonePositionC.argtypes = [ctypes.c_void_p, ctypes.c_bool]

            self._GetSkeletonBoneRotationC = self.dll.GetSkeletonBoneRotationC
            self._GetSkeletonBoneRotationC.restype = ctypes.c_void_p
            self._GetSkeletonBoneRotationC.argtypes = [ctypes.c_void_p, ctypes.c_bool]

            self._GetVector3X = self.dll.GetVector3X
            self._GetVector3X.restype = ctypes.c_float
            self._GetVector3X.argtypes = [ctypes.c_void_p]

            self._GetVector3Y = self.dll.GetVector3Y
            self._GetVector3Y.restype = ctypes.c_float
            self._GetVector3Y.argtypes = [ctypes.c_void_p]

            self._GetVector3Z = self.dll.GetVector3Z
            self._GetVector3Z.restype = ctypes.c_float
            self._GetVector3Z.argtypes = [ctypes.c_void_p]

            # Also define double versions used by sf_animation_io
            self._GetVector3DX = self.dll.GetVector3DX
            self._GetVector3DX.restype = ctypes.c_double
            self._GetVector3DX.argtypes = [ctypes.c_void_p]

            self._GetVector3DY = self.dll.GetVector3DY
            self._GetVector3DY.restype = ctypes.c_double
            self._GetVector3DY.argtypes = [ctypes.c_void_p]

            self._GetVector3DZ = self.dll.GetVector3DZ
            self._GetVector3DZ.restype = ctypes.c_double
            self._GetVector3DZ.argtypes = [ctypes.c_void_p]

            self._GetQuaternionX = self.dll.GetQuaternionX
            self._GetQuaternionX.restype = ctypes.c_double
            self._GetQuaternionX.argtypes = [ctypes.c_void_p]

            self._GetQuaternionY = self.dll.GetQuaternionY
            self._GetQuaternionY.restype = ctypes.c_double
            self._GetQuaternionY.argtypes = [ctypes.c_void_p]

            self._GetQuaternionZ = self.dll.GetQuaternionZ
            self._GetQuaternionZ.restype = ctypes.c_double
            self._GetQuaternionZ.argtypes = [ctypes.c_void_p]

            self._GetQuaternionW = self.dll.GetQuaternionW
            self._GetQuaternionW.restype = ctypes.c_double
            self._GetQuaternionW.argtypes = [ctypes.c_void_p]

            # Animation scene helpers
            self._DeleteAnimationSceneC = self.dll.DeleteAnimationSceneC
            self._DeleteAnimationSceneC.restype = ctypes.c_bool
            self._DeleteAnimationSceneC.argtypes = [ctypes.c_void_p]

            self._GetAnimationCountC = self.dll.GetAnimationCountC
            self._GetAnimationCountC.restype = ctypes.c_size_t
            self._GetAnimationCountC.argtypes = [ctypes.c_void_p]

            self._GetAnimationC = self.dll.GetAnimationC
            self._GetAnimationC.restype = ctypes.c_void_p
            self._GetAnimationC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            # Animation helpers
            self._GetAnimationBlockC = self.dll.GetAnimationBlockC
            self._GetAnimationBlockC.restype = ctypes.c_void_p
            self._GetAnimationBlockC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetAnimationBlockCountC = self.dll.GetAnimationBlockCountC
            self._GetAnimationBlockCountC.restype = ctypes.c_size_t
            self._GetAnimationBlockCountC.argtypes = [ctypes.c_void_p]

            self._GetAnimationTitleC = self.dll.GetAnimationTitleC
            self._GetAnimationTitleC.restype = ctypes.c_char_p
            self._GetAnimationTitleC.argtypes = [ctypes.c_void_p]

            self._GetFrameCountC = self.dll.GetFrameCountC
            self._GetFrameCountC.restype = ctypes.c_size_t
            self._GetFrameCountC.argtypes = [ctypes.c_void_p]

            # Animation block helpers
            self._GetAnimBlockBoneNameC = self.dll.GetAnimBlockBoneNameC
            self._GetAnimBlockBoneNameC.restype = ctypes.c_char_p
            self._GetAnimBlockBoneNameC.argtypes = [ctypes.c_void_p]

            self._GetAnimBlockBoneIndexC = self.dll.GetAnimBlockBoneIndexC
            self._GetAnimBlockBoneIndexC.restype = ctypes.c_int
            self._GetAnimBlockBoneIndexC.argtypes = [ctypes.c_void_p]

            self._GetRotationFromSqC = self.dll.GetRotationFromSqC
            self._GetRotationFromSqC.restype = ctypes.c_void_p
            self._GetRotationFromSqC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetRotationSqSizeC = self.dll.GetRotationSqSizeC
            self._GetRotationSqSizeC.restype = ctypes.c_size_t
            self._GetRotationSqSizeC.argtypes = [ctypes.c_void_p]

            self._GetTranslationFromSqC = self.dll.GetTranslationFromSqC
            self._GetTranslationFromSqC.restype = ctypes.c_void_p
            self._GetTranslationFromSqC.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]

            self._GetTranslationSqSizeC = self.dll.GetTranslationSqSizeC
            self._GetTranslationSqSizeC.restype = ctypes.c_size_t
            self._GetTranslationSqSizeC.argtypes = [ctypes.c_void_p]

            # Animation entry helpers
            self._GetFrameFromRotationEntryC = self.dll.GetFrameFromRotationEntryC
            self._GetFrameFromRotationEntryC.restype = ctypes.c_uint16
            self._GetFrameFromRotationEntryC.argtypes = [ctypes.c_void_p]

            self._GetFrameFromTranslationEntryC = self.dll.GetFrameFromTranslationEntryC
            self._GetFrameFromTranslationEntryC.restype = ctypes.c_uint16
            self._GetFrameFromTranslationEntryC.argtypes = [ctypes.c_void_p]

            self._GetValueFromRotationEntryC = self.dll.GetValueFromRotationEntryC
            self._GetValueFromRotationEntryC.restype = ctypes.c_void_p
            self._GetValueFromRotationEntryC.argtypes = [ctypes.c_void_p]

            self._GetValueFromTranslationEntryC = self.dll.GetValueFromTranslationEntryC
            self._GetValueFromTranslationEntryC.restype = ctypes.c_void_p
            self._GetValueFromTranslationEntryC.argtypes = [ctypes.c_void_p]

        except AttributeError as e:
            print(f"Warning: Some helper functions not available: {e}")

    def _decode_utf8_or_fallback(self, raw_value: Optional[bytes], fallback: str = "") -> str:
        if raw_value is None:
            return fallback
        try:
            return raw_value.decode('utf-8').strip()
        except Exception:
            return fallback

    def _extract_animation_scene_data(self, scene_ptr: ctypes.c_void_p, fallback_name: str) -> Dict[str, Any]:
        """Extract AnimationScene data to Python dictionaries for Blender keyframe application."""
        scene_data = {
            "name": fallback_name,
            "animations": [],
            "max_frame": 0,
        }

        required = [
            '_GetAnimationCountC', '_GetAnimationC', '_GetAnimationBlockCountC', '_GetAnimationBlockC',
            '_GetAnimationTitleC', '_GetAnimBlockBoneNameC', '_GetAnimBlockBoneIndexC',
            '_GetRotationSqSizeC', '_GetRotationFromSqC', '_GetFrameFromRotationEntryC', '_GetValueFromRotationEntryC',
            '_GetTranslationSqSizeC', '_GetTranslationFromSqC', '_GetFrameFromTranslationEntryC', '_GetValueFromTranslationEntryC',
            '_GetQuaternionX', '_GetQuaternionY', '_GetQuaternionZ', '_GetQuaternionW',
            '_GetVector3DX', '_GetVector3DY', '_GetVector3DZ',
        ]
        missing = [name for name in required if not hasattr(self, name)]
        if missing:
            print(f"Animation extraction helpers unavailable in DLL binding: {missing}")
            return scene_data

        try:
            animation_count = int(self._GetAnimationCountC(scene_ptr))
            for animation_index in range(animation_count):
                animation_ptr = self._GetAnimationC(scene_ptr, animation_index, None)
                if not animation_ptr:
                    continue

                animation_title = self._decode_utf8_or_fallback(
                    self._GetAnimationTitleC(animation_ptr),
                    fallback=fallback_name,
                )
                frame_count = int(self._GetFrameCountC(animation_ptr)) if hasattr(self, '_GetFrameCountC') else 0

                animation_data = {
                    "name": animation_title if animation_title else fallback_name,
                    "frame_count": frame_count,
                    "blocks": [],
                }

                block_count = int(self._GetAnimationBlockCountC(animation_ptr))
                for block_index in range(block_count):
                    block_ptr = self._GetAnimationBlockC(animation_ptr, block_index, None)
                    if not block_ptr:
                        continue

                    bone_name = self._decode_utf8_or_fallback(self._GetAnimBlockBoneNameC(block_ptr), fallback="")
                    bone_index = int(self._GetAnimBlockBoneIndexC(block_ptr))

                    rotation_sequence = []
                    rotation_count = int(self._GetRotationSqSizeC(block_ptr))
                    for i in range(rotation_count):
                        rotation_ptr = self._GetRotationFromSqC(block_ptr, i, None)
                        if not rotation_ptr:
                            continue

                        frame = int(self._GetFrameFromRotationEntryC(rotation_ptr))
                        quat_ptr = self._GetValueFromRotationEntryC(rotation_ptr)
                        if not quat_ptr:
                            continue

                        x = float(self._GetQuaternionX(quat_ptr))
                        y = float(self._GetQuaternionY(quat_ptr))
                        z = float(self._GetQuaternionZ(quat_ptr))
                        w = float(self._GetQuaternionW(quat_ptr))
                        rotation_sequence.append({
                            "frame": frame,
                            "x": x,
                            "y": y,
                            "z": z,
                            "w": w,
                        })
                        scene_data["max_frame"] = max(scene_data["max_frame"], frame)

                    translation_sequence = []
                    translation_count = int(self._GetTranslationSqSizeC(block_ptr))
                    for i in range(translation_count):
                        translation_ptr = self._GetTranslationFromSqC(block_ptr, i, None)
                        if not translation_ptr:
                            continue

                        frame = int(self._GetFrameFromTranslationEntryC(translation_ptr))
                        vec_ptr = self._GetValueFromTranslationEntryC(translation_ptr)
                        if not vec_ptr:
                            continue

                        x = float(self._GetVector3DX(vec_ptr))
                        y = float(self._GetVector3DY(vec_ptr))
                        z = float(self._GetVector3DZ(vec_ptr))
                        translation_sequence.append({
                            "frame": frame,
                            "x": x,
                            "y": y,
                            "z": z,
                        })
                        scene_data["max_frame"] = max(scene_data["max_frame"], frame)

                    if rotation_sequence or translation_sequence:
                        animation_data["blocks"].append({
                            "bone_name": bone_name,
                            "bone_index": bone_index,
                            "rotation_sequence": rotation_sequence,
                            "translation_sequence": translation_sequence,
                        })

                if animation_data["blocks"]:
                    scene_data["animations"].append(animation_data)

        except Exception as e:
            print(f"Error extracting animation scene data: {e}")

        return scene_data

    def is_loaded(self) -> bool:
        """Check if the DLL is loaded."""
        return self.loaded and self.dll is not None

    def _extract_rig_bone_data(self, rig_bone_ptr, bone_index, rig_ptr) -> RigBone:
        """Extract bone data from a CALUMI SkeletonBone pointer."""
        bone = RigBone()
        bone.index = bone_index

        try:
            # Get bone name - returns bytes, need to decode as UTF-8
            bone_name_bytes = self._GetSkeletonBoneNameC(rig_bone_ptr)
            if bone_name_bytes:
                try:
                    # Decode from UTF-8 bytes to string
                    decoded_name = bone_name_bytes.decode('utf-8').strip()
                    # Try to get English name if available, otherwise use decoded name
                    bone.bone_name = self._get_english_bone_name(decoded_name)
                except UnicodeDecodeError:
                    bone.bone_name = f"Bone_{bone_index}"  # Fallback for decode errors
            else:
                bone.bone_name = f"Bone_{bone_index}"  # Fallback name

            # Get parent index
            parent_index = self._GetSkeletonBoneParentIndexC(rig_bone_ptr)
            bone.parent_index = parent_index if parent_index is not None else -1

            # Get translation
            pos_ptr = self._GetSkeletonBonePositionC(rig_bone_ptr, False)
            if pos_ptr and pos_ptr != 0:
                try:
                    # Use float versions like sf_animation_io
                    x = self._GetVector3X(pos_ptr)
                    y = self._GetVector3Y(pos_ptr)
                    z = self._GetVector3Z(pos_ptr)
                    # Check for clearly invalid values (NaN, infinity, extremely large values)
                    # Allow small values that might be legitimate bone positions
                    if not (math.isnan(x) or math.isinf(x) or abs(x) > 1e6 or
                            math.isnan(y) or math.isinf(y) or abs(y) > 1e6 or
                            math.isnan(z) or math.isinf(z) or abs(z) > 1e6):
                        bone.translation = (x, y, z)
                        print(f"Bone {bone_index} position: ({x}, {y}, {z})")
                    else:
                        print(f"Bone {bone_index} has invalid position values: ({x}, {y}, {z})")
                        bone.translation = (0.0, 0.0, float(bone_index) * 0.1)  # Fallback
                except Exception as e:
                    print(f"Error extracting position for bone {bone_index}: {e}")
                    bone.translation = (0.0, 0.0, float(bone_index) * 0.1)  # Fallback
            else:
                print(f"Bone {bone_index} has no position data (ptr: {pos_ptr})")
                bone.translation = (0.0, 0.0, float(bone_index) * 0.1)  # Fallback

            # Get rotation
            rot_ptr = self._GetSkeletonBoneRotationC(rig_bone_ptr, False)
            if rot_ptr:
                x = self._GetQuaternionX(rot_ptr)
                y = self._GetQuaternionY(rot_ptr)
                z = self._GetQuaternionZ(rot_ptr)
                w = self._GetQuaternionW(rot_ptr)
                bone.rotation = (x, y, z, w)

        except Exception as e:
            print(f"Error extracting bone data for bone {bone_index}: {e}")
            # Set fallback values
            bone.bone_name = f"Bone_{bone_index}"
            bone.parent_index = -1

        return bone

    def _convert_rig_ptr_to_skel_rig(self, rig_ptr, rig_path) -> SkelRig:
        """Convert a CALUMI SkeletonRig pointer to a SkelRig object."""
        rig = SkelRig()
        rig.name = Path(rig_path).stem

        try:
            bone_count = self._GetSkeletonRigBoneCountC(rig_ptr)

            for i in range(bone_count):
                rig_bone_ptr = self._GetSkeletonBoneC(rig_ptr, i, False)
                if rig_bone_ptr:
                    bone = self._extract_rig_bone_data(rig_bone_ptr, i, rig_ptr)
                    rig.bones.append(bone)

            # Set parent names from indices
            for bone in rig.bones:
                if bone.parent_index is not None and bone.parent_index >= 0 and bone.parent_index < len(rig.bones):
                    bone.parent_name = rig.bones[bone.parent_index].bone_name
                else:
                    bone.parent_name = None

        except Exception as e:
            print(f"Error converting rig pointer to SkelRig: {e}")

        return rig

    def import_rig(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Import a .rig file.

        Args:
            filepath: Path to the .rig file

        Returns:
            Dict with rig data or None if failed
        """
        if not self.is_loaded():
            return None

        try:
            # Call the CALUMI function
            rig_ptr = self._LoadSFBGSSkeletonRigFromFileC(
                ctypes.c_wchar_p(filepath),
                None  # StringContainer* error message container
            )

            if rig_ptr is None:
                print(f"Failed to load rig from {filepath}")
                return None

            # Convert to Python object
            rig = self._convert_rig_ptr_to_skel_rig(rig_ptr, filepath)

            rig_data = {
                "pointer": rig_ptr,
                "filepath": filepath,
                "name": rig.name,
                "rig": rig
            }

            print(f"Successfully loaded rig: {filepath} with {len(rig.bones)} bones")
            return rig_data

        except Exception as e:
            print(f"Error importing rig: {e}")
            return None

    def export_rig(self, rig_data: Dict[str, Any], filepath: str) -> bool:
        """
        Export rig data to .rig file.

        Args:
            rig_data: Rig data dict
            filepath: Output path

        Returns:
            True if successful
        """
        if not self.is_loaded():
            return False

        try:
            rig_ptr = rig_data.get("pointer")
            if rig_ptr is None:
                print("No rig pointer in rig_data - export from Blender armature not yet implemented")
                return False

            success = self._SaveSkeletonRigToSFBGSFormatDirectC(
                rig_ptr,
                ctypes.c_wchar_p(filepath),
                None  # error message container
            )

            if success:
                print(f"Successfully exported rig to {filepath}")
                return True
            else:
                print(f"Failed to export rig to {filepath}")
                return False

        except Exception as e:
            print(f"Error exporting rig: {e}")
            return False

    def import_animation(self, filepath: str, rig_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Import a .af file.

        Args:
            filepath: Path to the .af file
            rig_path: Optional path to matching .rig file (recommended/required by CALUMI scene conversion)

        Returns:
            Dict with animation data or None if failed
        """
        if not self.is_loaded():
            return None

        try:
            paths_to_load = [filepath]
            if rig_path:
                paths_to_load.append(rig_path)

            # Prepare file paths array (const wchar_t**)
            file_paths = (ctypes.c_wchar_p * len(paths_to_load))()
            for i, path in enumerate(paths_to_load):
                file_paths[i] = str(path)

            scene_ptr = self._LoadAnimationSceneFromSFBGSFormatC(
                file_paths,
                len(paths_to_load),
                None  # StringContainer* error message container
            )

            if scene_ptr is None:
                print(f"Failed to load animation from {filepath}")
                if rig_path is None:
                    print("No rig path provided. CALUMI LoadAnimationSceneFromSFBGSFormatC requires a .rig entry in the file list for scene conversion.")
                else:
                    print(f"Attempted rig reference path: {rig_path}")
                return None

            scene_data = self._extract_animation_scene_data(scene_ptr, Path(filepath).stem)

            # Free scene memory once extracted.
            if hasattr(self, '_DeleteAnimationSceneC'):
                try:
                    self._DeleteAnimationSceneC(scene_ptr)
                except Exception as cleanup_error:
                    print(f"Warning: Failed to free AnimationScene pointer: {cleanup_error}")

            anim_data = {
                "pointer": None,
                "filepath": filepath,
                "name": Path(filepath).stem,
                "rig_path": rig_path,
                "scene": scene_data,
                "animations": scene_data.get("animations", []),
                "max_frame": scene_data.get("max_frame", 0),
            }

            print(
                f"Successfully loaded animation: {filepath} "
                f"(animations={len(scene_data.get('animations', []))}, max_frame={scene_data.get('max_frame', 0)})"
            )
            return anim_data

        except Exception as e:
            print(f"Error importing animation: {e}")
            return None

    def export_animation(self, anim_data: Dict[str, Any], filepath: str) -> bool:
        """
        Export animation data to .af file.

        Args:
            anim_data: Animation data dict
            filepath: Output path

        Returns:
            True if successful
        """
        if not self.is_loaded():
            return False

        try:
            anim_ptr = anim_data.get("pointer")
            if anim_ptr is None:
                print("No animation pointer in anim_data - export from Blender animation not yet implemented")
                return False

            rig_path = anim_data.get("rig_path")
            success = self._SaveAnimationToSFBGSFormatWithExistingRigDirectC(
                anim_ptr,
                ctypes.c_wchar_p(filepath),
                ctypes.c_wchar_p(rig_path) if rig_path else None,
                None  # error message container
            )

            if success:
                print(f"Successfully exported animation to {filepath}")
                return True
            else:
                print(f"Failed to export animation to {filepath}")
                return False

        except Exception as e:
            print(f"Error exporting animation: {e}")
            return False


# Global adapter instance
_adapter = None

def get_adapter() -> CALUMIAdapter:
    """Get the global CALUMI adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = CALUMIAdapter()
    return _adapter