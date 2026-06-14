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
ub=loadU("ulocal_bind.json"); u16=loadU("ulocal_f16.json")
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
bone="shin.L"; up=upath(bone)
# Blender edit rest local + eval local frame16
bn=defbones[bone]
Brest_edit=(bn.parent.matrix_local.inverted()@bn.matrix_local) if bn.parent else bn.matrix_local.copy()
def blocal(frame):
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg); pb=ev.pose.bones[bone]
    return (ev.pose.bones[pb.parent.name].matrix.inverted()@pb.matrix) if pb.parent else pb.matrix.copy()
B0=blocal(0); B16=blocal(16)
Ur=trs(ub[up]); U16=trs(u16[up])
def ang(m): return math.degrees(m.to_quaternion().angle)
print("RES Brest_edit quat:", [round(x,3) for x in Brest_edit.to_quaternion()])
print("RES Bframe0  quat:", [round(x,3) for x in B0.to_quaternion()])
print("RES Ubind    quat:", [round(x,3) for x in Ur.to_quaternion()])
print("RES delta angle Unity (bind->f16):", round(ang(Ur.inverted()@U16),2))
print("RES delta angle Blender (editrest->f16):", round(ang(Brest_edit.inverted()@B16),2))
print("RES delta angle Blender (frame0->f16):", round(ang(B0.inverted()@B16),2))
print("RES => si frame0 matche Unity, le bind FBX = pose frame0, pas edit-rest")
