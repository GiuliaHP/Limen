"""
Résout la conversion Blender → Unity à partir des dumps réels.

Hypothèse : Unity_local = S · Blender_local · S⁻¹ avec S une permutation signée
des axes (48 candidats). On teste chaque S sur tous les os de la rest pose et
on garde ceux qui matchent. Vérification ensuite sur la pose animée.
"""
import json, os, sys, itertools, math, re

HERE = os.path.dirname(os.path.abspath(__file__))


# --- mini algèbre 3x3 / quaternions (sans numpy) ---

def quat_to_mat(q):
    w, x, y, z = q
    return [
        [1-2*(y*y+z*z), 2*(x*y-w*z),   2*(x*z+w*y)],
        [2*(x*y+w*z),   1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y),   2*(y*z+w*x),   1-2*(x*x+y*y)],
    ]

def mat_mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def mat_T(a):
    return [[a[j][i] for j in range(3)] for i in range(3)]

def mat_vec(a, v):
    return [sum(a[i][k]*v[k] for k in range(3)) for i in range(3)]

def mat_diff(a, b):
    return max(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3))

def vec_diff(a, b):
    return max(abs(a[i]-b[i]) for i in range(3))


# --- 48 permutations signées ---

def signed_perms():
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            S = [[0.0]*3 for _ in range(3)]
            for i, (p, s) in enumerate(zip(perm, signs)):
                S[i][p] = float(s)
            out.append((perm, signs, S))
    return out


def load(name):
    with open(os.path.join(HERE, name)) as fh:
        txt = fh.read()
    # locale FR : virgules décimales (les séparateurs JSON ont une espace après)
    txt = re.sub(r'(\d),(\d)', r'\1.\2', txt)
    return json.loads(txt)


def unity_bones(unity):
    """Unity dump : chemins 'Def/root/...' → nom du dernier segment."""
    out = {}
    for path, d in unity.items():
        if path.startswith("_") or "/" not in path and path != "Def":
            if not path.startswith("Def"):
                continue
        if not path.split("/")[0] == "Def":
            continue
        name = path.split("/")[-1]
        if name == "Def":
            continue
        out[name] = d
    return out


def test_candidates(blender, unity, tol_rot=2e-2, tol_pos=1e-3, skip_root=True):
    results = []
    for perm, signs, S in signed_perms():
        St = mat_T(S)
        n_ok = n_tot = 0
        worst_rot = worst_pos = 0.0
        for bone, bd in blender.items():
            if bone not in unity:
                continue
            if skip_root and bd.get("parent") is None:
                continue   # le root est sous le nœud Def (conversion d'axes) → à part
            ud = unity[bone]
            Rb = quat_to_mat(bd["quat"])
            Ru = quat_to_mat(ud["quat"])
            pred_R = mat_mul(mat_mul(S, Rb), St)
            pred_t = mat_vec(S, bd["pos"])
            dr = mat_diff(pred_R, Ru)
            dp = vec_diff(pred_t, ud["pos"])
            worst_rot = max(worst_rot, dr)
            worst_pos = max(worst_pos, dp)
            n_tot += 1
            if dr < tol_rot and dp < tol_pos:
                n_ok += 1
        if n_tot:
            results.append((n_ok / n_tot, worst_rot, worst_pos, perm, signs))
    results.sort(reverse=True)
    return results


def fmt(perm, signs):
    ax = "xyz"
    return "(" + ", ".join(f"{'-' if s < 0 else ''}{ax[p]}" for p, s in zip(perm, signs)) + ")"


def main():
    blender = load("blender_rest.json")
    unity   = unity_bones(load("unity_rest.json"))
    common  = set(blender) & set(unity)
    print(f"os Blender: {len(blender)}, Unity: {len(unity)}, communs: {len(common)}")
    if len(common) < 10:
        print("⚠ correspondance de noms trop faible — vérifier les chemins Unity")
        for k in list(unity)[:10]:
            print("  unity:", k)
        sys.exit(1)

    print("\n--- top 6 candidats (rest pose) ---")
    res = test_candidates(blender, unity)
    for score, wr, wp, perm, signs in res[:6]:
        print(f"  score={score*100:5.1f}%  worst_rot={wr:.4f}  worst_pos={wp:.5f}"
              f"   pos_unity = S·pos_blender, S: {fmt(perm, signs)}")

    # racine (root, parent=None) : à traiter séparément
    best = res[0]
    perm, signs, = best[3], best[4]
    S = [[0.0]*3 for _ in range(3)]
    for i, (p, s) in enumerate(zip(perm, signs)):
        S[i][p] = float(s)
    if "root" in blender and "root" in unity:
        bd, ud = blender["root"], unity["root"]
        pred_R = mat_mul(mat_mul(S, quat_to_mat(bd["quat"])), mat_T(S))
        print(f"\nroot : pred vs unity rot diff = "
              f"{mat_diff(pred_R, quat_to_mat(ud['quat'])):.4f}, "
              f"pos pred={mat_vec(S, bd['pos'])} vs unity={ud['pos']}")

    # validation sur la pose animée si dispo
    try:
        bp = {k: v for k, v in load("blender_pose_test1.json").items() if not k.startswith("_")}
        up = unity_bones(load("unity_pose_test1.json"))
        print("\n--- validation pose animée Test 1 (frame milieu) ---")
        res2 = test_candidates(bp, {k: v for k, v in up.items()},
                               tol_rot=5e-2, tol_pos=5e-3, skip_root=False)
        for score, wr, wp, perm, signs in res2[:3]:
            print(f"  score={score*100:5.1f}%  worst_rot={wr:.4f}  worst_pos={wp:.5f}"
                  f"   S: {fmt(perm, signs)}")
    except FileNotFoundError:
        print("\n(pose animée Unity absente — validation rest uniquement)")


if __name__ == "__main__":
    main()
