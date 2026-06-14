using UnityEngine;
using UnityEditor;

/// <summary>
/// Configure automatiquement Chara_Raccoon.fbx à chaque (re)import :
///   - Generic rig, avatar depuis ce modèle, root motion sur l'os "root"
///   - Pas d'animation dans le FBX (les clips sont des .anim séparés)
///   - Blendshapes importées
///   - Assigne RaccoonAnim.controller sur l'Animator du modèle
/// </summary>
public class RaccoonImportSetup : AssetPostprocessor
{
    const string MODEL_PATH      = "Assets/Models/Chara_Raccoon.fbx";
    const string CONTROLLER_PATH = "Assets/Animations/RaccoonAnim.controller";
    const string ROOT_BONE       = "root";

    void OnPreprocessModel()
    {
        if (assetPath != MODEL_PATH) return;

        var mi = (ModelImporter)assetImporter;

        mi.animationType      = ModelImporterAnimationType.Generic;
        mi.avatarSetup        = ModelImporterAvatarSetup.CreateFromThisModel;
        mi.motionNodeName     = ROOT_BONE;
        mi.importAnimation    = false;
        mi.importBlendShapes  = true;
    }

    void OnPostprocessModel(GameObject root)
    {
        if (assetPath != MODEL_PATH) return;

        var animator = root.GetComponent<Animator>();
        if (animator == null) return;

        var ctrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(CONTROLLER_PATH);
        if (ctrl != null)
            animator.runtimeAnimatorController = ctrl;
        else
            Debug.LogWarning($"[RaccoonImport] Controller introuvable : {CONTROLLER_PATH}");
    }
}
