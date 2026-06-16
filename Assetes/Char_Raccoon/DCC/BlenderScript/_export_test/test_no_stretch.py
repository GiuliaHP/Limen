"""
Teste l'hypothese : morph par POSITION d'os (joints) + blendshape, SANS STRETCH_TO.

1. Setup rig normal, frame 24 (morph plein).
2. Mesure les positions des TETES d'os Def (= joints) AVEC stretch.
3. Mute les STRETCH_TO, re-evalue : les joints bougent-ils ? (ils ne devraient PAS :
   les tetes sont posees par COPY_TRANSFORMS, le stretch ne fait que scaler).
   -> si joints identiques : le squelette est deja adulte-proportionne sans scale.
4. Mesure l'ecart MESH (stretch ON vs OFF) = ce que le blendshape devra absorber.
"""

import bpy
import sys

ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context
MESH = "MSH_Racoon_Body"
F = 24


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core(); sdc.clear_rig_data("Def")
    ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    from AnimExport import core as ac; ac.reload_core()
    from AnimExport.core import exporter
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, bpy.data.actions["Test 2"])
    mesh = bpy.data.objects[MESH]

    def heads_and_scales():
        ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
        heads = {pb.name: pb.matrix.translation.copy() for pb in ev.pose.bones}
        scales = {}
        for pb in ev.pose.bones:
            _, _, s = pb.matrix.decompose()
            scales[pb.name] = s.copy()
        return heads, scales

    def mesh_verts():
        ev = mesh.evaluated_get(ctx.evaluated_depsgraph_get())
        me = ev.to_mesh()
        vs = [v.co.copy() for v in me.vertices]
        ev.to_mesh_clear()
        return vs

    ctx.scene.frame_set(F); ctx.view_layer.update()
    heads_on, scales_on = heads_and_scales()
    verts_on = mesh_verts()

    # mute tous les STRETCH_TO sur le Def
    n_stretch = 0
    for pb in defr.pose.bones:
        for c in pb.constraints:
            if c.type == 'STRETCH_TO':
                c.mute = True; n_stretch += 1
    ctx.view_layer.update()
    heads_off, scales_off = heads_and_scales()
    verts_off = mesh_verts()

    # re-active (ne pas alterer durablement)
    for pb in defr.pose.bones:
        for c in pb.constraints:
            if c.type == 'STRETCH_TO':
                c.mute = False

    # 1) les joints (tetes) bougent-ils quand on coupe le stretch ?
    head_moves = sorted((((heads_on[n] - heads_off[n]).length) * 1000, n) for n in heads_on)
    head_moves.sort(reverse=True)
    nbig = sum(1 for d, _ in head_moves if d > 1)
    print(f"=== {n_stretch} STRETCH_TO mutes ===")
    print(f"DEPLACEMENT DES JOINTS (tete d'os) stretch ON->OFF :")
    print(f"  os dont le joint bouge >1mm : {nbig} / {len(head_moves)}   max={head_moves[0][0]:.2f}mm ({head_moves[0][1]})")
    print(f"  -> si ~0 : le squelette est deja adulte-proportionne par POSITION (animable, sans scale)")

    # 2) scale residuel apres mute (doit ~1)
    res = sorted(((max(scales_off[n]) - min(scales_off[n]), n) for n in scales_off), reverse=True)
    print(f"  scale non-uniforme residuel apres mute : max ecart={res[0][0]:.3f} ({res[0][1]})  (doit ~0)")

    # 3) ecart MESH stretch ON vs OFF = travail du blendshape
    n = len(verts_on)
    diffs = sorted(((verts_on[i] - verts_off[i]).length for i in range(n)), reverse=True)
    print(f"ECART MESH stretch ON vs OFF (= ce que le blendshape Adult_shape doit porter) :")
    print(f"  moy={sum(diffs)/n*1000:.2f}mm  max={diffs[0]*1000:.2f}mm  ({n} verts)")
    print(f"  -> le blendshape (delta par vertex, exact) peut porter ca sans aucune limite TRS")


run()
