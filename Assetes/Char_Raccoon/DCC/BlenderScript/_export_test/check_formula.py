"""
Test de la formule de basis en maths pures (sans YAML) :

  L_u(b,t) = B_p^-1 @ L_b(b,t) @ B_b          puis décomposé/recomposé TRS
  monde    = defM @ chaîne(L_u)
  cible    = mirrorX( monde_blender(frame 24) )      [vérifié à la rest pose]

Compare aussi AVEC et SANS recomposition TRS (perte de shear) pour isoler
l'effet du scale non-uniforme du STRETCH_TO.
"""
import json, os, re
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

def load(n):
    txt = open(n).read()
    return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', txt))

def trs_to_mat(d):
    q = Quaternion(d["quat"])
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"])
    return m

b_rest = load("blender_rest.json")
b_pose = load("blender_pose_test1.json")
u_pose = load("unity_pose_test1.json")
basis  = json.load(open(os.path.join("..", "AnimExport", "core", "unity_basis.json")))

defM = Matrix([u_pose["_defMatrix"][i*4:(i+1)*4] for i in range(4)])
MIR  = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))

B    = {b: Matrix([d["B"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}
path = {b: d["path"] for b, d in basis.items()}

# Monde blender pose (armature space)
bw = {}
def bchain(n):
    if n in bw: return bw[n]
    m = trs_to_mat(b_pose[n])
    p = b_rest[n]["parent"]
    if p: m = bchain(p) @ m
    bw[n] = m
    return m

# L_u par formule, avec et sans recomposition TRS
def compute_chain(decompose_trs):
    uw = {}
    order = sorted((b for b in basis), key=lambda b: path[b].count("/"))
    for b in order:
        p = b_rest[b]["parent"]
        L = trs_to_mat(b_pose[b])
        Lu = (B[p].inverted() @ L @ B[b]) if (p and p in B) else (L @ B[b])
        if decompose_trs:
            loc, q, sc = Lu.decompose()
            m = q.to_matrix().to_4x4()
            for i in range(3):
                for j in range(3):
                    m[i][j] *= sc[j]
            m.translation = loc
            Lu = m
        uw[b] = (uw[p] @ Lu) if (p and p in B) else Lu
    return uw

for mode, label in ((False, "matrice exacte (avec shear)"),
                    (True,  "recomposé TRS (comme le YAML)")):
    uw = compute_chain(mode)
    errs = []
    for b in basis:
        target = MIR @ (defM @ bchain(b).translation) * 0.01 * 100  # defM inclut x100
        # cible : monde blender mètres, miroir X  (defM/100 = axes, voir diag A)
        tgt = MIR @ ((defM @ bchain(b).translation) * 0.01)
        got = (defM @ uw[b].translation) * 0.01
        errs.append(((tgt - got).length, b))
    errs.sort(reverse=True)
    mean = sum(e for e, _ in errs) / len(errs)
    print(f"{label:32}  moyenne={mean:.5f} m   max={errs[0][0]:.5f} m  ({errs[0][1]})")
    for e, b in errs[:4]:
        print(f"     {e:.5f}  {b}")
