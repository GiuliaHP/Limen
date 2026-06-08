import bpy
import sys
import os
import importlib

# 1. On vide la console pour y voir clair
os.system('cls')

# 2. On part du dossier du .blend
blend_dir = os.path.dirname(bpy.data.filepath)
script_dir = os.path.join(blend_dir, "BlenderScript", "CustomRig")

# 3. On injecte de force dans Blender
if script_dir not in sys.path:
    sys.path.append(script_dir)

# 4. Importation
import core
importlib.reload(core)

def register():
    core.register()

def unregister():
    core.unregister()

if __name__ == "__main__":
    try: 
        unregister()
    except Exception: 
        pass
        
    register()
    print("UI Raccoon (Architecture Finale) chargée avec succès !")