"""
Verifie que le scale d'animation reste possible apres le passage morph-sans-scale.

(a) COPY_TRANSFORMS transmet-il le SCALE du ctrl au Def ? (on scale un os ctrl,
    on regarde si le Def recoit le scale)
(b) Les os du visage sont-ils des FEUILLES (pas d'enfant) ? -> scale non-uniforme
    safe a l'export. Sinon : enfants tournes = risque de shear.
"""

import bpy
import sys
from mathutils import Vector

ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context

# candidats "visage" (heuristique sur les noms)
FACE_HINTS = ("muzzle", "ear", "eye", "jaw", "tongue", "lip", "brow", "nose",
              "head", "teeth", "cheek", "lid")


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core(); sdc.clear_rig_data("Def")
    ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
    sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
    from AnimExport import core as ac; ac.reload_core()
    md = sdc.MAPPING_DICT

    # os Def "visage" + sont-ils feuilles ?
    defbones = {b.name: b for b in defr.data.bones}
    face_def = [n for n in defbones
                if any(h in n.lower() for h in FACE_HINTS)]
    print("=== (b) os Def 'visage' et statut feuille ===")
    for n in face_def:
        nchild = len(defbones[n].children)
        leaf = "FEUILLE (scale non-unif safe)" if nchild == 0 else f"{nchild} enfant(s) -> scale non-unif risque shear"
        print(f"   {n:24s} {leaf}")
    if not face_def:
        print("   (aucun os visage detecte par heuristique — a confirmer manuellement)")

    # (a) test : scaler un os ctrl -> le Def le recoit-il via COPY_TRANSFORMS ?
    # on prend un os Def feuille du visage si possible, sinon le 1er mappe
    target_def = next((n for n in face_def if len(defbones[n].children) == 0), None)
    if target_def is None:
        target_def = next(iter(md))
    ad = (md[target_def].get('Adult') or md[target_def].get('Child') or '').strip()
    print(f"\n=== (a) propagation du scale via COPY_TRANSFORMS (os '{target_def}' <- ctrl '{ad}') ===")
    pbc = ctrl.pose.bones.get(ad)
    if pbc is None:
        print("   cible ctrl introuvable")
        return
    # scale non-uniforme sur le ctrl
    pbc.scale = Vector((1.0, 1.6, 1.0))
    ctx.view_layer.update()
    evc = ctrl.evaluated_get(ctx.evaluated_depsgraph_get())
    ev = defr.evaluated_get(ctx.evaluated_depsgraph_get())
    _, _, sc = evc.pose.bones[ad].matrix.decompose()
    _, _, s = ev.pose.bones[target_def].matrix.decompose()
    print(f"   set ctrl.scale Y=1.6")
    print(f"   CTRL evalue : ({sc.x:.3f}, {sc.y:.3f}, {sc.z:.3f})   (si ~1.0 : ecrase par Rigify, test invalide)")
    print(f"   DEF  evalue : ({s.x:.3f}, {s.y:.3f}, {s.z:.3f})")
    print(f"   -> CTRL=1.6 & DEF=1.6 : COPY_TRANSFORMS propage le scale (OK pour anim visage)")
    pbc.scale = Vector((1.0, 1.0, 1.0))

    # test bis : scaler un os de CONTROLE non-ORG (ce que l'animateur utilise vraiment)
    print("\n=== (a-bis) via un os de controle deformant non pilote ===")
    # heuristique : os ctrl 'Adult_' ou 'tweak'/'DEF' du visage non-ORG
    cand = [pb.name for pb in ctrl.pose.bones
            if any(h in pb.name.lower() for h in ("eye", "eyebrow"))
            and not pb.name.startswith("ORG-") and not pb.name.startswith("DEF-")]
    print(f"   candidats controle visage non-ORG : {cand[:8]}")


run()
