using System.Collections.Generic;
using System.Reflection;
using DG.Tweening;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
#if UNITY_EDITOR
using UnityEditor;
#endif

public class Transition : MonoBehaviour
{
    [Header("Transition")]
    [SerializeField] private List<Material> materials = new List<Material>();
    [SerializeField] private string transitionPropertyName = "_Transition";
    [SerializeField] private float transitionDuration = 0.5f;
    [SerializeField] private Ease transitionEase = Ease.OutSine;
    [SerializeField] private Color transitionFogColor = Color.white;
    [Space(12)]
    [Header("URP Renderer Swap")]
    [SerializeField] private ScriptableRendererData alternateRendererData;

    [Space(12)]
    [Header("Events")]
    public UnityEvent onTransitionTriggered;

    private Tween transitionTween;
    private Tween fogTween;
    private float currentTransitionValue;
    private UniversalRenderPipelineAsset pipelineAsset;
    private ScriptableRendererData originalRendererData;
    private Color originalFogColor;
    private bool isUsingAlternateRenderer;

    private void Start()
    {
        CachePipelineAsset();
        originalFogColor = RenderSettings.fogColor;
        currentTransitionValue = GetCurrentTransitionValue();
    }

#if UNITY_EDITOR
    private void OnEnable()
    {
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
    }

    private void OnDisable()
    {
        EditorApplication.playModeStateChanged -= OnPlayModeStateChanged;
    }

    private void OnPlayModeStateChanged(PlayModeStateChange state)
    {
        if (state != PlayModeStateChange.ExitingPlayMode)
        {
            return;
        }

        ResetTransitionState();
    }
#endif

    public void TriggerTransition()
    {
        TriggerTransition(true);
    }

    public void TriggerTransition(bool goForward)
    {
        onTransitionTriggered?.Invoke();

        float targetValue = goForward ? 1f : 0f;
        StartTransitionTween(targetValue);
        StartFogTween(goForward ? transitionFogColor : originalFogColor);

        if (goForward)
        {
            ApplyRendererSwap(alternateRendererData, true);
        }
        else
        {
            RestoreBaseRendererData();
        }
    }

    public void TriggerTransitionForward()
    {
        TriggerTransition(true);
    }

    public void TriggerTransitionBackward()
    {
        TriggerTransition(false);
    }

    private void StartTransitionTween(float targetValue)
    {
        transitionTween?.Kill();

        if (materials == null || materials.Count == 0)
        {
            return;
        }

        transitionTween = DOTween.To(
                () => currentTransitionValue,
                value =>
                {
                    currentTransitionValue = value;
                    ApplyTransitionValue(currentTransitionValue);
                },
                targetValue,
                transitionDuration)
            .SetEase(transitionEase);
    }

    private void StartFogTween(Color targetColor)
    {
        fogTween?.Kill();

        fogTween = DOTween.To(
                () => RenderSettings.fogColor,
                value => RenderSettings.fogColor = value,
                targetColor,
                transitionDuration)
            .SetEase(transitionEase);
    }

    private void CachePipelineAsset()
    {
        pipelineAsset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;

        if (pipelineAsset == null || pipelineAsset.rendererDataList.Length == 0)
        {
            return;
        }

        originalRendererData = pipelineAsset.rendererDataList[0];
    }

    private void RestoreBaseRendererData()
    {
        ApplyRendererSwap(originalRendererData, false);
    }

    private void ResetTransitionState()
    {
        transitionTween?.Kill();
        fogTween?.Kill();
        currentTransitionValue = 0f;
        ApplyTransitionValue(currentTransitionValue);
        RenderSettings.fogColor = originalFogColor;
        RestoreBaseRendererData();
    }

    private void ApplyRendererSwap(ScriptableRendererData rendererData, bool useAlternateRenderer)
    {
        if (pipelineAsset == null)
        {
            CachePipelineAsset();
        }

        if (pipelineAsset == null || rendererData == null)
        {
            return;
        }

        if (isUsingAlternateRenderer == useAlternateRenderer)
        {
            return;
        }

        if (!TrySetRendererSlotZero(rendererData))
        {
            return;
        }

        isUsingAlternateRenderer = useAlternateRenderer;
    }

    private bool TrySetRendererSlotZero(ScriptableRendererData rendererData)
    {
        FieldInfo rendererDataListField = typeof(UniversalRenderPipelineAsset).GetField("m_RendererDataList", BindingFlags.Instance | BindingFlags.NonPublic);
        FieldInfo renderersField = typeof(UniversalRenderPipelineAsset).GetField("m_Renderers", BindingFlags.Instance | BindingFlags.NonPublic);

        if (rendererDataListField == null || renderersField == null)
        {
            return false;
        }

        ScriptableRendererData[] rendererDataList = rendererDataListField.GetValue(pipelineAsset) as ScriptableRendererData[];
        if (rendererDataList == null || rendererDataList.Length == 0)
        {
            return false;
        }

        rendererDataList[0] = rendererData;
        rendererDataListField.SetValue(pipelineAsset, rendererDataList);

        ScriptableRenderer[] renderers = renderersField.GetValue(pipelineAsset) as ScriptableRenderer[];
        if (renderers != null && renderers.Length > 0)
        {
            renderers[0] = null;
            renderersField.SetValue(pipelineAsset, renderers);
        }

        return true;
    }

    private void ApplyTransitionValue(float value)
    {
        if (materials == null)
        {
            return;
        }

        for (int index = 0; index < materials.Count; index++)
        {
            Material material = materials[index];

            if (material == null)
            {
                continue;
            }

            material.SetFloat(transitionPropertyName, value);
        }
    }

    private float GetCurrentTransitionValue()
    {
        if (materials == null)
        {
            return 0f;
        }

        for (int index = 0; index < materials.Count; index++)
        {
            Material material = materials[index];

            if (material == null)
            {
                continue;
            }

            if (material.HasProperty(transitionPropertyName))
            {
                return material.GetFloat(transitionPropertyName);
            }
        }

        return 0f;
    }
}
