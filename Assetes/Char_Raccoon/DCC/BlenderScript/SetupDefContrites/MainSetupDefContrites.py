import bpy
import sys
import os
import importlib

# 1. Racine des scripts
blend_dir = os.path.dirname(bpy.data.filepath)
script_dir = os.path.join(blend_dir, "BlenderScript")
if script_dir not in sys.path:
    sys.path.append(script_dir)

# 2. Import + reload du core
from SetupDefContrites import Contrites_core as core
importlib.reload(core)
core.reload_core()

# Convention pattern (aucun nom d'objet en dur) : DEF-<Char> / RIG-<Char>
DEF_PREFIX = "DEF-"
RIG_PREFIX = "RIG-"


def _find_def_armature():
    """Première armature 'DEF-<Char>' du fichier (l'active en priorité si valide)."""
    act = bpy.context.active_object
    if act and act.type == 'ARMATURE' and act.name.startswith(DEF_PREFIX):
        return act
    return next((o for o in bpy.data.objects
                 if o.type == 'ARMATURE' and o.name.startswith(DEF_PREFIX)), None)


def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    def_rig = _find_def_armature()
    if def_rig is None:
        print(f"❌ Aucune armature '{DEF_PREFIX}<Char>' trouvée.")
        return
    char = def_rig.name[len(DEF_PREFIX):]
    ctrl_rig = bpy.data.objects.get(RIG_PREFIX + char)
    if ctrl_rig is None:
        print(f"❌ Ctrl '{RIG_PREFIX}{char}' introuvable.")
        return

    print(f"=== Setup morph : {def_rig.name}  ←  {ctrl_rig.name}  (Char={char}) ===")
    core.clear_rig_data(obj_name=def_rig.name)
    core.apply_constraints_from_dict(def_rig, ctrl_rig, core.MAPPING_DICT)


main()
