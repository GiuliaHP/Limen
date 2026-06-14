"""
Vérité terrain : compare les matrices MONDE complètes (3x3 + tête) des os
RÉELLEMENT échantillonnés par Unity (unity_pose_test2.json) contre les cibles
Blender. Détecte tout écart d'orientation/scale qui casserait le skinning.
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
b_pose = load("blender_pose_test2.json")
u_pose = load("unity_pose_test2.json")
basis  = json.load(open(os.path.join("..", "AnimExport", "core", "unity_basis.json")))

G_MIR = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
H    = {b: Matrix([d["H"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}
defM = Matrix([u_pose["_defMatrix"][i*4:(i+1)*4] for i in range(4)])

# Monde Unity réel = chaîne des locaux dumpés (sous Def), translations en mètres
u_local = {p[len("Def/"):]: trs_to_mat(d) for p, d in u_pose.items()
           if p.startswith("Def/")}
u_world = {}
for p in sorted(u_local, key=lambda x: x.count("/")):
    par = p.rsplit("/", 1)[0] if "/" in p else None
    # garder translations Unity telles quelles (mètres) → monde via defM
    u_world[p] = (u_world[par] @ u_local[p]) if par else u_local[p]

# Cible Blender monde : Ĝ @ W_blender @ H, puis amenée dans le repère Unity
pw = {}
def pworld(n):
    if n in pw: return pw[n]
    m = trs_to_mat(b_pose[n])
    p = b_rest[n]["parent"]
    if p: m = pworld(p) @ m
    pw[n] = m
    return m

# defM mappe l'espace M̂ (mètres) → monde Unity. defM contient déjà x100 + axes.
# u_world est en "locaux Unity" (mètres/100 enchaînés) → monde = defM @ u_world.
errs = []
for p, Mu in u_world.items():
    bone = p.split("/")[-1]
    if bone not in H: continue
    Wu = defM @ Mu                                   # monde Unity réel
    Wt = (defM * 0.01) @ (G_MIR @ pworld(bone) @ H[bone])   # cible (s=0.01)
    # normaliser : comparer orientations des axes (colonnes 3x3 normalisées)
    def axes(M):
        out = []
        for c in range(3):
            v = Vector((M[0][c], M[1][c], M[2][c]))
            out.append(v.normalized())
        return out
    au, at = axes(Wu), axes(Wt)
    ang = max((au[c].angle(at[c]) if au[c].length and at[c].length else 0)
              for c in range(3))
    head = (Wu.translation - Wt.translation).length
    # longueurs des axes (scale monde)
    lu = [Vector((Wu[0][c], Wu[1][c], Wu[2][c])).length for c in range(3)]
    lt = [Vector((Wt[0][c], Wt[1][c], Wt[2][c])).length for c in range(3)]
    sd = max(abs(lu[c]-lt[c]) for c in range(3))
    errs.append((ang, sd, head, bone, lu, lt))

errs.sort(reverse=True)
print("écart d'ORIENTATION des axes (rad) — os les pires :")
for ang, sd, head, bone, lu, lt in errs[:8]:
    print(f"  {ang:.4f} rad  scaleΔ={sd:.4f}  tête={head:.5f}  {bone}")
    if ang > 0.01:
        print(f"        |axes|U={[round(v,3) for v in lu]}  cible={[round(v,3) for v in lt]}")

mean_ang = sum(e[0] for e in errs)/len(errs)
mean_sd  = sum(e[1] for e in errs)/len(errs)
print(f"\nmoy orientation={mean_ang:.5f} rad   moy scaleΔ={mean_sd:.5f}")
