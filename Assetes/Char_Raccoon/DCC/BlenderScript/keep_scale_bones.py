"""
Marque des os pour GARDER leur scale non-uniforme à l'export (sinon le flatten
l'aplatit car ils ont des enfants).

À utiliser pour des os à enfants dont tu VEUX le squash non-uniforme (ex. museau),
quand l'enfant est quasi-aligné (le shear induit reste petit). Les os FEUILLES
gardent déjà leur scale automatiquement — pas besoin de les marquer.

⚠️ Compromis : l'enfant de l'os marqué prend un petit shear (≈ scale × sin(angle
de l'enfant)). OK si l'enfant est quasi-aligné (museau→nez ≈ 4.7° → ~quelques mm).

Édite BONES, lance dans l'éditeur de texte (Run Script), SAUVE le .blend.
"""

import bpy

# Os Def dont on garde le scale non-uniforme à l'export.
BONES = ["muzzle"]

DEF_PREFIX = "DEF-"


def main():
    defr = next((o for o in bpy.data.objects
                 if o.type == 'ARMATURE' and o.name.startswith(DEF_PREFIX)), None)
    if defr is None:
        print(f"❌ Aucune armature '{DEF_PREFIX}<Char>'.")
        return
    done = []
    for n in BONES:
        pb = defr.pose.bones.get(n)
        if pb is None:
            print(f"   ⚠️ os '{n}' absent de {defr.name}")
            continue
        pb["keep_nonuniform_scale"] = 1     # gardé tel quel à l'export
        done.append(n)
    bpy.context.view_layer.update()
    print(f"✅ scale non-uniforme GARDÉ à l'export pour : {done} (sur {defr.name})")
    print("   (Sauve le .blend. Les feuilles — joue/œil/sourcil/nez — sont déjà gardées.)")


if __name__ == "__main__":
    main()
