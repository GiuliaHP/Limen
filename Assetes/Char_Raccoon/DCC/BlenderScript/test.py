"""
TEST : applique la stratégie complète et vérifie la TRANSITION (blend 0/0.5/1).
À ouvrir dans le Text Editor de Blender (Text > Open) puis Run (▶).
"""
import bpy
import sys
import os

root_dir = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.append(script_root)

from SetupDefContrites import Contrites_core as core
core.reload_core()

defr = bpy.data.objects["Def"]
ctrl = bpy.data.objects["RIG-CtrlRig"]

core.clear_rig_data("Def")
core.apply_constraints_from_dict(defr, ctrl, core.MAPPING_DICT)


def blen(obj, bone):
    dg = bpy.context.evaluated_depsgraph_get()
    b = obj.evaluated_get(dg).pose.bones[bone]
    return (b.tail - b.head).length


bones = ["upper_arm.L", "forearm.L", "thigh.L", "shin.L", "spine.004"]

print("\n============ TRANSITION (longueurs Def) ============")
print(f"  {'os':12} {'blend=0':>9} {'blend=0.5':>10} {'blend=1':>9}  {'monotone ?':>11}")
for dn in bones:
    vals = []
    for bl in (0.0, 0.5, 1.0):
        ctrl.pose.bones["root"]["morph_blend"] = bl
        bpy.context.view_layer.update()
        vals.append(blen(defr, dn))
    v0, v5, v1 = vals
    # 0.5 doit être ENTRE 0 et 1 (sinon = explosion à la transition)
    lo, hi = min(v0, v1), max(v0, v1)
    ok = "OK" if (lo - 1e-4) <= v5 <= (hi + 1e-4) else "<-- EXPLOSE"
    print(f"  {dn:12} {v0:9.3f} {v5:10.3f} {v1:9.3f}  {ok:>11}")
print("====================================================\n")
print(">>> Glisse morph_blend 0<->1 dans le viewport : le Def doit morpher en douceur,")
print(">>> sans à-coup ni explosion à mi-chemin.")
