import bpy
import sys
import os
import importlib

# 1. On vide la console pour y voir clair
os.system('cls')

# 2. On pointe vers la RACINE commune des outils (BlenderScript)
blend_dir = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(blend_dir, "BlenderScript")

# 3. On l'injecte dans le path
if script_root not in sys.path:
    sys.path.append(script_root)

# 4. Import NAMESPACÉ : évite tout conflit avec les autres outils du projet
from CustomRig import core
importlib.reload(core)

def register():
    core.register()

def unregister():
    core.unregister()

def _self_register():
    """Coche 'Register' (use_module) sur ce texte pour qu'il se relance
    automatiquement à chaque ouverture du .blend. Idempotent."""
    me = None
    # 1. Si lancé depuis le Text Editor : on récupère le texte actif
    try:
        me = bpy.context.space_data.text
    except Exception:
        me = None
    # 2. Sinon (autre contexte) : on le retrouve par son nom
    if me is None:
        me = bpy.data.texts.get("Main_CtrlRig_ui.py")

    if me and not me.use_module:
        me.use_module = True
        print(f"[Raccoon] '{me.name}' marqué Register (use_module=True). Pense à sauver le .blend.")

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass

    register()
    _self_register()
    print("UI Raccoon (Architecture Finale) chargée avec succès !")