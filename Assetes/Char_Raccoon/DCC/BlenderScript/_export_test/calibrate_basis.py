"""
Calibration de la basis Raccoon via le module générique `blender_unity_anim`.

Remplace solve_Q_basis.py. Côté Raccoon-spécifique : monter le rig (CtrlRig →
Def par contraintes) et poser Test 1. Le reste (Kabsch, écriture) est générique.

Pré-requis : dumps Unity ulocal_bind.json + ulocal_f{8,16,24,32,40}.json
(DumpLocal.Run dans le projet jetable _TempDump).

Lancer dans la console Blender (avec le .blend Raccoon ouvert).
"""

import bpy
import sys
import os
import json

HERE = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)

import blender_unity_anim as bua
bua.reload()

FRAMES = [8, 16, 24, 32, 40]


def load_unity(name):
    return json.loads(open(os.path.join(HERE, name)).read())


# --- monter le rig Raccoon + poser Test 1 (spécifique) -----------------------
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
sdc.clear_rig_data("Def")
ctrl = bpy.data.objects["RIG-CtrlRig"]
defr = bpy.data.objects["Def"]
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)

from AnimExport import core as ac
ac.reload_core()
from AnimExport.core import exporter
action = bpy.data.actions["Test 1"]
exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)

# --- échantillonnage (générique) ---------------------------------------------
ctx = bpy.context
b_samples = bua.dump_blender_locals(defr, ctx, [0] + FRAMES)
b_bind = b_samples[0]
b_frames = {fr: b_samples[fr] for fr in FRAMES}

bone_to_path = {b.name: bua.bone_path(defr, b.name, root="Def")
                for b in defr.data.bones}

u_bind = {p: bua.trs_to_mat(d) for p, d in load_unity("ulocal_bind.json").items()}
u_frames = {fr: {p: bua.trs_to_mat(d)
                 for p, d in load_unity(f"ulocal_f{fr}.json").items()}
            for fr in FRAMES}

# --- résolution + écriture (générique) ---------------------------------------
basis, worst, label = bua.solve_basis(b_bind, b_frames, u_bind, u_frames,
                                      bone_to_path, s=0.01)
print(f"basis : {len(basis)} os  |  pire reconstruction = {worst:.5f} ({label})")

OUT = os.path.normpath(os.path.join(ROOT, "AnimExport", "core", "unity_basis.json"))
bua.save_basis(OUT, basis)
print("→", OUT)
