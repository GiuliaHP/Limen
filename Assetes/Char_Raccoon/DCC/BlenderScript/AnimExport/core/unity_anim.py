"""
Adaptateur Raccoon → module générique `blender_unity_anim`.

Toute la logique de sérialisation .anim (retarget, calibration, YAML) vit
désormais dans le paquet autonome `blender_unity_anim` (à la racine de
BlenderScript), réutilisable pour n'importe quelle armature.

Ce fichier ne contient plus que la spécificité Raccoon :
 - la pose vient du CtrlRig (action assignée au ctrl, le Def suit par contraintes)
 - la basis vit dans AnimExport/core/unity_basis.json

⚠ Si le squelette change : re-générer unity_basis.json via
   _export_test/calibrate_basis.py (calibration générique Kabsch).
"""

import blender_unity_anim as bua

from . import exporter


def write_anim(filepath, clip_name, context, ctrl_obj, def_obj, action, rng):
    """Bake d'un clip Raccoon en .anim Unity (conversion analytique, sans FBX).

    Le CtrlRig porte l'action ; le Def la suit par contraintes. On délègue
    l'écriture au writer générique sur le Def évalué. Le nœud racine Unity est
    nommé comme l'armature (l'importeur custom fait pareil).
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
