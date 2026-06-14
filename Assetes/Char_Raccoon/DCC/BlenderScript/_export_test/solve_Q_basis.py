import bpy, sys, os, json
import numpy as np
from mathutils import Matrix, Quaternion, Vector
HERE=r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")
FRAMES=[8,16,24,32,40]
def loadU(n): return json.loads(open(os.path.join(HERE,n)).read())
def trs(d):
    q=Quaternion(d["quat"]); m=q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3): m[i][j]*=d["scale"][j]
    m.translation=Vector(d["pos"]); return m
ub=loadU("ulocal_bind.json")
uf={fr:loadU(f"ulocal_f{fr}.json") for fr in FRAMES}
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
B0=blocal_all(0); Bf={fr:blocal_all(fr) for fr in FRAMES}
def rotvec(M):
    q=M.to_quaternion(); ang=q.angle
    ax=q.axis
    if ang>3.14159265: ang=ang-2*3.14159265
    import numpy as _np
    return _np.array([ax.x,ax.y,ax.z])*ang
def solveQ(pairs):  # pairs: list of (dU4,dB4) full matrices ; Kabsch sur rotvec
    A=[]; B=[]
    for dU,dB in pairs:
        A.append(rotvec(dU)); B.append(rotvec(dB))
    A=np.array(A); B=np.array(B)
    H=A.T@B
    U,_,Vt=np.linalg.svd(H)
    d=np.sign(np.linalg.det(Vt.T@U.T))
    R=Vt.T@np.diag([1,1,d])@U.T   # Q tel que Q@a≈b
    return R

def to4(R):
    m=Matrix.Identity(4)
    for i in range(3):
        for j in range(3): m[i][j]=float(R[i][j])
    return m
out={}; worst=0; wb=""
for bone in defbones:
    up=upath(bone)
    if up not in ub: continue
    Ubind=trs(ub[up]); Bbind=B0[bone]
    pairs=[]
    for fr in FRAMES:
        if up not in uf[fr]: continue
        dU=Ubind.inverted()@trs(uf[fr][up]); dB=Bbind.inverted()@Bf[fr][bone]
        pairs.append((dU,dB))
    R=solveQ(pairs); Q=to4(R)
    A=Ubind @ Q.inverted() @ Bbind.inverted()
    # vérif full matrix sur toutes les frames
    for fr in FRAMES:
        if up not in uf[fr]: continue
        pred=A @ Bf[fr][bone] @ Q
        e=max(abs(pred[i][j]-trs(uf[fr][up])[i][j]) for i in range(4) for j in range(4))
        if e>worst: worst=e; wb=f"{bone}@{fr}"
    Bbi=Bbind.inverted()
    out[bone]={"path":up,"Ubind":[v for r in Ubind for v in r],"Bbinv":[v for r in Bbi for v in r],"Q":[v for r in Q for v in r],"s":0.01}
print(f"RES basis Q (5 frames): pire reconstruction = {worst:.5f} ({wb}) sur {len(out)} os")
OUT=os.path.normpath(os.path.join(HERE,"..","AnimExport","core","unity_basis.json"))
open(OUT,"w").write(json.dumps(out))
print("basis Q ecrite")
