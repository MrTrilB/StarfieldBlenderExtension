# Starfield Blender Extension (MeshConverter)

Starfield Blender Extension is a unified Blender toolkit for Starfield modding that combines mesh, NIF, material, collision, animation, morph, and Havok-related workflows into one extension.

## Introduction

This project is designed to streamline Starfield asset authoring in Blender 5.0+.
Instead of juggling multiple separate add-ons, Starfield Blender Extension provides an integrated workflow for importing, editing, and exporting Starfield-ready content.

It includes and unifies functionality originally developed across multiple Starfield-focused Blender toolsets, while preserving compatibility with existing modding workflows.

## Main Features

- Unified Starfield content pipeline in one extension
- NIF import/export support
- `.mesh` import/export support
- Morph workflow and export support
- Starfield material workflow support
- Collision authoring tools
	- Collider creation/editing
	- Collision layers (including `Static`, `Anim Static`, etc.)
	- Rigidbody and constraint controls
- Havok-related integration and debug visualization
- Skeleton matching/armature import assistance
- Batch import support (including file-list workflow)
- Export configurations for static, animated, outfit, weapon, and related asset types

## Installation Instructions

1. Download the latest release package from this repository.
2. Open Blender and go to **Edit -> Preferences -> Add-ons**.
3. Click **Install...** and select the extension ZIP.
4. Enable **Starfield Blender Extension**.
5. Configure paths in the add-on panel:
	 - **Export Folder**
	 - **Assets Folder** (point this to extracted Starfield loose files, especially meshes)
6. (Optional but recommended) Use the built-in recommended scale/units action before export.
7. Restart Blender if needed and verify the **BGS Starfield** panel is visible.

You can also follow this setup video:
https://www.youtube.com/watch?v=YuuFkJNWDCU

## Requirements

### Runtime Requirements

- Blender **5.0+**
- Access to Starfield loose asset files for full import/material path resolution
- **Export BSFBX** (collider / rigidbody FBX for AssetWatcher): the official Skyrim / Creation Kit **BGS FBX Exporter** addon (`io_scene_bsfbx_skyrim`). Bethesda did not ship a public Starfield-named BSFBX Blender addon; this extension calls `bpy.ops.export_scene.bsfbx_skyrim`. Install and enable that addon, then use **Export BSFBX** as usual.

### Build/Developer Dependencies

- JSON library for C++: https://github.com/nlohmann/json
- DirectXMesh geometry processing library: https://github.com/microsoft/DirectXMesh
- Eigen library for linear algebra: https://eigen.tuxfamily.org/index.php?title=Main_Page
- Miniball library for bounding sphere computation: https://github.com/hbf/miniball

## Discord Community

- https://discord.gg/TZ2Fvb7EQg (permanent access)
- https://discord.gg/dUuUcJ6G8t (temporary access)

## Mod Page

https://www.nexusmods.com/starfield/mods/4360

## Shoutouts

Huge thanks to the developers and teams whose work made this unified extension possible:

- **SesamePaste** - core Starfield Geometry Bridge / MeshConverter work and foundation.
- **Deveris** - major development and integration contributions to the unified extension.
- **Bethesda Game Studios** - original official tool foundations and reference implementations.
- **Zenimax Media / original BGS tooling contributors** - foundational framework contributions.

## Credits and Attributions

This extension incorporates code and functionality from the following sources:

### io_starfield_havokphysics

- **Source**: Bethesda Game Studios' official Starfield Art Tools for 3dsMax
- **Original Author**: Bethesda Game Studios
- **License**: Copyright (C) Bethesda Game Studios. Used with permission for modding purposes.
- **Description**: HKX physics export functionality adapted from the official 3dsMax tools for use in Blender.
- **Integration**: Ported as `tool_havokphysics` module within the Starfield Blender Extension.

## Terms of Use

- Starfield Blender Extension is an open-source program meant for ***everyone***. You are free to use it within the repository license and applicable law.
- This extension carries forward the original Starfield Geometry Bridge author’s intent: keep the toolchain open, transparent, and community-friendly.
- If you use this extension in ***paywalled mods***, you **must clearly disclose** that reverse-engineered tools were used in the asset pipeline.
- When distributing content made with this extension, you should preserve attribution to the original tool authors and contributors where applicable.