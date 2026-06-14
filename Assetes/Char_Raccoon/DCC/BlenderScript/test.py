"""
TEST EXPORT : sort UN seul FBX "simple" du Def pour valider la chaîne Unity.
À ouvrir dans le Text Editor de Blender (Text > Open) puis Run (>).

- Choisis le clip dans CLIP_NAME (None = action active du RIG-CtrlRig).
- Le FBX sort dans le dossier du .blend sous  _export_test/  (pas dans Unity,
  pour ne pas polluer le projet pendant les essais).
"""
import bpy
import sys
import os

# --- params d'essai ---
CLIP_NAME = None          # None = action active ; sinon "NomDeLAction"
OUT_SUBDIR = "_export_test"

root_dir = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.append(script_root)

from AnimExport import core
core.reload_core()
from AnimExport.core import exporter, config

ctrl = bpy.data.objects[config.ANIM_SOURCE]
defr = bpy.data.objects[config.DEF_ARMATURE]

# action à exporter
if CLIP_NAME:
    action = bpy.data.actions[CLIP_NAME]
else:
    action = ctrl.animation_data.action if ctrl.animation_data else None
if action is None:
    raise RuntimeError("Aucune action : assigne-en une au RIG-CtrlRig ou fixe CLIP_NAME.")

out_dir = os.path.join(root_dir, OUT_SUBDIR)
os.makedirs(out_dir, exist_ok=True)

rng = exporter.export_range(action)
print(f"\n=== EXPORT TEST : {action.name}  plage={rng}  ->  {out_dir} ===")
ok, msg = exporter._export_one(bpy.context, action, rng, ctrl, defr, out_dir)
print(("OK   " if ok else "FAIL ") + msg)

fbx = os.path.join(out_dir, exporter._sanitize(action.name) + ".fbx")
if os.path.exists(fbx):
    print(f">>> {os.path.getsize(fbx)} octets : {fbx}")
    print(">>> Glisse ce .fbx dans Unity (Assets) et vérifie l'anim sur l'avatar.")
