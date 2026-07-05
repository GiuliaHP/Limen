"""
Adaptateur → module générique `blender_unity_anim` (conversion analytique).

Le ctrl porte l'action, le Def suit par contraintes ; on délègue l'écriture du
.anim au writer générique sur le Def évalué.
"""

import blender_unity_anim as bua

from . import exporter


def write_anim(filepath, clip_name, context, ctrl_obj, def_obj, action, rng):
    """Bake d'un clip en .anim Unity (conversion analytique, sans FBX).

    IK_Stretch : son défaut est réglé à 0 dans le rig (disable_ik_stretch.py),
    donc _reset_to_default le remet à 0 → pas de stretch (scale non-uniforme
    inexportable). Rien à forcer ici.
    """
    start, end = rng
    scene = context.scene
    scene.frame_start = start
    scene.frame_end = end

    exporter._reset_to_default(ctrl_obj)
    exporter._assign_action(ctrl_obj, action)
    context.view_layer.update()

    return bua.write_anim(
        filepath, clip_name, context,
        deform_armature=def_obj,
        frames=range(start, end + 1),
        root_name="",   # os enfants directs de l'Animator (loader custom)
    )
