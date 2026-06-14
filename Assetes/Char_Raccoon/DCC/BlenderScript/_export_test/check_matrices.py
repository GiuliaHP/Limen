"""
Erreur de SKINNING : compare les matrices 3x3 complètes (pas juste les têtes)
entre la chaîne TRS reproduite par Unity et la cible Blender, pour Test 2
frame finale (adulte). Teste aussi un fit TRS par décomposition polaire (SVD).
"""
import json, os, re
import numpy as np
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
b_pose = load("blender_pose_test2.json")
basis  = json.load(open(os.path.join("..", "AnimExport", "core", "unity_basis.json")))

G_MIR = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
H    = {b: Matrix([d["H"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}
path = {b: d["path"] for b, d in basis.items()}

# Mondes blender pose
pw = {}
def pworld(n):
    if n in pw: return pw[n]
    m = trs_to_mat(b_pose[n])
    p = b_rest[n]["parent"]
    if p: m = pworld(p) @ m
    pw[n] = m
    return m

def parent_in_basis(b):
    p = b_rest[b]["parent"]
    while p and p not in basis:
        p = b_rest[p]["parent"]
    return p

def trs_recompose(loc, q, sc):
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= sc[j]
    m.translation = loc
    return m

def fit_naive(L):
    return trs_recompose(*L.decompose())

def fit_polar(L):
    """Meilleur TRS : rotation par décomposition polaire (SVD), scale diagonal."""
    M = np.array([[L[i][j] for j in range(3)] for i in range(3)])
    U, s, Vt = np.linalg.svd(M)
    R = U @ Vt
    if np.linalg.det(R) < 0:                      # éviter les réflexions
        U[:, -1] *= -1
        R = U @ Vt
    K = R.T @ M                                   # symétrique ~PSD (stretch)
    scale = np.diag(K).copy()
    out = Matrix(((R[0][0]*scale[0], R[0][1]*scale[1], R[0][2]*scale[2], L[0][3]),
                  (R[1][0]*scale[0], R[1][1]*scale[1], R[1][2]*scale[2], L[1][3]),
                  (R[2][0]*scale[0], R[2][1]*scale[1], R[2][2]*scale[2], L[2][3]),
                  (0, 0, 0, 1)))
    return out

order = sorted(basis, key=lambda b: path[b].count("/"))

for fit, label in ((fit_naive, "decompose() naïf"), (fit_polar, "polaire SVD")):
    achieved = {}
    errs3, errsh = [], []
    for b in order:
        target = G_MIR @ pworld(b) @ H[b]
        p = parent_in_basis(b)
        L = (achieved[p].inverted() @ target) if p else target
        rec = fit(L)
        achieved[b] = (achieved[p] @ rec) if p else rec
        A, T = achieved[b], target
        # erreur relative 3x3 (norme F) + erreur tête
        nf = (sum((A[i][j]-T[i][j])**2 for i in range(3) for j in range(3)) /
              max(sum(T[i][j]**2 for i in range(3) for j in range(3)), 1e-12)) ** 0.5
        errs3.append((nf, b))
        errsh.append(((A.translation - T.translation).length, b))
    errs3.sort(reverse=True); errsh.sort(reverse=True)
    m3 = sum(e for e, _ in errs3)/len(errs3)
    print(f"\n[{label}]  3x3 rel: moy={m3*100:.2f}%  max={errs3[0][0]*100:.2f}% ({errs3[0][1]})"
          f"   têtes: max={errsh[0][0]:.5f} m")
    for e, b in errs3[:6]:
        print(f"     {e*100:7.2f}%  {b}")
