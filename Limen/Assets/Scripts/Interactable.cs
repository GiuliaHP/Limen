using DG.Tweening;
using UnityEngine;
using UnityEngine.Events;

public class Interactable : MonoBehaviour
{
    [Header("Interaction")]
    public bool canInteract = true;
    [Tooltip("Si coché, l'interactable se désactivera après la première utilisation.")]
    public bool isOneTimeUse = false; 
    public UnityEvent onInteract;
    public UnityEvent onEnter;
    public UnityEvent onExit;

    [Space(12)]
    [Header("Visual Feedback")]
    public float emissiveMinIntensity = -10f;
    public float emissiveMaxIntensity = 10f;
    public float emissiveTweenDuration = 0.25f;
    public Color emissiveColor = Color.white;
    public float popScaleDuration = 0.2f;
    public Vector3 popScalePunch = new Vector3(0.08f, 0.08f, 0.08f);
    public float buttonCanvasTweenDuration = 0.2f;
    public float buttonCanvasVisibleScaleMultiplier = 1.05f;
    public float buttonCanvasHiddenScaleMultiplier = 0.9f;

    [Space(12)]
    [Header("References")]
    public Material selectedMaterial;
    public Collider triggerCollider;
    public Canvas buttonCanvas;

    [Space(12)]
    [Header("Runtime State")]
    private Tweener emissiveTween;
    private Tween scaleTween;
    private Tween buttonCanvasTween;
    private float currentEmissiveIntensity;
    private Vector3 initialScale;
    private Vector3 buttonCanvasInitialScale;
    private CanvasGroup buttonCanvasGroup;

    public bool CanInteract => canInteract;

    private void Start()
    {
        initialScale = transform.localScale;
        currentEmissiveIntensity = emissiveMinIntensity;
        ApplyEmissionIntensity(currentEmissiveIntensity);

        if (buttonCanvas != null)
        {
            buttonCanvasInitialScale = buttonCanvas.transform.localScale;
            buttonCanvasGroup = buttonCanvas.GetComponent<CanvasGroup>();

            if (buttonCanvasGroup == null)
            {
                buttonCanvasGroup = buttonCanvas.gameObject.AddComponent<CanvasGroup>();
            }

            buttonCanvasGroup.alpha = 0f;
            buttonCanvas.transform.localScale = buttonCanvasInitialScale * buttonCanvasHiddenScaleMultiplier;
        }
    }

    private void OnTriggerEnter(Collider other)
    {
        if (!canInteract || !IsPlayerCollider(other))
        {
            return;
        }

        onEnter?.Invoke();
        PlayPopScale();
        PlayButtonCanvasEnter();
        StartEmissiveTween(emissiveMaxIntensity);
    }

    private void OnTriggerExit(Collider other)
    {
        if (!canInteract || !IsPlayerCollider(other))
        {
            return;
        }

        onExit?.Invoke();
        PlayButtonCanvasExit();
        StartEmissiveTween(emissiveMinIntensity);
    }

    private void LateUpdate()
    {
        FaceButtonCanvasToCamera();
    }

    public void Interact()
    {
        if (!canInteract)
        {
            return;
        }

        onInteract?.Invoke();

        if (isOneTimeUse)
        {
            canInteract = false;
            PlayButtonCanvasExit(); 
            StartEmissiveTween(emissiveMinIntensity); 

            // Remet l'objet et ses enfants sur le layer "Default" (index 0)
            SetLayerRecursively(gameObject, 0);
        }
    }

    private void SetLayerRecursively(GameObject obj, int newLayer)
    {
        if (obj == null) return;
        
        obj.layer = newLayer;
        
        foreach (Transform child in obj.transform)
        {
            if (child != null)
            {
                SetLayerRecursively(child.gameObject, newLayer);
            }
        }
    }

    private bool IsPlayerCollider(Collider other)
    {
        return other != null && other.GetComponentInParent<PlayerCharacterController>() != null;
    }

    private void StartEmissiveTween(float targetIntensity)
    {
        if (selectedMaterial == null)
        {
            return;
        }

        emissiveTween?.Kill();

        emissiveTween = DOTween.To(
                () => currentEmissiveIntensity,
                intensity =>
                {
                    currentEmissiveIntensity = intensity;
                    ApplyEmissionIntensity(currentEmissiveIntensity);
                },
                targetIntensity,
                emissiveTweenDuration)
            .SetEase(Ease.OutSine);
    }

    private void ApplyEmissionIntensity(float intensity)
    {
        if (selectedMaterial == null)
        {
            return;
        }

        selectedMaterial.EnableKeyword("_EMISSION");
        selectedMaterial.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
        selectedMaterial.SetColor("_EmissionColor", emissiveColor * intensity);
    }

    private void PlayPopScale()
    {
        scaleTween?.Kill();

        transform.localScale = initialScale;
        scaleTween = transform.DOPunchScale(popScalePunch, popScaleDuration, vibrato: 1, elasticity: 0.85f);
    }

    private void PlayButtonCanvasEnter()
    {
        if (buttonCanvas == null || buttonCanvasGroup == null)
        {
            return;
        }

        buttonCanvasTween?.Kill();
        buttonCanvasGroup.alpha = 0f;
        buttonCanvas.transform.localScale = buttonCanvasInitialScale * buttonCanvasHiddenScaleMultiplier;

        buttonCanvasTween = DOTween.Sequence()
            .Join(buttonCanvasGroup.DOFade(1f, buttonCanvasTweenDuration))
            .Join(buttonCanvas.transform.DOScale(buttonCanvasInitialScale * buttonCanvasVisibleScaleMultiplier, buttonCanvasTweenDuration).SetEase(Ease.OutBack));
    }

    private void PlayButtonCanvasExit()
    {
        if (buttonCanvas == null || buttonCanvasGroup == null)
        {
            return;
        }

        buttonCanvasTween?.Kill();

        buttonCanvasTween = DOTween.Sequence()
            .Join(buttonCanvasGroup.DOFade(0f, buttonCanvasTweenDuration))
            .Join(buttonCanvas.transform.DOScale(buttonCanvasInitialScale * buttonCanvasHiddenScaleMultiplier, buttonCanvasTweenDuration).SetEase(Ease.InBack));
    }

    private void FaceButtonCanvasToCamera()
    {
        if (buttonCanvas == null || Camera.main == null)
        {
            return;
        }

        Transform canvasTransform = buttonCanvas.transform;
        Vector3 toCamera = Camera.main.transform.position - canvasTransform.position;

        if (toCamera.sqrMagnitude > 0.0001f)
        {
            canvasTransform.rotation = Quaternion.LookRotation(toCamera, Vector3.up);
        }
    }
}