---
name: starfield-blender-addon-instructions
description: "Always-on instructions for the Starfield Blender addon project. Use when: working on Blender addon code, UI panels, operators, imports, structure, packaging. Ensures unified single extension, proper UI organization, and follows ReleaseTemplate for distribution."
---

# Starfield Blender Addon Instructions

## Project Overview
This is a single unified Blender addon for Starfield modding. **Do not create or suggest separate extensions** - everything must be integrated into one addon through `scripts/Starfield_Blender_Extension/`.

## Code Structure and Organization
- **Primary Addon Location**: All code belongs in `scripts/Starfield_Blender_Extension/`.
- **Subfolders**:
  - `ui/`: All UI panels, menus, and interface elements.
  - `operators/`: All operator classes for actions.
  - `types/`: Data type definitions and properties.
## Project Overview
This is a single unified Blender addon for Starfield modding. **Do not create or suggest separate extensions** - everything must be integrated into one addon through `scripts/starfield_blender_extension/`.

## Code Structure and Organization
- **Primary Addon Location**: All code belongs in `scripts/starfield_blender_extension/`.
- **Subfolders**:
  - `ui/`: All UI panels, menus, and interface elements.
  - `operators/`: All operator classes for actions.
  - `types/`: Data type definitions and properties.
  - `utils/`: Utility functions and helpers.
- **Main Entry Point**: `__init__.py` registers all components.
- **Avoid Duplication**: Do not create parallel structures like `Starfield_Blender_Extension/` or separate addons.

## Import Rules
- Use **relative imports** only: `from .ui import MyPanel`, `from ..utils import helper`.
- No absolute imports from outside the addon.
- Ensure `__init__.py` files in subfolders for package imports.

## UI Panel Management
- All UI elements in `ui/` folder.
- Panels must be properly categorized (use `bl_category = "BGS Starfield"` for sidebar N-panels where applicable).
- Use consistent naming: `ExportMaterialPanel`, `BoneRegionsPanel`.
- Register/unregister in `__init__.py`.
- Ensure panels show in the correct areas:
  - Panels targeting the Properties window: use `bl_space_type = 'PROPERTIES'` and `bl_region_type = 'WINDOW'`. Do NOT use `bl_category` for Properties panels.
  - Panels targeting the N-panel (sidebar): use `bl_space_type = 'VIEW_3D'`, `bl_region_type = 'UI'`, and set `bl_category = "BGS Starfield"`.

## Operators and Types
- Operators in `operators/` with clear names like `ExportMeshOperator`.
- Types in `types/` for properties and data structures.
- Register all in `__init__.py`.

## Distribution and Packaging
- Follow `SFGBDocs/ReleaseTemplate/` exactly for packaging.
- Output to `release_packages/` or `release_packages_corrected/` as appropriate.
- Ensure the distribution ZIP contains the single unified addon and required runtime files from the ReleaseTemplate.
- When making changes to individual elements, compile the extension into `temp_check_dist/starfield_blender_extension` for testing.
- Copy the reorganized addon from `scripts/starfield_blender_extension/` to `temp_check_dist/starfield_blender_extension/` when assembling test distributions.
- Include necessary assets and DLLs from the ReleaseTemplate (`Assets/`, `3rdparty/`, `MeshConverter.dll`, etc.).

## Building and Testing
- The extension is composed of Python scripts plus native runtime artifacts and helper tools.
- `build_tools/build_temp_distribution.py` builds `temp_check_dist/starfield_blender_extension` and validates runtime files.
- The native `MeshConverter` C++ project must be compiled separately into `MeshConverter.dll` when a local build is required.

## Validation and Testing
- After changes, run Blender to test addon loading and UI visibility.
- Use `test_addon_load.py` or the `Build Temp Distribution` tasks to validate import and registration.

## Commit Rules
- Only commit when explicitly instructed by the user.
- Use descriptive messages for changes.

## Common Pitfalls to Avoid
- Do not suggest or create separate extensions/addons.
- Keep UI elements unified and identifiable.
- Follow the ReleaseTemplate for all distributions.

## Examples

### Adding a New UI Panel (Properties window)
```python
# In ui/new_panel.py
import bpy

class NewPanel(bpy.types.Panel):
    bl_label = "New Panel"
    bl_idname = "BGS_PT_new_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        layout.label(text="New Panel Content")
```

### Adding a New UI Panel (N-panel / Sidebar)
```python
# In ui/sidebar_panel.py
import bpy

class SidebarPanel(bpy.types.Panel):
    bl_label = "Sidebar Panel"
    bl_idname = "BGS_PT_sidebar_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BGS Starfield"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Sidebar Panel Content")
```

### Relative Import
```python
# In operators/export_ops.py
from ..utils.blender_utils import get_preferences
```