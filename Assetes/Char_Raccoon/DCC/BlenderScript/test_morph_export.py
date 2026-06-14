"""
VALIDATION pre-bake : compare longueurs Blender vs FBX réimporté.
"""
import bpy, sys, os

root_dir = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.insert(0, script_root)

ctrl = bpy.data.objects.get("RIG-CtrlRig")
defr = bpy.data.objects.get("Def")

from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
sdc.clear_rig_data("Def")
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)

from AnimExport import core as anim_core
anim_core.reload_core()
from AnimExport.core import exporter, clips

action = bpy.data.actions["Test 2"]
rng    = exporter.export_range(action)
start, end = rng

# Référence Blender (frame par frame via action sur ctrl)
print("\n=== RÉFÉRENCE Blender ===")
bones_check = ["upper_arm.L", "forearm.L", "thigh.L", "shin.L"]
root_pb = ctrl.pose.bones["root"]
exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)

ref = {}
print(f"  {'frame':>6}  {'blend':>6}  " + "  ".join(f"{b:>14}" for b in bones_check))
for f in [start, (start+end)//2, end]:
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    dg  = bpy.context.evaluated_depsgraph_get()
    ev  = defr.evaluated_get(dg)
    blend = root_pb.get("morph_blend", -1)
    lens  = []
    for b in bones_check:
        pb = ev.pose.bones.get(b)
        l  = (pb.tail - pb.head).length if pb else -1.0
        lens.append(l)
        ref.setdefault(f, {})[b] = l
    print(f"  {f:>6}  {blend:>6.3f}  " + "  ".join(f"{l:>14.5f}" for l in lens))

# Export avec la nouvelle méthode pre-bake
print("\n=== EXPORT (pre-bake) ===")
out_dir = os.path.join(root_dir, "_export_test")
os.makedirs(out_dir, exist_ok=True)
exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)
bpy.context.scene.frame_start = start
bpy.context.scene.frame_end   = end
bpy.context.scene.frame_set(start)
bpy.context.view_layer.update()

ok, msg = exporter._export_one(bpy.context, action, rng, ctrl, defr, out_dir)
print(("OK  : " if ok else "FAIL: ") + msg)
fbx = os.path.join(out_dir, exporter._sanitize("Test 2") + ".fbx")
if os.path.exists(fbx):
    print(f"  Taille : {os.path.getsize(fbx):,} octets")

# Réimport + comparaison
print("\n=== COMPARAISON Blender vs FBX réimporté ===")
bpy.ops.import_scene.fbx(filepath=fbx)
imp = next((o for o in bpy.context.selected_objects if o.type == 'ARMATURE'), None)
if imp is None:
    print("  Import FBX échoué."); sys.exit(1)

imp_action = next((a for a in bpy.data.actions
                   if a.name.startswith("Test 2") and a is not action), None)
if imp_action and imp.animation_data:
    imp.animation_data.action = imp_action

print(f"  {'frame':>6}  {'os':>14}  {'Blender':>12}  {'FBX':>12}  {'écart%':>8}")
for f in [start, (start+end)//2, end]:
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    dg  = bpy.context.evaluated_depsgraph_get()
    ev  = imp.evaluated_get(dg)
    for b in bones_check:
        pb  = ev.pose.bones.get(b)
        fbx_l = (pb.tail - pb.head).length if pb else -1.0
        ref_l = ref.get(f, {}).get(b, -1.0)
        ecart = abs(fbx_l - ref_l) / ref_l * 100 if ref_l > 0 else 0
        flag  = "  <-- !!" if ecart > 2.0 else ""
        print(f"  {f:>6}  {b:>14}  {ref_l:>12.5f}  {fbx_l:>12.5f}  {ecart:>7.2f}%{flag}")
    print()

print("=== FIN ===")
