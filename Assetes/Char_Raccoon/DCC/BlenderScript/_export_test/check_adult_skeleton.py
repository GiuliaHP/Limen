"""
Le rig de controle a-t-il des joints ADULTES plus longs (proportions par
translation, exportable), ou l'elongation est-elle uniquement inventee par le
STRETCH_TO (proportions par scale, non exportable) ?

Compare, pour chaque os Def, la longueur de segment Child vs Adult cote CTRL
(distance tete->tete de l'os suivant), via le MAPPING_DICT.
"""

import bpy
import sys

ROOT = r"P:/Chara_Giu/Limen/Assetes/Char_Raccoon/DCC/BlenderScript"
sys.path.insert(0, ROOT)
ctx = bpy.context


def run():
    from SetupDefContrites import Contrites_core as sdc
    sdc.reload_core()
    ctrl = bpy.data.objects["RIG-CtrlRig"]
    md = sdc.MAPPING_DICT

    # positions de repos des os ctrl (edit/rest, armature space) via data.bones
    cb = {b.name: b for b in ctrl.data.bones}

    def head(name):
        b = cb.get(name)
        return b.head_local.copy() if b else None

    def seg_len(name):
        """Longueur du segment de l'os ctrl (tete->queue rest)."""
        b = cb.get(name)
        return (b.tail_local - b.head_local).length if b else None

    print("=== longueur de segment CTRL : Child vs Adult (rest) ===")
    ratios = []
    for def_name, t in md.items():
        ch = (t.get('Child') or '').strip()
        ad = (t.get('Adult') or '').strip()
        lc = seg_len(ch); la = seg_len(ad)
        if lc and la and lc > 1e-5:
            r = la / lc
            ratios.append((r, def_name, lc, la))
    ratios.sort(reverse=True)
    print(f"  {len(ratios)} os mappes Child+Adult")
    print("  TOP elongation (ratio Adult/Child) :")
    for r, n, lc, la in ratios[:10]:
        print(f"     {n:24s} child={lc*100:6.2f}cm  adult={la*100:6.2f}cm  ratio={r:.2f}")
    import statistics
    rs = [r for r, *_ in ratios]
    print(f"  ratio median={statistics.median(rs):.2f}  min={min(rs):.2f}  max={max(rs):.2f}")
    big = sum(1 for r in rs if r > 1.1)
    print(f"  os dont l'os ADULTE ctrl est >10% plus long : {big}/{len(rs)}")
    print("  -> si beaucoup : les proportions adultes EXISTENT en translation (riggable sans scale)")
    print("  -> si ~tous a 1.0 : l'elongation est inventee par le stretch (rig a re-autoriser)")


run()
