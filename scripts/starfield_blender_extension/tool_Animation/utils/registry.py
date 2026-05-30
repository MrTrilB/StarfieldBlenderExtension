import os
import shutil


def sanitize_name(value: str) -> str:
    value = value.strip().replace(" ", "_")
    return "".join(ch for ch in value if ch.isalnum() or ch == "_")


def get_default_registry_dir() -> str:
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, "assets", "rigs")


def ensure_registry_dir(path: str) -> str:
    out = path if path else get_default_registry_dir()
    os.makedirs(out, exist_ok=True)
    return out


def list_registered_rigs(registry_dir: str):
    folder = ensure_registry_dir(registry_dir)
    items = []

    try:
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith('.rig'):
                continue
            rig_name = name[:-4]
            items.append((rig_name, rig_name, f"Registered rig: {name}"))
    except OSError:
        pass

    if not items:
        items.append(("NONE", "NONE", "No registered rigs found"))

    return items


def register_rig_file(source_file: str, registry_dir: str, rig_name: str) -> str:
    folder = ensure_registry_dir(registry_dir)
    destination = os.path.join(folder, f"{rig_name}.rig")
    shutil.copyfile(source_file, destination)
    return destination


def get_registered_rig_path(registry_dir: str, rig_name: str):
    """Get full path to a registered rig file if it exists."""
    if not rig_name or rig_name == "NONE":
        return None

    folder = ensure_registry_dir(registry_dir)
    candidate = os.path.join(folder, f"{sanitize_name(rig_name)}.rig")
    if os.path.isfile(candidate):
        return candidate

    return None
