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
u16=loadU("ulocal_f16.json")
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
bpy.context.scene.frame_set(16); bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg)
def blocal(bone):
    pb=ev.pose.bones[bone]
    return (ev.pose.bones[pb.parent.name].matrix.inverted()@pb.matrix) if pb.parent else pb.matrix.copy()
# tester plusieurs M (miroirs) + scale
def scale_trans(m,s):
    m=m.copy(); m.translation=m.translation*s; return m
mirrors={"Zmir diag(1,1,-1)":Matrix.Diagonal((1,1,-1,1)),
         "Xmir diag(-1,1,1)":Matrix.Diagonal((-1,1,1,1)),
         "Ymir diag(1,-1,1)":Matrix.Diagonal((1,-1,1,1))}
for name,M in mirrors.items():
    Mi=M.inverted(); worst=0;n=0;wb=""
    for bone in defbones:
        up=upath(bone)
        if up not in u16: continue
        Lb=blocal(bone)
        pred=scale_trans(M@Lb@Mi, 0.01)
        U=trs(u16[up])
        d=max(abs(pred[i][j]-U[i][j]) for i in range(4) for j in range(4))
        n+=1
        if d>worst: worst=d; wb=bone
    print(f"RES {name}: pire écart matrice = {worst:.4f} ({wb}) sur {n} os")
