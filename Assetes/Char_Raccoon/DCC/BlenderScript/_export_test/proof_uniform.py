"""
PREUVE : le scale UNIFORME s'exporte sans shear, le NON-uniforme non.

Pour la pose adulte (frame 24), on construit deux variantes des locaux Def :
  (1) NON-uniforme  = tel quel (STRETCH_TO)
  (2) UNIFORME      = même os mais scale remplacé par moyenne géométrique

Pour chacune, on applique la formule EXACTE du writer (A @ L @ H), on
decompose→recompose (ce que Unity fait avec localScale Vector3, perdant tout
shear), on rechaîne, et on mesure l'erreur 3x3 monde vs la cible.
Erreur ~0 ⇒ exportable. C'est la simulation fidèle de Unity (validée à 0 sur
frame 48).
"""
import json, os, re
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)

def load(n): return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', open(n).read()))

def trs(d):
    q = Quaternion(d["quat"]); m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"]); return m

b_rest = load("blender_rest.json")
b_pose = load("blender_pose_test2.json")
basis  = json.load(open(os.path.join("..", "AnimExport", "core", "unity_basis.json")))
A = {b: Matrix([d["A"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}
H = {b: Matrix([d["H"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}
path = {b: d["path"] for b, d in basis.items()}

def local_blender(name, uniform):
    """Local parent-relatif Def, scale tel quel ou uniformisé."""
    d = b_pose[name]
    sx, sy, sz = d["scale"]
    if uniform:
        s = (abs(sx*sy*sz)) ** (1/3)
        sc = (s, s, s)
    else:
        sc = (sx, sy, sz)
    q = Quaternion(d["quat"]); m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= sc[j]
    m.translation = Vector(d["pos"]); return m

def parent_in_basis(b):
    p = b_rest[b]["parent"]
    while p and p not in basis:
        p = b_rest[p]["parent"]
    return p

order = sorted(basis, key=lambda b: path[b].count("/"))

for uniform in (False, True):
    # cible monde (avec shear éventuel) et chaîne "Unity" (TRS recomposé)
    target_w, achieved = {}, {}
    errs = []
    for b in order:
        p = parent_in_basis(b)
        Lb = local_blender(b, uniform)
        # cible monde Unity-space = A_chain... on travaille en local A@L@H
        Lu = A[b] @ Lb @ H[b]
        # cible monde = parent_target @ Lu
        tw = (target_w[p] @ Lu) if p else Lu
        target_w[b] = tw
        # Unity : decompose Lu → recompose (perd le shear)
        loc, q, sc = Lu.decompose()
        rec = q.to_matrix().to_4x4()
        for i in range(3):
            for j in range(3):
                rec[i][j] *= sc[j]
        rec.translation = loc
        aw = (achieved[p] @ rec) if p else rec
        achieved[b] = aw
        # erreur 3x3 relative
        nf = (sum((aw[i][j]-tw[i][j])**2 for i in range(3) for j in range(3)) /
              max(sum(tw[i][j]**2 for i in range(3) for j in range(3)), 1e-9)) ** 0.5
        errs.append((nf, b))
    errs.sort(reverse=True)
    label = "UNIFORME " if uniform else "NON-unif."
    m = sum(e for e, _ in errs) / len(errs)
    print(f"[{label}]  erreur 3x3 monde : moy={m*100:6.2f}%  max={errs[0][0]*100:6.2f}%  ({errs[0][1]})")
