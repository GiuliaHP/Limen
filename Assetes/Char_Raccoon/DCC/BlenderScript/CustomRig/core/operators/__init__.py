import bpy
import importlib
from . import visibility

importlib.reload(visibility)

classes = (
    visibility.ARMATURE_OT_toggle_skeleton_raccoon,
)

def register():
    for cls in classes:
        # Hack TD pour nettoyer la RAM
        if hasattr(bpy.types, cls.__name__):
            try: bpy.utils.unregister_class(getattr(bpy.types, cls.__name__))
            except Exception: pass
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass