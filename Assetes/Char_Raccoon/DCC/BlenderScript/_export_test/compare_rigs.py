"""
Compare le mesh adulte (frame 24) :
  TRUTH   = ancien rig STRETCH_TO + blendshape  (l'intention d'origine)
  NEW_on  = nouveau rig uniforme + blendshape
  NEW_off = nouveau rig uniforme, blendshape forcée à 0
Écarts de sommets en cm → localise la casse.
"""
import bpy, sys, os, importlib.util
import numpy as np

ROOT = r'P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript'
sys.path.insert(0, ROOT)
ctrl = bpy.data.objects['RIG-CtrlRig']; defr = bpy.data.objects['Def']
body = bpy.data.objects['MSH_Racoon_Body']

from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
from AnimExport import core as ac; ac.reload_core()
from AnimExport.core import exporter

# charge l'ancien applier depuis le fichier git
spec = importlib.util.spec_from_file_location("old_applier", r'P:/Chara_Giu/_TempDump/old_applier.py')
old_applier = importlib.util.module_from_spec(spec); spec.loader.exec_module(old_applier)

def goto_adult():
    a = bpy.data.actions['Test 2']
    exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, a)
    bpy.context.scene.frame_set(24); bpy.context.view_layer.update()

def verts():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg); me = ev.to_mesh()
    a = np.array([list(v.co) for v in me.vertices]); ev.to_mesh_clear()
    return a

def force_shape(val, mute):
    for o in (bpy.data.objects['MSH_Racoon_Body'], bpy.data.objects['MSH_Racoon_TailDetails']):
        skd = o.data.shape_keys
        if skd.animation_data:
            for d in skd.animation_data.drivers: d.mute = mute
        if mute: skd.key_blocks['Adult_shape'].value = val

# TRUTH : ancien rig
sdc.clear_rig_data('Def')
old_applier.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
force_shape(0, False)
goto_adult(); truth = verts()

# NEW : nouveau rig
sdc.clear_rig_data('Def')
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
force_shape(0, False)
goto_adult(); new_on = verts()
force_shape(0.0, True)
goto_adult(); new_off = verts()

def cmp(lbl, a):
    d = np.linalg.norm(a - truth, axis=1)
    print(f"  {lbl:28} moy={d.mean()*100:7.3f} cm  max={d.max()*100:7.3f} cm")

print(f"sommets={len(truth)}  (TRUTH = ancien STRETCH_TO + blendshape)")
cmp("NEW uniforme + blendshape", new_on)
cmp("NEW uniforme SANS blendshape", new_off)
