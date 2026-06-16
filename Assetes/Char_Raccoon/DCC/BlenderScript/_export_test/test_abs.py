import bpy, sys, traceback
from mathutils import Matrix
ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context


def nperm(Q):
    """Permutation signee la plus proche de la 3x3 de Q."""
    M = Q.to_3x3()
    P = [[0.0] * 3 for _ in range(3)]
    for _, i, j in sorted(((abs(M[i][j]), i, j) for i in range(3) for j in range(3)), reverse=True):
        if any(P[i][k] for k in range(3)) or any(P[k][j] for k in range(3)):
            continue
        P[i][j] = 1.0 if M[i][j] >= 0 else -1.0
    m = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            m[i][j] = P[i][j]
    return m


def shear(M):
    _, q, s = M.decompose()
    rec = q.to_matrix() @ Matrix.Diagonal(s)
    M3 = M.to_3x3()
    return max(abs(M3[i][j] - rec[i][j]) for i in range(3) for j in range(3))


def rot_only(M):
    _, q, _ = M.decompose()
    return q.to_matrix().to_4x4()


try:
    import blender_unity_anim as bua
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core(); sdc.clear_rig_data("Def")
    ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    from AnimExport import core as ac; ac.reload_core()
    from AnimExport.core import exporter
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    basis = bua.load_basis(ROOT + "/AnimExport/core/unity_basis.json")

    ctx.scene.frame_set(1); ctx.view_layer.update()
    ev0 = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    Bbind = {pb.name: bua.bone_local(ev0, ev0.pose.bones[pb.name])
             for pb in defr.pose.bones if pb.name in basis}

    H = {n: nperm(e.Q) for n, e in basis.items()}
    A1 = {n: basis[n].Ubind @ H[n].inverted() @ Bbind[n].inverted() for n in basis}
    A2 = {n: rot_only(A1[n]) for n in basis}

    for F in (1, 24):
        ctx.scene.frame_set(F); ctx.view_layer.update()
        ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
        sh_d, sh_1, sh_2, bindmiss = [], [], [], []
        for n, e in basis.items():
            bl = bua.bone_local(ev, ev.pose.bones[n])
            dB = e.Bbinv @ bl; dB.translation = dB.translation * e.s
            Ld = e.Ubind @ e.Q.inverted() @ dB @ e.Q
            L1 = A1[n] @ bl @ H[n]
            L2 = A2[n] @ bl @ H[n]
            sh_d.append(shear(Ld)); sh_1.append(shear(L1)); sh_2.append(shear(L2))
            if F == 1:
                bindmiss.append(max(abs(L1[i][j] - e.Ubind[i][j]) for i in range(4) for j in range(4)))
        print(f"frame {F}: shear max  delta={max(sh_d):.3f} | abs-v1={max(sh_1):.3f} | abs-v2(A=rot)={max(sh_2):.3f}")
        if F == 1 and bindmiss:
            print(f"   (v1 reconstruit le bind Unity a {max(bindmiss):.2e})")
except Exception:
    traceback.print_exc()
