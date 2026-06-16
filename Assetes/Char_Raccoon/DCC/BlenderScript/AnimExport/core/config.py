# ============================================================================
#  Configuration de l'exporteur d'animation (générique, pattern-based)
# ============================================================================
#
#  Aucun nom d'objet en dur : le personnage est résolu par pattern depuis
#  l'objet actif (cf. character.py) — armature "DEF-<Char>" / ctrl "RIG-<Char>".
#  Nommage : clips "ANIM_<Char>_<nom>", modèle "CHAR_<Char>.racmodel".

# Dossiers de sortie (relatifs au .blend) — communs à tous les persos.
EXPORT_DIR       = "//../../../Limen/Assets/Animations"   # .anim Unity
MODEL_EXPORT_DIR = "//../../../Limen/Assets/Models"       # .racmodel souverain
