// ScriptedImporter souverain GÉNÉRIQUE : un fichier .racmodel (JSON exporté par
// blender_unity_anim/model_export.py) devient un vrai asset modèle Unity —
// glissable dans la scène, ré-importé auto comme un FBX, mais 100% notre code
// (aucun FBX). Le JSON est déjà en espace Unity → build verbatim.
//
// Marche pour N'IMPORTE QUEL perso : nom (CHAR_<Char>), os, meshes skinnés +
// rigides, blendshapes, matériaux embarqués. Le controller est dérivé du perso :
// Assets/Animations/<Char>.controller s'il existe.

using System.IO;
using System.Linq;
using Unity.Collections;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.AssetImporters;
using UnityEngine;

[ScriptedImporter(2, "racmodel")]
public class CharModelImporter : ScriptedImporter
{
    [System.Serializable] class BoneData { public string name; public int parent; public float[] pos; public float[] rot; public float[] scale; }
    [System.Serializable] class ShapeData { public string name; public float[] deltaVertices; }
    [System.Serializable] class MeshData {
        public string name;
        public float[] vertices; public float[] normals; public float[] uvs;
        public int[] triangles; public string[] materials; public int[] submeshIndexCounts;
        public int[] bonesPerVertex; public int[] boneIndices; public float[] boneWeights;
        public ShapeData[] blendshapes;
    }
    [System.Serializable] class RigidMeshData {
        public string name; public string bone;
        public float[] pos; public float[] rot; public float[] scale;
        public float[] vertices; public float[] normals; public float[] uvs;
        public int[] triangles; public string[] materials; public int[] submeshIndexCounts;
    }
    [System.Serializable] class MatDef { public string name; public float[] baseColor; public float metallic; public float smoothness; }
    [System.Serializable] class ModelData { public string name; public BoneData[] bones; public MeshData[] meshes; public RigidMeshData[] rigidMeshes; public MatDef[] materials; }

    public override void OnImportAsset(AssetImportContext ctx)
    {
        var model = JsonUtility.FromJson<ModelData>(File.ReadAllText(ctx.assetPath));
        if (model == null || model.bones == null || model.bones.Length == 0)
        { ctx.LogImportError("[Char] .racmodel invalide"); return; }

        if (QualitySettings.skinWeights != SkinWeights.Unlimited)
            QualitySettings.skinWeights = SkinWeights.Unlimited;   // poids >4/vertex

        var root = new GameObject(model.name);
        var matCache = new System.Collections.Generic.Dictionary<string, Material>();
        var matDefs = new System.Collections.Generic.Dictionary<string, MatDef>();
        if (model.materials != null) foreach (var d in model.materials) matDefs[d.name] = d;

        // 1. hiérarchie d'os (bind = TRS local verbatim)
        var boneTf = new Transform[model.bones.Length];
        int rootIdx = -1;
        for (int i = 0; i < model.bones.Length; i++)
        {
            var b = model.bones[i];
            var go = new GameObject(b.name);
            boneTf[i] = go.transform;
            boneTf[i].SetParent(b.parent >= 0 ? boneTf[b.parent] : root.transform, false);
            boneTf[i].localPosition = new Vector3(b.pos[0], b.pos[1], b.pos[2]);
            boneTf[i].localRotation = new Quaternion(b.rot[0], b.rot[1], b.rot[2], b.rot[3]);
            boneTf[i].localScale = new Vector3(b.scale[0], b.scale[1], b.scale[2]);
            if (b.parent < 0 && rootIdx < 0) rootIdx = i;
        }
        Transform rootBone = boneTf[rootIdx < 0 ? 0 : rootIdx];

        var bindposes = new Matrix4x4[boneTf.Length];
        for (int i = 0; i < boneTf.Length; i++)
            bindposes[i] = boneTf[i].worldToLocalMatrix * root.transform.localToWorldMatrix;

        // 2. meshes skinnés (sous-assets)
        foreach (var md in model.meshes)
        {
            var mesh = BuildMesh(md, bindposes);
            ctx.AddObjectToAsset(md.name + "_Mesh", mesh);

            var smrGO = new GameObject(md.name);
            smrGO.transform.SetParent(root.transform, false);
            var smr = smrGO.AddComponent<SkinnedMeshRenderer>();
            smr.sharedMesh = mesh;
            smr.bones = boneTf;
            smr.rootBone = rootBone;
            smr.localBounds = mesh.bounds;
            smr.sharedMaterials = ResolveMaterials(ctx, md.materials, md.name, matCache, matDefs);
        }

        // 2b. meshes RIGIDES (yeux, nez…) : MeshRenderer childé à l'os
        var boneByName = new System.Collections.Generic.Dictionary<string, Transform>();
        for (int i = 0; i < model.bones.Length; i++) boneByName[model.bones[i].name] = boneTf[i];
        if (model.rigidMeshes != null)
            foreach (var rm in model.rigidMeshes)
            {
                var mesh = BuildStaticMesh(rm);
                ctx.AddObjectToAsset(rm.name + "_Mesh", mesh);
                var go = new GameObject(rm.name);
                go.transform.SetParent(boneByName.TryGetValue(rm.bone, out var bt) ? bt : root.transform, false);
                go.transform.localPosition = new Vector3(rm.pos[0], rm.pos[1], rm.pos[2]);
                go.transform.localRotation = new Quaternion(rm.rot[0], rm.rot[1], rm.rot[2], rm.rot[3]);
                go.transform.localScale = new Vector3(rm.scale[0], rm.scale[1], rm.scale[2]);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                go.AddComponent<MeshRenderer>().sharedMaterials =
                    ResolveMaterials(ctx, rm.materials, rm.name, matCache, matDefs);
            }

        // 3. Animator + Avatar Generic + controller dérivé du perso
        var anim = root.AddComponent<Animator>();
        var avatar = AvatarBuilder.BuildGenericAvatar(root, rootBone.name);
        avatar.name = model.name + "_Avatar";
        if (avatar.isValid) { ctx.AddObjectToAsset("avatar", avatar); anim.avatar = avatar; }
        else ctx.LogImportWarning("[Char] Avatar Generic invalide");

        // <Char> = nom du modèle sans le préfixe "CHAR_"
        string charName = model.name.StartsWith("CHAR_") ? model.name.Substring(5) : model.name;
        string ctrlPath = $"Assets/Animations/ANIMATOR_{charName}.controller";
        ctx.DependsOnSourceAsset(ctrlPath);
        var ctrl = AssetDatabase.LoadAssetAtPath<AnimatorController>(ctrlPath);
        if (ctrl != null) anim.runtimeAnimatorController = ctrl;

        // 4. asset principal = la racine (modèle glissable)
        ctx.AddObjectToAsset("root", root);
        ctx.SetMainObject(root);

        // Le controller ANIMATOR_<Char> est créé EN DIFFÉRÉ (CreateAsset interdit
        // pendant l'import) s'il n'existe pas, puis le modèle est ré-importé pour
        // qu'il s'assigne ci-dessus. Idempotent (rien si déjà présent).
        string capChar = charName, capModel = ctx.assetPath;
        EditorApplication.delayCall += () => EnsureController(capChar, capModel);
    }

    static void EnsureController(string charName, string modelPath)
    {
        string path = $"Assets/Animations/ANIMATOR_{charName}.controller";
        if (AssetDatabase.LoadAssetAtPath<AnimatorController>(path) != null)
            return;   // déjà là → on ne touche pas (pas de boucle de ré-import)

        Directory.CreateDirectory("Assets/Animations");
        var ctrl = AnimatorController.CreateAnimatorControllerAtPath(path);
        var sm = ctrl.layers[0].stateMachine;
        // peuple avec les clips ANIM_<Char>_*.anim trouvés (un état par clip)
        foreach (var f in Directory.GetFiles("Assets/Animations", $"ANIM_{charName}_*.anim").OrderBy(x => x))
        {
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(f.Replace('\\', '/'));
            if (clip == null) continue;
            var st = sm.AddState(clip.name);
            st.motion = clip;
            if (sm.defaultState == null) sm.defaultState = st;
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"[Char] controller créé : {path}");
        // ré-import du modèle → l'importeur l'assignera à l'Animator
        if (File.Exists(modelPath)) AssetDatabase.ImportAsset(modelPath);
    }

    static Material[] ResolveMaterials(AssetImportContext ctx, string[] names, string fallback,
                                       System.Collections.Generic.Dictionary<string, Material> cache,
                                       System.Collections.Generic.Dictionary<string, MatDef> defs)
    {
        var ns = (names != null && names.Length > 0) ? names : new[] { fallback + "_mat" };
        var mats = new Material[ns.Length];
        for (int m = 0; m < ns.Length; m++) mats[m] = ResolveMaterial(ctx, ns[m], cache, defs);
        return mats;
    }

    static Shader DefaultShader()
    {
        var rp = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;
        return (rp != null && rp.defaultShader != null) ? rp.defaultShader
             : (Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard"));
    }

    static Material ResolveMaterial(AssetImportContext ctx, string name,
                                    System.Collections.Generic.Dictionary<string, Material> cache,
                                    System.Collections.Generic.Dictionary<string, MatDef> defs)
    {
        // TOUS embarqués (modèle auto-suffisant), nommés comme dans Blender, un par nom.
        if (cache.TryGetValue(name, out var m)) return m;
        m = new Material(DefaultShader()) { name = name };
        if (defs != null && defs.TryGetValue(name, out var d))
        {
            var c = d.baseColor != null && d.baseColor.Length == 4
                  ? new Color(d.baseColor[0], d.baseColor[1], d.baseColor[2], d.baseColor[3]) : Color.gray;
            m.color = c;
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", d.metallic);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", d.smoothness);
        }
        ctx.AddObjectToAsset("mat_" + name, m);
        cache[name] = m;
        return m;
    }

    static void SetSubmeshes(Mesh mesh, int[] triangles, int[] counts)
    {
        int nsm = (counts != null && counts.Length > 0) ? counts.Length : 1;
        mesh.subMeshCount = nsm;
        if (nsm == 1) { mesh.SetTriangles(triangles, 0); return; }
        int off = 0;
        for (int sm = 0; sm < nsm; sm++)
        {
            int cnt = counts[sm];
            var sub = new int[cnt];
            System.Array.Copy(triangles, off, sub, 0, cnt);
            mesh.SetTriangles(sub, sm);
            off += cnt;
        }
    }

    static Mesh BuildStaticMesh(RigidMeshData rm)
    {
        int vc = rm.vertices.Length / 3;
        var mesh = new Mesh { name = rm.name + "_Mesh" };
        mesh.indexFormat = vc > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        var verts = new Vector3[vc]; var norms = new Vector3[vc]; var uvs = new Vector2[vc];
        for (int i = 0; i < vc; i++)
        {
            verts[i] = new Vector3(rm.vertices[i*3], rm.vertices[i*3+1], rm.vertices[i*3+2]);
            norms[i] = new Vector3(rm.normals[i*3], rm.normals[i*3+1], rm.normals[i*3+2]);
            uvs[i] = new Vector2(rm.uvs[i*2], rm.uvs[i*2+1]);
        }
        mesh.vertices = verts; mesh.normals = norms; mesh.uv = uvs;
        SetSubmeshes(mesh, rm.triangles, rm.submeshIndexCounts);
        mesh.RecalculateBounds();
        return mesh;
    }

    static Mesh BuildMesh(MeshData md, Matrix4x4[] bindposes)
    {
        int vc = md.vertices.Length / 3;
        var mesh = new Mesh { name = md.name + "_Mesh" };
        mesh.indexFormat = vc > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
        var verts = new Vector3[vc]; var norms = new Vector3[vc]; var uvs = new Vector2[vc];
        for (int i = 0; i < vc; i++)
        {
            verts[i] = new Vector3(md.vertices[i*3], md.vertices[i*3+1], md.vertices[i*3+2]);
            norms[i] = new Vector3(md.normals[i*3], md.normals[i*3+1], md.normals[i*3+2]);
            uvs[i] = new Vector2(md.uvs[i*2], md.uvs[i*2+1]);
        }
        mesh.vertices = verts; mesh.normals = norms; mesh.uv = uvs;
        SetSubmeshes(mesh, md.triangles, md.submeshIndexCounts);

        var bpv = new NativeArray<byte>(vc, Allocator.Temp);
        var weights = new NativeArray<BoneWeight1>(md.boneWeights.Length, Allocator.Temp);
        for (int v = 0; v < vc; v++) bpv[v] = (byte)md.bonesPerVertex[v];
        for (int i = 0; i < md.boneWeights.Length; i++)
            weights[i] = new BoneWeight1 { boneIndex = md.boneIndices[i], weight = md.boneWeights[i] };
        mesh.SetBoneWeights(bpv, weights);
        bpv.Dispose(); weights.Dispose();
        mesh.bindposes = bindposes;

        if (md.blendshapes != null)
            foreach (var s in md.blendshapes)
            {
                var dv = new Vector3[vc];
                for (int i = 0; i < vc; i++)
                    dv[i] = new Vector3(s.deltaVertices[i*3], s.deltaVertices[i*3+1], s.deltaVertices[i*3+2]);
                mesh.AddBlendShapeFrame(s.name, 100f, dv, null, null);
            }

        mesh.RecalculateBounds();
        return mesh;
    }
}
