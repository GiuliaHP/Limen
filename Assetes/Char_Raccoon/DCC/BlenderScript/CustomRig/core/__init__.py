import bpy
import importlib

from . import constants
from . import operators
from . import ui


def reload_core():
    """Recharge les sous-modules (TD : nettoie la RAM entre deux runs)."""
    importlib.reload(constants)
    importlib.reload(operators)
    importlib.reload(ui)


def _all_classes():
    # Opérateurs puis UI
    return (*operators.classes, *ui.classes)


def register():
    ui.register_props()
    for cls in _all_classes():
        # Hack TD : on désenregistre une éventuelle ancienne version
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_all_classes()):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass
    ui.unregister_props()
