"""
Calcule les matrices de conversion par os pour la sérialisation .anim.

Modèle (validé empiriquement) :
    M̂_u(b)   = Ĝ @ W_b(b) @ H_b          mondes Unity re-mis en mètres
    L_unity(b,t) = scaleTrans_s( A_b @ L_blender(b,t) @ H_b )

 - H_b : rotation pure par os (basis FBX), translation ~0
 - A_b = H_parent^-1, ou Ĝ = diag(-1,1,1) pour les os racine (miroir X global)
 - s = 0.01 : les translations locales Unity sont en mètres/100
   (compensé par le scale ×100 du nœud Def) — appliqué SEULEMENT aux translations.

Vérifie : reconstruction rest exacte + erreur monde sur la pose animée Test 1.
Sortie : AnimExport/core/unity_basis.json
"""
import json, os, re
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = os.path.normpath(os.path.join(HERE, "..", "AnimExport", "core", "unity_basis.json"))

S = 0.01   # translations Unity = mètres * S


def load(n):
    txt = open(n).read()
    try:
        return json.loads(txt)                              # InvariantCulture (point décimal)
    except json.JSONDecodeError:
        return json.loads(re.sub(r'(\d),(\d)', r'\1.\2', txt))  # locale FR (virgule décimale)


def trs_to_mat(d):
    q = Quaternion(d["quat"])
    m = q.to_matrix().to_4x4()
    for i in range(3):
        for j in range(3):
            m[i][j] *= d["scale"][j]
    m.translation = Vector(d["pos"])
    return m


def scale_trans(m, s):
    m = m.copy()
    m.translation = m.translation * s
    return m


b_rest = load("blender_rest.json")
u_rest = load("unity_rest.json")

G_MIR = Matrix.Diagonal((1.0, 1.0, -1.0, 1.0))   # miroir Z (mesuré sur le modèle réel)

# --- M̂_u : chaîne des locaux Unity remis en mètres (translations ×1/S) ---
u_local = {p[len("Def/"):]: trs_to_mat(d) for p, d in u_rest.items()
           if p.startswith("Def/")}
m_hat = {}
for p in sorted(u_local, key=lambda x: x.count("/")):
    par = p.rsplit("/", 1)[0] if "/" in p else None
    loc = scale_trans(u_local[p], 1.0 / S)
    m_hat[p] = (m_hat[par] @ loc) if par else loc

# --- Mondes Blender rest ---
bw = {}
def bworld(n):
    if n in bw: return bw[n]
    m = trs_to_mat(b_rest[n])
    p = b_rest[n]["parent"]
    if p: m = bworld(p) @ m
    bw[n] = m
    return m

# --- H_b = (Ĝ @ W_b)^-1 @ M̂_u ---
H, path_of = {}, {}
max_ht = 0.0
for p in m_hat:
    bone = p.split("/")[-1]
    if bone not in b_rest:
        print(f"⚠ os Unity absent de Blender : {p}")
        continue
    Hb = (G_MIR @ bworld(bone)).inverted() @ m_hat[p]
    H[bone] = Hb
    path_of[bone] = "Def/" + p
    max_ht = max(max_ht, Hb.translation.length)

print(f"os : {len(H)}   |translation H| max = {max_ht:.6f}  (doit être ~0)")

# --- A_b ---
A = {}
for bone in H:
    par = b_rest[bone]["parent"]
    A[bone] = H[par].inverted() if (par and par in H) else G_MIR

# --- formule complète ---
def L_unity(bone, L_blender):
    return scale_trans(A[bone] @ L_blender @ H[bone], S)

# --- sanity 1 : rest reconstruit == locaux Unity rest ---
err = 0.0
for p in u_local:
    bone = p.split("/")[-1]
    if bone not in H: continue
    par = b_rest[bone]["parent"]
    Lb = (bworld(par).inverted() @ bworld(bone)) if par else bworld(bone)
    pred = L_unity(bone, Lb)
    err = max(err, max(abs(pred[i][j] - u_local[p][i][j])
                       for i in range(4) for j in range(4)))
print(f"sanity rest : erreur max locaux = {err:.2e}")

# --- sanity 2 : pose animée Test 1, comparaison MONDE ---
try:
    b_pose = load("blender_pose_test1.json")
    u_pose = load("unity_pose_test1.json")
    defM = Matrix([u_pose["_defMatrix"][i*4:(i+1)*4] for i in range(4)])

    pw = {}
    def pworld(n):
        if n in pw: return pw[n]
        m = trs_to_mat(b_pose[n])
        p = b_rest[n]["parent"]
        if p: m = pworld(p) @ m
        pw[n] = m
        return m

    # chaîne Unity prédite (avec recomposition TRS comme le YAML)
    uw = {}
    for p in sorted(u_local, key=lambda x: x.count("/")):
        bone = p.split("/")[-1]
        if bone not in H: continue
        par_b = b_rest[bone]["parent"]
        Lb = (pworld(par_b).inverted() @ pworld(bone)) if par_b else pworld(bone)
        Lu = L_unity(bone, Lb)
        loc, q, sc = Lu.decompose()
        m = q.to_matrix().to_4x4()
        for i in range(3):
            for j in range(3):
                m[i][j] *= sc[j]
        m.translation = loc
        par_p = p.rsplit("/", 1)[0] if "/" in p else None
        uw[p] = (uw[par_p] @ m) if par_p else m

    errs = []
    for p in uw:
        bone = p.split("/")[-1]
        got = defM @ uw[p].translation                  # monde Unity (mètres)
        # cible : monde Blender miroité, en passant par defM (translation defM = 0)
        tgt = (defM @ (G_MIR @ pworld(bone).translation)) * S
        errs.append(((tgt - got).length, bone))
    errs.sort(reverse=True)
    mean = sum(e for e, _ in errs) / len(errs)
    print(f"sanity pose : monde  moyenne={mean:.5f} m   max={errs[0][0]:.5f} m ({errs[0][1]})")
    for e, b in errs[:5]:
        print(f"     {e:.5f}  {b}")
except FileNotFoundError:
    print("(pas de pose animée — sanity 2 sautée)")

# --- export ---
out = {}
for bone in H:
    out[bone] = {"path": path_of[bone],
                 "A": [v for row in A[bone] for v in row],
                 "H": [v for row in H[bone] for v in row],
                 "s": S}
with open(OUT, "w") as fh:
    json.dump(out, fh)
print(f"→ {OUT}")
