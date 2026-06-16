"""
blender_unity_anim — sérialisation directe Blender → Unity .anim, ANALYTIQUE.

Conversion d'espace par changement de base M = swap(x,z,y) (méthode
taniwha/io_object_mu), appliquée IDENTIQUEMENT au modèle (importeur custom Unity)
et aux courbes .anim → géométrie préservée par construction. AUCUNE calibration,
AUCUN FBX (le modèle entre dans Unity via l'importeur custom, pas via FBX).

    pos   : Unity(x,y,z)   = Blender(x, z, y)
    quat  : Unity(w,x,y,z) = Blender(w, -x, -z, -y)   (cf. convert.py)
    scale : Unity(x,y,z)   = Blender(x, z, y)

EXPORT (`exporter.write_anim`) : par os, pose locale Blender → conversion → TRS
Unity verbatim. Unités = mètres (l'importeur n'applique pas de ×100).

API publique
------------
    from blender_unity_anim import write_anim, convert, bone_local
    from blender_unity_anim import dump_blender_locals, trs_to_mat, bone_path
"""

from .retarget import bone_local
from . import convert
from .exporter import write_anim, skinned_blendshape_meshes
from .model_export import export_model
from .bone_io import dump_blender_locals, bone_path, trs_to_mat


def reload():
    """Recharge tous les sous-modules (pratique en console Blender)."""
    import importlib
    from . import convert, retarget, yaml_clip, exporter, model_export, bone_io
    for m in (convert, retarget, yaml_clip, exporter, model_export, bone_io):
        importlib.reload(m)


__all__ = [
    "convert",
    "bone_local",
    "write_anim", "skinned_blendshape_meshes",
    "export_model",
    "dump_blender_locals", "bone_path", "trs_to_mat",
    "reload",
]
