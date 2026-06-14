"""
Pour chaque variante de modèle, cherche s'il existe UNE reflexion/rotation
GLOBALE M (parmi 48 permutations signées) telle que, pour TOUS les os :
    Unity_local(b) ≈ M · Blender_local(b) · M⁻¹   (conjugaison globale)

Si oui avec résidu ~0 → la conversion est une conjugaison axis-aligned globale,
qui COMMUTE avec le scale diagonal → AUCUN shear → export du morph OK sans
toucher au rig. On compare la partie 3x3 (rotation+scale), translation à part.
"""
import json, os, re, itertools
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

def load(n):
    return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', open(n).read()))

def blocal_3x3(d):
    q = Quaternion(d["quat"]); m = q.to_matrix()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    return m

def signed_perms():
    out = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1.0, -1.0), repeat=3):
            M = Matrix(((0,0,0),(0,0,0),(0,0,0)))
            for i,(p,s) in enumerate(zip(perm,sg)):
                M[i][p] = s
            out.append((perm, sg, M))
    return out

b_rest = load("blender_rest.json")
# parent map pour exclure les racines si besoin
variants = ["var_Y_X", "var_X_Y", "var_negY_X"]

for var in variants:
    fn = f"unity_rest_{var}.json"
    if not os.path.exists(fn):
        print(f"{var}: dump absent"); continue
    u = load(fn)
    # locaux Unity 3x3 par nom d'os (dernier segment), exclure meshes & racine Def
    u_loc = {}
    for path, d in u.items():
        seg = path.split("/")
        bone = seg[-1]
        if bone in b_rest and "Def" in seg:        # sous l'armature
            m = Quaternion(d["quat"]).to_matrix()
            for i in range(3):
                for j in range(3):
                    m[i][j] *= d["scale"][j]
            u_loc[bone] = (m, len(seg))
    # exclure le 1er os sous Def (porte le scale global du noeud) : profondeur min
    if not u_loc:
        print(f"{var}: aucun os matché"); continue
    dmin = min(v[1] for v in u_loc.values())
    common = [b for b in u_loc if u_loc[b][1] > dmin and b in b_rest]

    best = None
    for perm, sg, M in signed_perms():
        Mi = M.inverted()
        worst = 0.0
        for b in common:
            Bl = blocal_3x3(b_rest[b])
            pred = M @ Bl @ Mi
            U = u_loc[b][0]
            diff = max(abs(pred[i][j]-U[i][j]) for i in range(3) for j in range(3))
            if diff > worst: worst = diff
            if worst > (best[0] if best else 1e9): break
        if best is None or worst < best[0]:
            best = (worst, perm, sg)
    ax="xyz"
    fmt="("+", ".join(f"{'-' if s<0 else ''}{ax[p]}" for p,s in zip(best[1],best[2]))+")"
    print(f"{var:12} : meilleur M global {fmt}  résidu max 3x3 = {best[0]:.4f}   (os testés {len(common)})")
