import bpy, sys, os, json, math
from mathutils import Matrix, Quaternion, Vector
HERE=r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")
def loadU(n): return json.loads(open(os.path.join(HERE,n)).read())
def trs(d):
    q=Quaternion(d["quat"]); m=q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3): m[i][j]*=d["scale"][j]
    m.translation=Vector(d["pos"]); return m
ub=loadU("ulocal_bind.json"); u16=loadU("ulocal_f16.json"); u32=loadU("ulocal_f32.json")
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core(); sdc.clear_rig_data("Def")
ctrl=bpy.data.objects["RIG-CtrlRig"]; defr=bpy.data.objects["Def"]
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
from AnimExport import core as ac; ac.reload_core()
from AnimExport.core import exporter
a=bpy.data.actions["Test 1"]
exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, a)
defbones={b.name:b for b in defr.data.bones}
def upath(bone):
    parts=[];cur=defbones.get(bone)
    while cur:parts.append(cur.name);cur=cur.parent
    parts.reverse();return "Def/"+"/".join(parts)
def blocal_all(frame):
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg)
    return {pb.name:((ev.pose.bones[pb.parent.name].matrix.inverted()@pb.matrix) if pb.parent else pb.matrix.copy()) for pb in ev.pose.bones}
B0=blocal_all(0); B16=blocal_all(16); B32=blocal_all(32)
# R_b = Ubind @ Bbind^-1 ; pred(t) = R_b @ Blender_local(t)
worst16=worst32=0; w16=w32=""; n=0
for bone in defbones:
    up=upath(bone)
    if up not in ub or up not in u16 or up not in u32: continue
    Ubind=trs(ub[up]); Bbind=B0[bone]
    R=Ubind @ Bbind.inverted()
    p16=R @ B16[bone]; p32=R @ B32[bone]
    d16=max(abs(p16[i][j]-trs(u16[up])[i][j]) for i in range(4) for j in range(4))
    d32=max(abs(p32[i][j]-trs(u32[up])[i][j]) for i in range(4) for j in range(4))
    n+=1
    if d16>worst16: worst16=d16; w16=bone
    if d32>worst32: worst32=d32; w32=bone
print(f"RES retarget pred vs FBX : frame16 max={worst16:.5f} ({w16})  frame32 max={worst32:.5f} ({w32})  sur {n} os")
