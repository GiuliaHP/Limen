"""Cœur de conversion : pose locale Blender → pose locale Unity.

Une seule formule, validée empiriquement (~2 mm vs vérité-terrain FBX) :

    dB        = Bbinv @ L_blender          (delta depuis le bind)
    dB.trans *= s                          (mètres → mètres/100)
    L_unity   = Ubind @ Q^-1 @ dB @ Q      (retarget dans l'espace Unity)
"""


def bone_local(ev_armature, pose_bone):
    """Matrice locale de l'os relative à son parent (espace armature évalué)."""
    pb = pose_bone
    if pb.parent:
        return ev_armature.pose.bones[pb.parent.name].matrix.inverted() @ pb.matrix
    return pb.matrix.copy()


def retarget_local(local_blender, entry):
    """Local Blender (Matrix) + BoneBasis → local Unity (Matrix)."""
    dB = entry.Bbinv @ local_blender
    dB.translation = dB.translation * entry.s
    return entry.Ubind @ entry.Q.inverted() @ dB @ entry.Q
