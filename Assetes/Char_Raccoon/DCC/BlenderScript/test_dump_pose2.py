"""Dump Blender : pose Test 2 à la DERNIÈRE frame (morph adulte complet)."""
import bpy, sys, os, json

root_dir    = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.insert(0, script_root)

ctrl = bpy.data.objects.get("RIG-CtrlRig")
defr = bpy.data.objects.get("Def")
out_dir = os.path.join(script_root, "_export_test")

from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
sdc.clear_rig_data("Def")
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)

from AnimExport import core as anim_core
anim_core.reload_core()
from AnimExport.core import exporter

action = bpy.data.actions["Test 2"]
rng = exporter.export_range(action)

# Trouver le frame du PIC de morph (morph_blend max), pas la dernière frame :
# Test 2 fait child→adult→child, le pic adulte est au milieu.
exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)
root_pb = ctrl.pose.bones.get("root")
best_f, best_v = rng[0], -1.0
for f in range(rng[0], rng[1] + 1):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    v = root_pb.get("morph_blend", 0.0) if root_pb else 0.0
    if v > best_v:
        best_v, best_f = v, f
frame = best_f
print(f"pic morph_blend={best_v:.3f} au frame {frame}")

exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)
bpy.context.scene.frame_set(frame)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = defr.evaluated_get(dg)


def trs(m):
    loc, q, sc = m.decompose()
    return {"pos": [loc.x, loc.y, loc.z],
            "quat": [q.w, q.x, q.y, q.z],
            "scale": [sc.x, sc.y, sc.z]}


pose = {"_frame": frame, "_fps": bpy.context.scene.render.fps,
        "_t": (frame - rng[0]) / bpy.context.scene.render.fps}
for pb in ev.pose.bones:
    if pb.parent:
        m = ev.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix
    else:
        m = pb.matrix.copy()
    pose[pb.name] = trs(m)

with open(os.path.join(out_dir, "blender_pose_test2.json"), "w") as fh:
    json.dump(pose, fh, indent=1)
print(f"pose Test 2 : frame {frame} (t={pose['_t']:.4f}s) -> blender_pose_test2.json")
print("=== FIN ===")
