"""
Conversion d'espace Blender → Unity, ANALYTIQUE (méthode taniwha/io_object_mu).

C'est le changement de base M = swap(x,z,y) (réflexion Y↔Z : Blender RH/Z-up →
Unity LH/Y-up), prouvé exact (`_export_test/test_basis_change.py`). Appliquée de
façon IDENTIQUE au modèle (os bind + verts, via l'importeur custom) et aux courbes
.anim, elle préserve la géométrie PAR CONSTRUCTION — aucune calibration, aucun FBX.

    pos   : Unity(x,y,z)   = Blender(x, z, y)
    quat  : Unity(w,x,y,z) = Blender(w, -x, -z, -y)
    scale : Unity(x,y,z)   = Blender(x, z, y)
"""

from mathutils import Vector, Quaternion


def pos_to_unity(v):
    return (v.x, v.z, v.y)


def quat_to_unity(q):
    """q : mathutils.Quaternion (w,x,y,z) → tuple Unity (x,y,z,w)."""
    return (-q.x, -q.z, -q.y, q.w)


def scale_to_unity(s):
    return (s.x, s.z, s.y)


def local_to_unity(matrix):
    """Matrice locale Blender → (pos[3], quat_xyzw[4], scale[3]) Unity."""
    loc, q, s = matrix.decompose()
    return pos_to_unity(loc), quat_to_unity(q), scale_to_unity(s)
