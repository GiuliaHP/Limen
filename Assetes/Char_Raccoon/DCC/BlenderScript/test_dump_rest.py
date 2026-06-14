"""
Dump JSON du squelette Def :
 - rest pose : matrices parent-relatives (espace armature)
 - frame animée de Test 1 : pareil, pose évaluée (contraintes appliquées)
"""
import bpy, sys, os, json

root_dir    = os.path.dirname(bpy.data.filepath)
script_root = os.path.join(root_dir, "BlenderScript")
if script_root not in sys.path:
    sys.path.insert(0, script_root)

ctrl = bpy.data.objects.get("RIG-CtrlRig")
defr = bpy.data.objects.get("Def")

out_dir = os.path.join(script_root, "_export_test")
os.makedirs(out_dir, exist_ok=True)


def trs(m):
    loc, q, sc = m.decompose()
    return {"pos": [loc.x, loc.y, loc.z],
            "quat": [q.w, q.x, q.y, q.z],
            "scale": [sc.x, sc.y, sc.z]}


# --- Rest pose : matrix_local est en espace armature ---
rest = {}
for b in defr.data.bones:
    if b.parent:
        m = b.parent.matrix_local.inverted() @ b.matrix_local
    else:
        m = b.matrix_local.copy()
    rest[b.name] = trs(m)
    rest[b.name]["parent"] = b.parent.name if b.parent else None

with open(os.path.join(out_dir, "blender_rest.json"), "w") as fh:
    json.dump(rest, fh, indent=1)
print(f"rest : {len(rest)} os -> blender_rest.json")

# --- Pose animée (Test 1, milieu de clip) ---
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core()
sdc.clear_rig_data("Def")
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)

from AnimExport import core as anim_core
anim_core.reload_core()
from AnimExport.core import exporter

action = bpy.data.actions["Test 1"]
rng = exporter.export_range(action)
frame = (rng[0] + rng[1]) // 2

exporter._reset_to_default(ctrl)
exporter._assign_action(ctrl, action)
bpy.context.scene.frame_set(frame)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = defr.evaluated_get(dg)

pose = {"_frame": frame, "_fps": bpy.context.scene.render.fps}
for pb in ev.pose.bones:
    if pb.parent:
        m = ev.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix
    else:
        m = pb.matrix.copy()
    pose[pb.name] = trs(m)

with open(os.path.join(out_dir, "blender_pose_test1.json"), "w") as fh:
    json.dump(pose, fh, indent=1)
print(f"pose : frame {frame} -> blender_pose_test1.json")
print("=== FIN ===")
