using UnityEngine;
using UnityEngine.InputSystem;

public class Plush : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Transform holdBone;
    [SerializeField] private Transition transition;
    [SerializeField] private Interactable interactable;
    [SerializeField] private Rigidbody plushRigidbody;

    [Space(12)]
    [Header("Runtime")]
    [SerializeField] private Collider[] plushColliders;

    [Space(12)]
    [Header("Events")]
    public UnityEngine.Events.UnityEvent onPickedUp;
    public UnityEngine.Events.UnityEvent onDropped;

    private bool isHeld;
    private bool originalRigidbodyUseGravity;
    private bool originalRigidbodyIsKinematic;
    private bool originalRigidbodyDetectCollisions;

    public bool IsHeld => isHeld;

    private void Awake()
    {
        if (interactable == null)
        {
            interactable = GetComponent<Interactable>();
        }

        if (plushRigidbody == null)
        {
            plushRigidbody = GetComponent<Rigidbody>();
        }

        if (plushColliders == null || plushColliders.Length == 0)
        {
            plushColliders = GetComponentsInChildren<Collider>(true);
        }

        if (plushRigidbody != null)
        {
            originalRigidbodyUseGravity = plushRigidbody.useGravity;
            originalRigidbodyIsKinematic = plushRigidbody.isKinematic;
            originalRigidbodyDetectCollisions = plushRigidbody.detectCollisions;
        }
    }

    private void Update()
    {
        if (!isHeld)
        {
            return;
        }

        if (Keyboard.current != null && Keyboard.current.fKey.wasPressedThisFrame)
        {
            DropPlush();
        }
    }

    public void OnInteract()
    {
        if (isHeld)
        {
            return;
        }

        PickUpPlush();
    }

    private void PickUpPlush()
    {
        if (holdBone == null)
        {
            Debug.LogWarning($"{name} cannot be picked up because no hold bone is assigned.", this);
            return;
        }

        isHeld = true;

        if (interactable != null)
        {
            interactable.UpdatePromptText("F");
        }

        transform.SetParent(holdBone, true);
        transform.localPosition = Vector3.zero;
        transform.localRotation = Quaternion.identity;

        SetCollidersEnabled(false);
        SetRigidbodyHeldState(true);

        transition?.TriggerTransition(true);
        onPickedUp?.Invoke();
    }

    public void DropPlush()
    {
        isHeld = false;

        transform.SetParent(null, true);

        SetRigidbodyHeldState(false);
        SetCollidersEnabled(true);

        if (interactable != null)
        {
            interactable.UpdatePromptText("E");
            interactable.canInteract = true;
        }

        transition?.TriggerTransition(false);
        onDropped?.Invoke();
    }

    private void SetCollidersEnabled(bool enabled)
    {
        if (plushColliders == null)
        {
            return;
        }

        for (int index = 0; index < plushColliders.Length; index++)
        {
            Collider plushCollider = plushColliders[index];

            if (plushCollider == null)
            {
                continue;
            }

            plushCollider.enabled = enabled;
        }
    }

    private void SetRigidbodyHeldState(bool held)
    {
        if (plushRigidbody == null)
        {
            return;
        }

        if (held)
        {
            plushRigidbody.linearVelocity = Vector3.zero;
            plushRigidbody.angularVelocity = Vector3.zero;
            plushRigidbody.useGravity = false;
            plushRigidbody.isKinematic = true;
            plushRigidbody.detectCollisions = false;
            return;
        }

        plushRigidbody.useGravity = originalRigidbodyUseGravity;
        plushRigidbody.isKinematic = originalRigidbodyIsKinematic;
        plushRigidbody.detectCollisions = originalRigidbodyDetectCollisions;
    }
}