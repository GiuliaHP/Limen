"""
Validation finale end-to-end : recale Blender->Unity via les têtes d'os
(correspondance connue, Umeyama), mappe le mesh adulte Blender dans l'espace
Unity, puis mesure le plus-proche-voisin contre le mesh Unity baké.
Résidu faible = le mesh Unity == l'adulte Blender (os + blendshape corrects).
"""
import bpy, sys, os, json, re
import numpy as np

ROOT = r'P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript'
sys.path.insert(0, ROOT); HERE = os.path.join(ROOT, "_export_test")
ctrl = bpy.data.objects['RIG-CtrlRig']; defr = bpy.data.objects['Def']
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core(); sdc.clear_rig_data('Def')
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
ctrl.pose.bones['root']['morph_blend']=1.0
ctrl.update_tag(); bpy.context.scene.frame_set(24); bpy.context.view_layer.update()

def loadj(n):
    return json.loads(open(os.path.join(HERE,n)).read())

# têtes d'os : Blender (évalué) vs Unity (wpos du dump)
up = json.loads(re.sub(r'(\d),(\d)', r'\1.\2', open(os.path.join(HERE,"unity_pose_test2.json")).read()))
dg = bpy.context.evaluated_depsgraph_get(); ev = defr.evaluated_get(dg)
B=[]; Uw=[]
for path,d in up.items():
    if not path.startswith("Def/"): continue
    bn=path.split("/")[-1]
    pb=ev.pose.bones.get(bn)
    if pb is None or "wpos" not in d: continue
    B.append(list(defr.matrix_world @ pb.head)); Uw.append(d["wpos"])
B=np.array(B); Uw=np.array(Uw)

def umeyama(src,dst):
    ms,md=src.mean(0),dst.mean(0); s0,d0=src-ms,dst-md
    U,D,Vt=np.linalg.svd(d0.T@s0/len(src)); S=np.eye(3)
    if np.linalg.det(U)*np.linalg.det(Vt)<0: S[2,2]=-1
    R=U@S@Vt; sc=np.trace(np.diag(D)@S)/((s0**2).sum()/len(src))
    return R,sc,md,ms
R,sc,md,ms=umeyama(B,Uw)
def maptoU(P): return (sc*(R@(P-ms).T)).T+md

# mesh adulte Blender -> espace Unity
o=bpy.data.objects['MSH_Racoon_Body']
dg=bpy.context.evaluated_depsgraph_get(); evm=o.evaluated_get(dg); me=evm.to_mesh()
Bm=np.array([list(o.matrix_world @ v.co) for v in me.vertices]); evm.to_mesh_clear()
BmU=maptoU(Bm)

Um=np.array(json.loads(open(os.path.join(HERE,"unity_mesh_MSH_Racoon_Body.json")).read())["verts"])

# NN: pour chaque vert Blender mappé, distance au plus proche vert Unity
from mathutils.kdtree import KDTree
kd=KDTree(len(Um))
for i,p in enumerate(Um): kd.insert(p,i)
kd.balance()
ds=[kd.find(p)[2] for p in BmU]
ds=np.array(ds)
char_h=np.linalg.norm(Um.max(0)-Um.min(0))
print(f"recalage os: scale={sc:.4f} detR={np.linalg.det(R):+.2f} (residu heads={np.sqrt(((maptoU(B)-Uw)**2).sum(1)).mean()/char_h*100:.2f}%)")
print(f"mesh NN Blender-adulte -> Unity : moy={ds.mean()/char_h*100:.3f}%  max={ds.max()/char_h*100:.3f}%  de la hauteur perso")
print(f"  ({'OK - mesh Unity = adulte Blender' if ds.mean()/char_h<0.01 else 'ecart notable'})")
