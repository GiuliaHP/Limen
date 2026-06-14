import bpy, sys, os, json
from mathutils import Matrix, Quaternion, Vector
HERE=r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")

def loadU(n):  # dumps Unity (InvariantCulture)
    return json.loads(open(os.path.join(HERE,n)).read())
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

def blocal_at(frame):
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg)
    out={}
    for pb in ev.pose.bones:
        m = (ev.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix) if pb.parent else pb.matrix.copy()
        out[pb.name]=m
    return out

def brest():
    out={}
    for b in defr.data.bones:
        m=(b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy()
        out[b.name]=m
    return out

Br=brest(); B16=blocal_at(16); B32=blocal_at(32)

import math
# test : Δ_unity = M^-1 @ Δ_blender @ M  (conjugaison constante du delta relatif au repos)
worst=0; n=0; nconst=0; wb=""
for bone in Br:
    up=upath(bone)
    if up not in ub or up not in u16 or up not in u32: continue
    Ur=trs(ub[up]); U16=trs(u16[up]); U32=trs(u32[up])
    dU16=Ur.inverted()@U16; dU32=Ur.inverted()@U32
    dB16=Br[bone].inverted()@B16[bone]; dB32=Br[bone].inverted()@B32[bone]
    # M tel que dU16 = M^-1 @ dB16 @ M  -> résoudre M ? difficile. Test direct : M = dB16^-1... 
    # Approche : trouver T constant tel que dU = T(dB). Test conjugaison via une rotation.
    # On teste si dU et dB ont le même ANGLE de rotation (invariant par conjugaison)
    aU=math.degrees(dU16.to_quaternion().angle); aB=math.degrees(dB16.to_quaternion().angle)
    n+=1
    if abs(aU-aB)<0.5: nconst+=1
    if abs(aU-aB)>worst: worst=abs(aU-aB); wb=bone
print(f"os {n}  même angle de rotation delta (Unity vs Blender, <0.5°): {nconst}  pire écart angle: {worst:.3f}° ({wb})")
