"""
D'OÙ vient la forme adulte ? Compare les positions de sommets du mesh évalué
au pic (frame 24) sous 3 configs, contre la vérité (tout activé) :

  A. VÉRITÉ      : bones étirés (STRETCH_TO) + Adult_shape=1
  B. blendshape  : bones FORCÉS à scale=1 (rotation+pos gardées) + Adult_shape=1
  C. bones seuls : bones étirés + Adult_shape=0
  D. rien        : bones rest + Adult_shape=1   (blendshape pure sur skel enfant)

Donne l'écart moyen/max de sommets (mètres). Si B≈0, on peut exporter des bones
sans scale non-uniforme → plus de shear → Unity OK.
"""
import bpy, sys, os
import numpy as np

sys.path.insert(0, r'P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript')
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core(); sdc.clear_rig_data("Def")
ctrl = bpy.data.objects["RIG-CtrlRig"]; defr = bpy.data.objects["Def"]
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
from AnimExport import core as ac; ac.reload_core()
from AnimExport.core import exporter

action = bpy.data.actions["Test 2"]
exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, action)
FRAME = 24
mesh_obj = bpy.data.objects["MSH_Racoon_Body"]


def eval_verts():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh_obj.evaluated_get(dg)
    me = ev.to_mesh()
    arr = np.array([list(v.co) for v in me.vertices])
    ev.to_mesh_clear()
    return arr


bpy.context.scene.frame_set(FRAME)
truth = eval_verts()                                   # A
print(f"sommets: {len(truth)}")


def compare(label, arr):
    d = np.linalg.norm(arr - truth, axis=1)
    print(f"  {label:34} moy={d.mean()*100:6.3f} cm  max={d.max()*100:6.3f} cm")


# --- B : forcer les bones Def à scale uniforme=1 via un POST-hook impossible
#     simplement → on lit la matrice de pose et on retire le scale.
#     On désactive les contraintes STRETCH_TO et on garde COPY (rot+loc).
def set_stretch_influence(val):
    n = 0
    for pb in defr.pose.bones:
        for c in pb.constraints:
            if c.type == 'STRETCH_TO':
                c.influence = val; n += 1
    return n


n = set_stretch_influence(0.0)
bpy.context.scene.frame_set(FRAME)
compare(f"B. sans STRETCH ({n} off) + blendshape", eval_verts())
set_stretch_influence(1.0)

# --- C : bones étirés, blendshape OFF
sk = mesh_obj.data.shape_keys.key_blocks["Adult_shape"]
# couper le driver en fixant la valeur ne marche pas (driver ré-écrit) → mute driver
def mute_shape_drivers(mute):
    for o in (bpy.data.objects["MSH_Racoon_Body"], bpy.data.objects["MSH_Racoon_TailDetails"]):
        ad = o.data.shape_keys.animation_data
        if ad:
            for d in ad.drivers:
                d.mute = mute
        for kb in o.data.shape_keys.key_blocks:
            pass

# Approche robuste : on lit la contribution en mettant Adult_shape à 0 via mute
import contextlib
def force_shape(val):
    for o in (bpy.data.objects["MSH_Racoon_Body"], bpy.data.objects["MSH_Racoon_TailDetails"]):
        skd = o.data.shape_keys
        ad = skd.animation_data
        if ad:
            for d in ad.drivers:
                d.mute = True
        skd.key_blocks["Adult_shape"].value = val

force_shape(0.0)
bpy.context.scene.frame_set(FRAME); bpy.context.view_layer.update()
compare("C. bones étirés + blendshape=0", eval_verts())

# --- D : bones rest + blendshape=1
force_shape(1.0)
n = set_stretch_influence(0.0)
# aussi couper COPY pour vraiment rest ? non : on garde le pose enfant.
bpy.context.scene.frame_set(FRAME); bpy.context.view_layer.update()
compare("D. bones sans stretch + blendshape=1", eval_verts())

print("\n(rappel: A=vérité=0. Si B petit → exporter bones sans scale = solution.)")
