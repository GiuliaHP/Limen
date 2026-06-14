# ============================================================================
#  Configuration de l'exporteur d'animation
# ============================================================================

# Objet qui PORTE les animations (les Actions y sont assignées).
ANIM_SOURCE = "RIG-CtrlRig"

# Objet de DÉFORMATION exporté. Piloté par ANIM_SOURCE via contraintes.
DEF_ARMATURE = "Def"

# Dossier .anim Unity  (chemin Blender relatif au .blend)
# .blend est dans  ...\Char_Raccoon\DCC\  →  3 niveaux  →  Limen\Assets\Animations
EXPORT_DIR = "//../../../Limen/Assets/Animations"

# Export du modèle (mesh + Def, rest pose, sans animation) → Unity Assets/Models
MODEL_EXPORT_DIR      = "//../../../Limen/Assets/Models"
MODEL_EXPORT_FILENAME = "Chara_Raccoon.fbx"
