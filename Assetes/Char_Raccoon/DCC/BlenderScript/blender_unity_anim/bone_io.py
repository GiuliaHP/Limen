"""Échantillonnage Blender et helpers de matrices (côté calibration + export).

`dump_blender_locals` lit l'armature de déformation ÉVALUÉE à chaque frame —
peu importe comment la pose est produite (action directe, contraintes, drivers).
L'appelant pose la scène (assigne l'action où il veut) AVANT d'appeler.
"""

import bpy

from mathutils import Matrix, Vector, Quaternion

from .retarget import bone_local


def bone_path(armature, bone_name, root=None):
    """Chemin de binding Unity d'un os : '<root>/<chaîne hiérarchique>'.

    root par défaut = nom de l'objet armature (= nom du nœud racine côté Unity).
    """
    root = root if root is not None else armature.name
    bones = {b.name: b for b in armature.data.bones}
    parts = []
    cur = bones.get(bone_name)
    while cur:
        parts.append(cur.name)
        cur = cur.parent
    parts.reverse()
    return f"{root}/" + "/".join(parts)


def dump_blender_locals(armature, context, frames):
    """{frame: {bone: Matrix locale}} pour l'armature évaluée aux frames données.

    `frames` : itérable d'entiers. Renvoie aussi la frame telle quelle comme clé.
    """
    out = {}
    for fr in frames:
        context.scene.frame_set(fr)
        context.view_layer.update()
        dg = context.evaluated_depsgraph_get()
        ev = armature.evaluated_get(dg)
        out[fr] = {pb.name: bone_local(ev, ev.pose.bones[pb.name])
                   for pb in ev.pose.bones}
    return out


def trs_to_mat(d):
    """Dict {pos, quat (w,x,y,z), scale} → Matrix 4x4 (format des dumps Unity)."""
    q = Quaternion(d["quat"])
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"])
    return m
