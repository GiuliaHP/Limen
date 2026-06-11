import bpy
import importlib
from . import visibility
from . import rigify_snap_runtime
from . import ikfk_snap

importlib.reload(visibility)
importlib.reload(rigify_snap_runtime)
importlib.reload(ikfk_snap)

classes = (
    visibility.ARMATURE_OT_toggle_skeleton_raccoon,
    # Moteur de snap Rigify embarqué (opérateurs internes)
    *rigify_snap_runtime.classes,
    # Wrapper haut niveau appelé par l'UI
    ikfk_snap.POSE_OT_raccoon_ikfk_snap,
)