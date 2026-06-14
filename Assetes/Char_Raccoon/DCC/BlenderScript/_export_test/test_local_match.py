"""
Pour chaque variante de modèle : unity_local_rest == blender_local_rest ?
Si OUI (résidu ~0) pour les os NON-racine → la conversion est GLOBALE,
donc le writer .anim peut stocker blender_local directement (pas de
conjugaison par-os, pas de shear) et le non-uniforme passe.
"""
import json, os, re
from mathutils import Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)

def load(n):
    return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', open(n).read()))

def local3(d):
    m = Quaternion(d["quat"]).to_matrix()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    return m

b = load("blender_rest.json")   # parent-relatif Def

for var in ("var_native", "var_unity"):
    fn = f"unity_rest_{var}.json"
    if not os.path.exists(fn):
        print(f"{var}: absent"); continue
    u = load(fn)
    u_loc = {}
    depth = {}
    for path, d in u.items():
        seg = path.split("/")
        if "Def" not in seg:
            continue
        bone = seg[-1]
        if bone in b:
            u_loc[bone] = local3(d)
            depth[bone] = len(seg)
    if not u_loc:
        print(f"{var}: aucun os"); continue
    dmin = min(depth.values())
    # comparaison directe unity_local vs blender_local (3x3), os non-racine
    worst = 0.0; wname = ""; n = 0
    for bone, Ul in u_loc.items():
        if depth[bone] == dmin:      # saute la racine (porte le flip global)
            continue
        Bl = local3(b[bone])
        diff = max(abs(Ul[i][j]-Bl[i][j]) for i in range(3) for j in range(3))
        if diff > worst: worst, wname = diff, bone
        n += 1
    print(f"{var:12}: |unity_local - blender_local| max = {worst:.4f}  ({wname}, {n} os)")
