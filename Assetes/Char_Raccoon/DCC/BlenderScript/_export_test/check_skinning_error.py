"""
Erreur de SKINNING au pic adulte (frame 24).
Compare, pour chaque os, la matrice MONDE Unity réelle (dump) contre la cible
Blender — décomposée en : écart d'orientation (axes normalisés) + écart de
longueur d'axe (scale) + écart de tête. Met en évidence le SHEAR irréductible.
"""
import json, os, re
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

def load(n):
    return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', open(n).read()))

def trs_to_mat(d):
    q = Quaternion(d["quat"]); m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"]); return m

b_rest = load("blender_rest.json")
b_pose = load("blender_pose_test2.json")
u_pose = load("unity_pose_test2.json")
basis  = json.load(open(os.path.join("..", "AnimExport", "core", "unity_basis.json")))

G = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))
H = {b: Matrix([d["H"][i*4:(i+1)*4] for i in range(4)]) for b, d in basis.items()}

# Monde Unity réel : chaîne des locaux dumpés, translations remises en mètres (/0.01)
u_local = {p[len("Def/"):]: trs_to_mat(d) for p, d in u_pose.items() if p.startswith("Def/")}
for m in u_local.values():
    m.translation = m.translation * 100.0           # mètres
u_world = {}
for p in sorted(u_local, key=lambda x: x.count("/")):
    par = p.rsplit("/", 1)[0] if "/" in p else None
    u_world[p] = (u_world[par] @ u_local[p]) if par else u_local[p]

pw = {}
def pworld(n):
    if n in pw: return pw[n]
    m = trs_to_mat(b_pose[n]); p = b_rest[n]["parent"]
    if p: m = pworld(p) @ m
    pw[n] = m; return m

def axis(M, c): return Vector((M[0][c], M[1][c], M[2][c]))

errs = []
for p, Wu in u_world.items():
    bone = p.split("/")[-1]
    if bone not in H: continue
    Wt = G @ pworld(bone) @ H[bone]                 # cible monde (M̂, mètres)
    ang = max((axis(Wu, c).angle(axis(Wt, c)) if axis(Wu, c).length and axis(Wt, c).length else 0)
              for c in range(3))
    lu = [axis(Wu, c).length for c in range(3)]
    lt = [axis(Wt, c).length for c in range(3)]
    sd = max(abs(lu[c]-lt[c]) / max(lt[c], 1e-6) for c in range(3))
    head = (Wu.translation - Wt.translation).length
    errs.append((ang, sd, head, bone, lu, lt))

errs.sort(key=lambda e: e[0] + e[1], reverse=True)
print(f"{'os':22} {'orient°':>8} {'scale%':>8} {'tête':>8}")
for ang, sd, head, bone, lu, lt in errs[:14]:
    import math
    print(f"{bone:22} {math.degrees(ang):8.2f} {sd*100:8.1f} {head:8.4f}")
ma = sum(e[0] for e in errs)/len(errs)
ms = sum(e[1] for e in errs)/len(errs)
mh = sum(e[2] for e in errs)/len(errs)
import math
print(f"\nMOYENNE  orient={math.degrees(ma):.2f}°  scale={ms*100:.1f}%  tête={mh:.4f} m")
print(f"os avec orient>5° : {sum(1 for e in errs if math.degrees(e[0])>5)}")
print(f"os avec scale>10% : {sum(1 for e in errs if e[1]>0.10)}")
