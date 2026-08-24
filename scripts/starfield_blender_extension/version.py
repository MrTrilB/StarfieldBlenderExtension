import addon_utils

class Version:
    def __init__(self, version: tuple[int, int, int] = (0,0,0)):
        self.version = version

    def __str__(self):
        return f"{self.version[0]}.{self.version[1]}.{self.version[2]}"

    def __eq__(self, other):
        return self.version == other.version

    def __lt__(self, other):
        for i in range(3):
            if self.version[i] < other.version[i]:
                return True
        return False

    def __gt__(self, other):
        return not self.__eq__(other) and not self.__lt__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)
    
    def as_tuple(self):
        return self.version
    
    def as_str(self):
        return str(self)
    
    def as_int(self):
        return self.version[0] * 10000 + self.version[1] * 100 + self.version[2]
    
def make_version(version: str) -> Version:
    v = Version()
    v.version = tuple(map(int, version.split('.')))
    return v

__extra_compatible_dict__ = {
    # The physics editor is now versioned in lockstep with the main addon, so
    # 1.6.0 pairs with 1.6.0. The older 0.17.0 stays listed because an existing
    # install may still have it side by side.
    (1, 6, 0): {'tool_physics_editor': [(1, 6, 0), (0, 17, 0)]},
    (1, 5, 0): {'tool_physics_editor': [(0, 17, 0)]},
    (1, 4, 0): {'tool_physics_editor': [(0, 17, 0)]},
    (1, 3, 0): {'tool_physics_editor': [(0, 17, 0)]},
    (1, 2, 0): {'tool_physics_editor': [(0, 17, 0)]},
    (1, 1, 0): {'tool_physics_editor': [(0, 17, 0)]},
    (1, 0, 0): {'tool_physics_editor': [(0, 17, 0)]},
}

def check_compatibility(submodule_name: str, raise_if_not_found: bool = False) -> bool:
    import os
    main_name = 'starfield_blender_extension'
    _, enabled = addon_utils.check(main_name)
    if not enabled:
        if raise_if_not_found:
            raise Exception(f"Main module '{main_name}' not enabled.")
        return False

    # A submodule can arrive either way, so try both rather than assuming one.
    # build_temp_distribution copies tool_physics_editor *beside* the main addon,
    # so treating it as bundled-only made this return False for a normal install
    # and NifIO then dropped physics data with only a warning.
    mods = addon_utils.modules()
    main_plugin_version = None
    submodule_version = None
    main_mod = None
    for mod in mods:
        if mod.__name__ == main_name:
            main_mod = mod
            main_plugin_version = Version(mod.bl_info['version'])
        elif mod.__name__ == submodule_name:
            submodule_version = Version(mod.bl_info['version'])

    # Installed as its own addon: compare versions.
    _, submodule_enabled = addon_utils.check(submodule_name)
    if submodule_enabled and submodule_version is not None and main_plugin_version is not None:
        return compare_versions(
            main_plugin_version.as_str(), submodule_version.as_str(), submodule_name
        )

    # Bundled inside the main addon: presence of the directory is enough, since
    # it ships and versions with the addon.
    if main_mod and getattr(main_mod, '__file__', None):
        addon_dir = os.path.dirname(main_mod.__file__)
        if os.path.exists(os.path.join(addon_dir, submodule_name)):
            return True

    if raise_if_not_found:
        raise Exception(
            f"Submodule '{submodule_name}' is neither enabled as an addon nor bundled in {main_name}."
        )
    return False
        
import functools

@functools.lru_cache(maxsize=16)
def compare_versions(main_version_str: str, sub_module_version_str: str, sub_module_name: str) -> bool:
    '''
        return True if the sub_module_version is compatible with the main_version
    '''
    main_version = make_version(main_version_str).as_tuple()
    sub_module_version = make_version(sub_module_version_str).as_tuple()

    # Matching versions are compatible by definition. Without this the table has
    # to gain an entry on every release, and a missed bump silently disables
    # physics: build_temp_distribution installs tool_physics_editor beside the
    # main addon rather than inside it, so the bundled short-circuit in
    # check_compatibility does not apply and this comparison decides. NifIO then
    # drops physics data with only a warning, which is easy to miss.
    if sub_module_version == main_version:
        return True

    if main_version in __extra_compatible_dict__:
        extra_compatible_versions = __extra_compatible_dict__[main_version]
        if sub_module_name in extra_compatible_versions:
            return sub_module_version in extra_compatible_versions[sub_module_name]
        
    return False
        

__plugin_version__ = Version((0, 1, 0))