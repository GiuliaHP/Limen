"""
Prouve que la conversion io_object_mu (pos (x,z,y), quat (w,-x,-z,-y), scale (x,z,y))
est EXACTEMENT le changement de base M = swap(x,z,y) appliqué par conjugaison.

Si Lu_formule == M @ L_blender @ M^-1 pour tous les os, alors :
  - convertir TOUT (verts, os, anim) par cette formule = exprimer la scène dans
    la base Unity → skinning/géométrie préservés PAR CONSTRUCTION.
  - aucune calibration, aucun FBX : le modèle (importeur custom) et le .anim
    parlent le même langage.
"""
import bpy, sys
from mathutils import Matrix, Quaternion, Vector
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")
ctx = bpy.context

# M : changement de base Blender(RH,Z-up) -> Unity(LH,Y-up) = swap Y<->Z (réflexion)
M = Matrix(((1, 0, 0, 0),
            (0, 0, 1, 0),
            (0, 1, 0, 0),
            (0, 0, 0, 1)))
Minv = M.inverted()


def conv_formula(L):
    """Conversion io_object_mu par TRS."""
    loc, q, s = L.decompose()
    pu = Vector((loc.x, loc.z, loc.y))
    qu = Quaternion((q.w, -q.x, -q.z, -q.y))
    su = Vector((s.x, s.z, s.y))
    m = qu.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= su[j]
    m.translation = pu
    return m


def run():
    defr = bpy.data.objects["Def"]
    ctx.scene.frame_set(0); ctx.view_layer.update()
    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())

    worst = 0.0; wb = ""
    for pb in ev.pose.bones:
        L = (pb.parent.matrix.inverted() @ pb.matrix) if pb.parent else pb.matrix.copy()
        Lf = conv_formula(L)
        Lc = M @ L @ Minv
        e = max(abs(Lf[i][j] - Lc[i][j]) for i in range(4) for j in range(4))
        if e > worst:
            worst = e; wb = pb.name
    print(f"max |formule - M·L·M⁻¹| = {worst:.2e}  ({wb})")
    print("  -> si ~0 : la conversion io_object_mu EST le changement de base M.")
    print("     Pipeline modèle+anim correct par construction, sans calibration ni FBX.")


run()
