"""
Harnais de validation Blender-only (pas de round-trip FBX).

Skinning manuel (Linear Blend Skinning) pour isoler l'erreur D'OS de l'erreur de
blendshape, sur Test 1 et Test 2. Compare, par vertex, plusieurs poses d'os :

  TRUE   : os Blender vrais (W_b) — la cible (skin seul, sans blendshape)
  PARSER : os passes par mon retarget actuel puis round-trip TRS (delta+Q)
  FLOOR  : meilleure approximation TRS possible = simulation de la hierarchie
           Unity (chaque local = closest-TRS, scale herite en plein).
           AUCUNE formule ne bat ce plancher.

LBS : v' = Σ_b w_b · (W_b · Bind_b^-1) · v0   (v0 = vertex au repos)
Bind_b = matrice MONDE de l'os au repos (frame du bind) ; W_b = matrice MONDE animee.
On travaille en espace armature (object space du Def), suffisant pour comparer.
"""

import bpy
import sys
from mathutils import Matrix

ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context

MESH = "MSH_Racoon_Body"
BIND_FRAME = 1            # le bind FBX = pose frame 1 (etabli)
TEST_FRAMES = {"Test 1": [10, 20], "Test 2": [12, 24]}


def recompose(L):
    loc, q, sc = L.decompose()
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= sc[j]
    m.translation = loc
    return m


def world_bones(defr):
    """{bone: matrice monde (espace armature) evaluee maintenant}."""
    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    return {pb.name: pb.matrix.copy() for pb in ev.pose.bones}


def trs_floor(defr, Wtarget):
    """Simule la hierarchie Unity : chaque local ramene a son closest-TRS,
    puis monde reconstruit avec heritage de scale complet. = plancher TRS."""
    bones = defr.data.bones
    order = sorted(Wtarget, key=lambda n: len(_chain(bones, n)))
    Wu = {}
    for n in order:
        b = bones[n]
        par = b.parent.name if (b.parent and b.parent.name in Wtarget) else None
        if par:
            local = Wu[par].inverted() @ Wtarget[n]
            Wu[n] = Wu[par] @ recompose(local)
        else:
            Wu[n] = recompose(Wtarget[n])
    return Wu


def _chain(bones, n):
    parts = []
    cur = bones[n]
    while cur:
        parts.append(cur.name)
        cur = cur.parent
    return parts


def parser_bones(defr, basis, Wbind_blender):
    """Os passes par mon retarget (delta+Q) + round-trip TRS, ramenes en monde
    armature Blender pour skinning. On rebuild le monde Unity (TRS chain) puis on
    mappe Unity->Blender via la relation de bind par os."""
    import blender_unity_anim as bua
    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    # local Unity (TRS round-trip) par os
    Lu = {}
    for pb in defr.pose.bones:
        if pb.name not in basis:
            continue
        e = basis[pb.name]
        bl = bua.bone_local(ev, ev.pose.bones[pb.name])
        L = bua.retarget_local(bl, e)
        Lu[pb.name] = recompose(L)        # ce que le .anim stocke vraiment
    # monde Unity par chaine
    bones = defr.data.bones
    order = sorted(Lu, key=lambda n: len(_chain(bones, n)))
    Wu = {}
    for n in order:
        par = bones[n].parent.name if (bones[n].parent and bones[n].parent.name in Lu) else None
        Wu[n] = (Wu[par] @ Lu[n]) if par else Lu[n]
    # mapping Unity->Blender : au bind, Wu_bind[n] correspond a Wbind_blender[n].
    # transform constant C_n = Wbind_blender[n] @ Wu_bind[n]^-1 (en supposant rigide-ish)
    return Wu  # on calcule le mapping a part (besoin du Wu au bind)


def lbs_positions(mesh_obj, defr, Wmap, Bindinv, verts0, vgroups):
    """Positions LBS pour un set de matrices monde Wmap (espace armature)."""
    M = defr.matrix_world
    out = []
    for vi, v0 in enumerate(verts0):
        acc = None
        wsum = 0.0
        for gname, w in vgroups[vi]:
            if gname not in Wmap or gname not in Bindinv:
                continue
            skin = Wmap[gname] @ Bindinv[gname]
            p = skin @ v0
            acc = p * w if acc is None else acc + p * w
            wsum += w
        out.append((acc / wsum) if (acc and wsum > 1e-6) else v0)
    return out


def run():
    import blender_unity_anim as bua
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core(); sdc.clear_rig_data("Def")
    ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    from AnimExport import core as ac; ac.reload_core()
    from AnimExport.core import exporter
    basis = bua.load_basis(ROOT + "/AnimExport/core/unity_basis.json")
    mesh = bpy.data.objects[MESH]

    # rest verts (object space mesh) + groupes de poids
    me = mesh.data
    vgroups_names = {g.index: g.name for g in mesh.vertex_groups}
    verts0 = [v.co.to_4d() for v in me.vertices]
    vgroups = [[(vgroups_names[g.group], g.weight) for g in v.groups
                if g.group in vgroups_names] for v in me.vertices]
    # mesh->armature : on skinne en espace armature, donc v0 doit y etre.
    mesh_to_arm = defr.matrix_world.inverted() @ mesh.matrix_world
    verts0 = [mesh_to_arm @ v for v in verts0]

    for action_name, frames in TEST_FRAMES.items():
        exporter._reset_to_default(ctrl)
        exporter._assign_action(ctrl, bpy.data.actions[action_name])

        # bind (frame 1) : matrices monde os Blender + Unity-parser
        ctx.scene.frame_set(BIND_FRAME); ctx.view_layer.update()
        Wbind = world_bones(defr)
        Bindinv = {n: Wbind[n].inverted() for n in Wbind}
        WUbind = parser_bones(defr, basis, Wbind)   # monde Unity au bind
        Cmap = {n: Wbind[n] @ WUbind[n].inverted() for n in WUbind}  # Unity->Blender

        print(f"\n========== {action_name} ==========")
        for F in frames:
            ctx.scene.frame_set(F); ctx.view_layer.update()
            Wtrue = world_bones(defr)
            Wfloor = trs_floor(defr, Wtrue)
            WUparser = parser_bones(defr, basis, Wbind)
            Wparser = {n: Cmap[n] @ WUparser[n] for n in WUparser if n in Cmap}

            pos_true = lbs_positions(mesh, defr, Wtrue, Bindinv, verts0, vgroups)
            pos_floor = lbs_positions(mesh, defr, Wfloor, Bindinv, verts0, vgroups)
            pos_parser = lbs_positions(mesh, defr, Wparser, Bindinv, verts0, vgroups)

            def stats(a, b):
                ds = sorted(((a[i] - b[i]).length for i in range(len(a))), reverse=True)
                return sum(ds) / len(ds) * 1000, ds[0] * 1000
            mf, xf = stats(pos_true, pos_floor)
            mp, xp = stats(pos_true, pos_parser)
            print(f"  frame {F}:")
            print(f"     PLANCHER TRS  vs vrai : moy={mf:6.2f} mm  max={xf:7.2f} mm  (limite absolue, aucune formule mieux)")
            print(f"     MON PARSEUR   vs vrai : moy={mp:6.2f} mm  max={xp:7.2f} mm")


run()
