import bpy
import sys
import os
import importlib

# 1. On pointe vers le parent
blend_dir = os.path.dirname(bpy.data.filepath)
# Point d'entrée : SetupDefContrites
script_dir = os.path.join(blend_dir, "BlenderScript")
if script_dir not in sys.path: 
    sys.path.append(script_dir)

# 2. On importe explicitement le nouveau dossier renommé
from SetupDefContrites import Contrites_core as core

# 3. On recharge le package LUI-MÊME (récupère le reload_core corrigé) PUIS ses sous-modules.
#    Sans ce reload(core), une session déjà ouverte garderait l'ancien __init__ en mémoire.
importlib.reload(core)
core.reload_core()

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    def_rig = bpy.data.objects.get("Def")
    ctrl_rig = bpy.data.objects.get("RIG-CtrlRig")
    
    if not def_rig or not ctrl_rig:
        print("❌ Objets 'Def' ou 'RIG-CtrlRig' introuvables.")
        return

    # 4. Appel
    core.clear_rig_data(obj_name="Def")
    core.apply_constraints_from_dict(def_rig, ctrl_rig, core.MAPPING_DICT)

main()