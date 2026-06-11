# ============================================================================
#  Configuration de l'exporteur d'animation
# ============================================================================

# Objet qui PORTE les animations (les Actions y sont assignées).
# C'est le rig de contrôle généré par Rigify, que l'animateur manipule.
ANIM_SOURCE = "RIG-CtrlRig"

# Objet de DÉFORMATION exporté (baked). Piloté par ANIM_SOURCE via
# contraintes copy-transform + drivers.
DEF_ARMATURE = "Def"

# Dossier de sortie (chemin Blender relatif au .blend, '//' = dossier du .blend).
# Le .blend est dans  ...\Char_Raccoon\DCC\  → on remonte vers la racine projet
# puis on descend dans le projet Unity : Limen\Assets\Animations
# Fixé ici (côté TD) — volontairement PAS exposé dans l'UI de l'animateur.
EXPORT_DIR = "//../../../Limen/Assets/Animations"
