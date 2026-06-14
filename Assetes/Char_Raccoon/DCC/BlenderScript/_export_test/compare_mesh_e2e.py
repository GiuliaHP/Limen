"""
End-to-end : le mesh skinné BAKÉ par Unity (os + blendshape, pic adulte)
correspond-il à l'ADULTE ou à l'ENFANT ? (preuve que la blendshape a firé)
Les os sont déjà validés 0.01° => pas d'envers. Ici on compare la FORME via
les proportions de bounding-box (robuste au split de verts Unity + au transform
global Blender↔Unity).
"""
import bpy, sys, os, json
import numpy as np

ROOT = r'P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript'
sys.path.insert(0, ROOT)
HERE = os.path.join(ROOT, "_export_test")

ctrl = bpy.data.objects['RIG-CtrlRig']; defr = bpy.data.objects['Def']
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core(); sdc.clear_rig_data('Def')
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)


def blender_extents(blend):
    ctrl.pose.bones['root']['morph_blend'] = blend
    ctrl.update_tag(); bpy.context.scene.frame_set(24); bpy.context.view_layer.update()
    o = bpy.data.objects['MSH_Racoon_Body']
    dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh()
    a = np.array([list(v.co) for v in me.vertices]); ev.to_mesh_clear()
    e = a.max(0) - a.min(0)
    return np.sort(e) / e.sum()        # proportions triées, sans unité


u = json.loads(open(os.path.join(HERE, "unity_mesh_MSH_Racoon_Body.json")).read())
U = np.array(u["verts"])
eu = np.sort(U.max(0) - U.min(0)); eu = eu / eu.sum()

ea = blender_extents(1.0)
ec = blender_extents(0.0)

da = np.abs(eu - ea).sum()
dc = np.abs(eu - ec).sum()
print(f"proportions bbox  Unity={np.round(eu,4)}")
print(f"                  ADULTE={np.round(ea,4)}  (ecart {da:.4f})")
print(f"                  ENFANT={np.round(ec,4)}  (ecart {dc:.4f})")
print(f"-> Unity ressemble a l'{'ADULTE -> blendshape OK' if da<dc else 'ENFANT -> blendshape PAS appliquee'}")
