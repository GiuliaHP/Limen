import bpy, sys, os, json, re
from mathutils import Matrix
HERE = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript/_export_test"
sys.path.insert(0, r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript")

def load(n):
    # fbxclip_*.json = InvariantCulture (point décimal, virgule séparateur) → pas de regex
    return json.loads(open(os.path.join(HERE,n)).read())

def mat(flat):  # 16 floats row-major -> Matrix
    return Matrix([flat[0:4], flat[4:8], flat[8:12], flat[12:16]])

fa = load("fbxclip_world_a.json"); fb = load("fbxclip_world_b.json")
ta, tb = fa["_t"], fb["_t"]
G = mat(fa["Def"])   # noeud armature Unity (constant)

# setup rig + Test 1
from SetupDefContrites import Contrites_core as sdc
sdc.reload_core(); sdc.clear_rig_data("Def")
ctrl=bpy.data.objects["RIG-CtrlRig"]; defr=bpy.data.objects["Def"]
sdc.apply_constraints_from_dict(defr, ctrl, sdc.MAPPING_DICT)
from AnimExport import core as ac; ac.reload_core()
from AnimExport.core import exporter
a=bpy.data.actions["Test 1"]
exporter._reset_to_default(ctrl); exporter._assign_action(ctrl, a)
fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base

def blender_world_at(t):
    fr = t*fps
    bpy.context.scene.frame_set(int(fr), subframe=fr-int(fr))
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); ev=defr.evaluated_get(dg)
    return {pb.name: pb.matrix.copy() for pb in ev.pose.bones}

Ba = blender_world_at(ta); Bb = blender_world_at(tb)

# pour chaque os : C = (G @ Bmat_a)^-1 @ Uworld_a ; vérifier sur frame b
def uworld(f, bone):
    key = "Def/"+ ("/".join(_path(bone)))
    return mat(f[key]) if key in f else None

# construire le chemin Unity depuis la hiérarchie des os Def
defbones = {b.name:b for b in defr.data.bones}
def _path(bone):
    parts=[]; cur=defbones.get(bone)
    while cur: parts.append(cur.name); cur=cur.parent
    parts.reverse(); return parts

import math
worst=0; nconst=0; ntot=0; worst_bone=""
results={}
for bone in Ba:
    Ua = uworld(fa, bone); Ub = uworld(fb, bone)
    if Ua is None or Ub is None: continue
    C = (G @ Ba[bone]).inverted() @ Ua
    # vérif frame b
    pred = (G @ Bb[bone]) @ C
    err = max(abs(pred[i][j]-Ub[i][j]) for i in range(4) for j in range(4))
    ntot+=1
    if err<1e-3: nconst+=1
    if err>worst: worst=err; worst_bone=bone
    results[bone]=C
print(f"os testés: {ntot}  C_b constant (err<1e-3): {nconst}  pire err: {worst:.5f} ({worst_bone})")

# --- construire la basis (A = H_parent^-1, H = C_b) et l'écrire ---
# ordre parents d'abord
order = sorted([b for b in results], key=lambda b: len(_path(b)))
H = {}   # bone -> C_b
for b in order: H[b] = results[b]
out = {}
for b in order:
    path = "Def/" + "/".join(_path(b))
    par = defbones[b].parent
    while par and par.name not in H: par = par.parent
    A = H[par.name].inverted() if par else Matrix.Diagonal((1,1,1,1)).to_4x4()
    # racine : A telle que Unity_local(root)=A@Bmat@C_b => A = (G applied)... on prend A=G^-1? 
    if not par:
        A = G.inverted() @ Matrix.Identity(4)  # root: world = G@Bmat@C => local(=world here under Def)= G^-1... 
        # en fait pour la racine sous Def, Unity_local = G^-1 @ Uworld = Bmat @ C_b => A = identité? non:
        A = Matrix.Identity(4)
    out[b] = {"path": path,
              "A":[v for r in A for v in r],
              "H":[v for r in H[b] for v in r],
              "s":1.0}
import json as _j
OUT=os.path.normpath(os.path.join(HERE,"..","AnimExport","core","unity_basis.json"))
open(OUT,"w").write(_j.dumps(out))
print("BASIS FBX-calibrée écrite:", len(out), "os ->", OUT)
