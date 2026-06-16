// Diagnostic générique : un clip .anim se lie-t-il au modèle .racmodel importé ?
// Menu Character > Diagnose Animation. Prend le 1er .racmodel + le 1er .anim trouvés,
// échantillonne et reporte la résolution des chemins + le mouvement réel.
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class CharAnimDiagnostic
{
    const string MODELS_DIR = "Assets/Models";
    const string ANIM_DIR = "Assets/Animations";

    [MenuItem("Character/Diagnose Animation")]
    public static void Diagnose()
    {
        var modelPath = Directory.GetFiles(MODELS_DIR, "*.racmodel").FirstOrDefault();
        if (modelPath == null) { Debug.LogError($"[Diag] aucun .racmodel dans {MODELS_DIR}"); return; }
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath.Replace('\\', '/'));
        if (prefab == null) { Debug.LogError($"[Diag] modèle illisible : {modelPath}"); return; }

        var animPath = Directory.GetFiles(ANIM_DIR, "*.anim").FirstOrDefault();
        if (animPath == null) { Debug.LogError($"[Diag] aucun .anim dans {ANIM_DIR}"); return; }
        animPath = animPath.Replace('\\', '/');
        var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(animPath);
        Debug.Log($"[Diag] clip = {clip.name}  (legacy={clip.legacy}, length={clip.length:F2}s)");

        var inst = Object.Instantiate(prefab);
        inst.hideFlags = HideFlags.HideAndDontSave;

        // 1) résolution des chemins
        var bindings = AnimationUtility.GetCurveBindings(clip);
        int total = bindings.Length, resolved = 0, missed = 0;
        string firstBonePath = null;
        foreach (var b in bindings)
        {
            var t = inst.transform.Find(b.path);
            if (t != null) { resolved++; if (firstBonePath == null && b.type == typeof(Transform)) firstBonePath = b.path; }
            else { missed++; if (missed <= 8) Debug.LogWarning($"[Diag] NON résolu: '{b.path}'  (type={b.type.Name}, prop={b.propertyName})"); }
        }
        Debug.Log($"[Diag] bindings résolus : {resolved}/{total}  (manqués={missed})");

        // exemples de chemins attendus vs hiérarchie réelle
        Debug.Log($"[Diag] ex. chemin clip : '{bindings.FirstOrDefault(b=>b.type==typeof(Transform)).path}'");
        var kids = "";
        foreach (Transform c in inst.transform) kids += c.name + ", ";
        Debug.Log($"[Diag] enfants directs du prefab : {kids}");

        // 2) le sample bouge-t-il un os ?
        if (firstBonePath != null)
        {
            var bone = inst.transform.Find(firstBonePath);
            var p0 = bone.position; var r0 = bone.rotation;
            clip.SampleAnimation(inst, clip.length * 0.5f);
            float dp = (bone.position - p0).magnitude;
            float dr = Quaternion.Angle(bone.rotation, r0);
            Debug.Log($"[Diag] sample t=50% sur '{firstBonePath}' : Δpos={dp*1000:F2}mm Δrot={dr:F2}°  → {(dp>1e-5||dr>1e-3 ? "BOUGE" : "STATIQUE")}");
        }

        // 3) controller assigné ?
        var anim = inst.GetComponent<Animator>();
        Debug.Log($"[Diag] Animator: avatar={(anim && anim.avatar ? anim.avatar.name : "AUCUN")}, controller={(anim && anim.runtimeAnimatorController ? anim.runtimeAnimatorController.name : "AUCUN")}, cullingMode={(anim ? anim.cullingMode.ToString() : "-")}");

        Object.DestroyImmediate(inst);
    }
}
