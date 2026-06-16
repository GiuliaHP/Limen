"""
Hypothese corrigee (suggestion user) : DECONNECTER les os Def, PUIS couper le
STRETCH_TO. Alors chaque tete d'os est posee librement par son COPY_TRANSFORMS
vers le joint ADULTE -> squelette adulte-proportionne par TRANSLATION (sans scale,
exportable, animable).

Verifie :
 1. apres deconnexion + stretch coupe, les joints Def atterrissent-ils aux
    positions ADULTES (compare a la tete de l'os ctrl Adult) ?
 2. scale non-uniforme residuel ~0 ?
 3. ecart mesh (rig complet stretch) vs (deconnecte sans stretch) = travail du blendshape
"""

import bpy
import sys

ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context
MESH = "MSH_Racoon_Body"
F = 24


def mesh_verts(obj):
    ev = obj.evaluated_get(ctx.evaluated_depsgraph_get())
    me = ev.to_mesh()
    vs = [v.co.copy() for v in me.vertices]
    ev.to_mesh_clear()
    return vs


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core()
    defr = bpy.data.objects["Def"]
    ctrl = bpy.data.objects["RIG-CtrlRig"]
    mesh = bpy.data.objects[MESH]
    md = sdc.MAPPING_DICT

    from AnimExport import core as ac; ac.reload_core()
    from AnimExport.core import exporter

    # --- A) rig complet (connecte + stretch) : reference mesh + positions ---
    sdc.clear_rig_data("Def")
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    ctx.scene.frame_set(F); ctx.view_layer.update()
    verts_full = mesh_verts(mesh)

    # --- B) DECONNECTER les os Def ---
    ctx.view_layer.objects.active = defr
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in defr.data.edit_bones:
        eb.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')

    # re-setup (constraints inchangees par la deconnexion, mais on refait propre)
    sdc.clear_rig_data("Def")
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    # couper les STRETCH_TO
    n_stretch = 0
    for pb in defr.pose.bones:
        for c in pb.constraints:
            if c.type == 'STRETCH_TO':
                c.mute = True; n_stretch += 1
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    ctx.scene.frame_set(F); ctx.view_layer.update()

    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    cb = {b.name: b for b in ctrl.data.bones}

    # 1) joints Def vs joint ADULTE ctrl (en monde)
    errs = []
    resid_scale = []
    for def_name, t in md.items():
        pb = ev.pose.bones.get(def_name)
        ad = (t.get('Adult') or '').strip()
        if pb is None or ad not in cb:
            continue
        def_head = defr.matrix_world @ pb.matrix.translation
        adult_head = ctrl.matrix_world @ cb[ad].head_local
        errs.append(((def_head - adult_head).length * 1000, def_name))
        _, _, s = pb.matrix.decompose()
        resid_scale.append((max(s) - min(s), def_name))
    errs.sort(reverse=True); resid_scale.sort(reverse=True)
    nbig = sum(1 for d, _ in errs if d > 5)
    print(f"=== DECONNECTE + {n_stretch} STRETCH_TO coupes (frame {F}) ===")
    print(f"1) joint Def vs joint ADULTE ctrl : moy={sum(d for d,_ in errs)/len(errs):.1f}mm  max={errs[0][0]:.1f}mm ({errs[0][1]})")
    print(f"   os >5mm du joint adulte : {nbig}/{len(errs)}")
    print(f"   -> si ~0 : squelette adulte-proportionne par TRANSLATION, animable, sans scale")
    print(f"2) scale non-uniforme residuel : max ecart={resid_scale[0][0]:.3f} ({resid_scale[0][1]})  (doit ~0)")

    # 3) ecart mesh full(stretch) vs deconnecte-sans-stretch = travail blendshape
    verts_nost = mesh_verts(mesh)
    n = len(verts_full)
    diffs = sorted(((verts_full[i] - verts_nost[i]).length for i in range(n)), reverse=True)
    print(f"3) ecart mesh full-stretch vs deconnecte-sans-stretch (= ce que le blendshape porte) :")
    print(f"   moy={sum(diffs)/n*1000:.1f}mm  max={diffs[0]*1000:.1f}mm")


run()
