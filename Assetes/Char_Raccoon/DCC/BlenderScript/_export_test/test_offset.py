import bpy, sys, os, json
from mathutils import Matrix, Quaternion, Vector
import math
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
def brest(b):
    bn=defbones[b]
    return (bn.parent.matrix_local.inverted()@bn.matrix_local) if bn.parent else bn.matrix_local.copy()
def blocal(bone,frame):
    bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg)
    pb=ev.pose.bones[bone]
    return (ev.pose.bones[pb.parent.name].matrix.inverted()@pb.matrix) if pb.parent else pb.matrix.copy()
# pour chaque offset, moyenne d'écart d'angle sur tous les os
for off in (-1.0,-0.5,0.0,0.5,1.0):
    fr=16+off
    tot=0;n=0;worst=0
    for bone in defbones:
        up=upath(bone)
        if up not in ub or up not in u16: continue
        dU=trs(ub[up]).inverted()@trs(u16[up])
        bpy.context.scene.frame_set(int(fr),subframe=fr-int(fr)); bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg); pb=ev.pose.bones[bone]
        Bl=(ev.pose.bones[pb.parent.name].matrix.inverted()@pb.matrix) if pb.parent else pb.matrix.copy()
        dB=brest(bone).inverted()@Bl
        d=abs(math.degrees(dU.to_quaternion().angle)-math.degrees(dB.to_quaternion().angle))
        tot+=d;n+=1;worst=max(worst,d)
    print(f"offset {off:+.1f} (frame {fr}): moy écart angle={tot/n:.3f}°  max={worst:.3f}°")
