using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(CharacterController))]
public class PlayerCharacterController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float gravity = -9.81f;
    [SerializeField] private float rotationSmoothTime = 0.08f;
    [SerializeField] private Transform cameraTransform;
    [SerializeField] private float interactionRadius = 2f;
    [SerializeField] private LayerMask interactableLayers = ~0;

    private CharacterController characterController;
    private Vector3 verticalVelocity;
    private float playerRotationVelocity;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();

        RefreshCameraTransform();
    }

    private void Update()
    {
        HandleMovement();
        HandleGravity();
        HandleInteraction();
    }


    private void HandleMovement()
    {
        // Movement is relative to the fixed camera/screen view.
        RefreshCameraTransform();

        if (Keyboard.current == null)
        {
            return;
        }

        Vector2 moveInput = Vector2.zero;

        if (Keyboard.current.wKey.isPressed || Keyboard.current.zKey.isPressed)
        {
            moveInput.y += 1f;
        }

        if (Keyboard.current.sKey.isPressed)
        {
            moveInput.y -= 1f;
        }

        if (Keyboard.current.dKey.isPressed)
        {
            moveInput.x += 1f;
        }

        if (Keyboard.current.aKey.isPressed || Keyboard.current.qKey.isPressed)
        {
            moveInput.x -= 1f;
        }

        if (moveInput.sqrMagnitude > 1f)
        {
            moveInput.Normalize();
        }

        Vector3 referenceForward = cameraTransform != null ? cameraTransform.forward : transform.forward;
        Vector3 referenceRight = cameraTransform != null ? cameraTransform.right : transform.right;

        referenceForward.y = 0f;
        referenceRight.y = 0f;
        referenceForward.Normalize();
        referenceRight.Normalize();

        Vector3 movement = (referenceRight * moveInput.x) + (referenceForward * moveInput.y);
        characterController.Move(movement * (moveSpeed * Time.deltaTime));

        if (movement.sqrMagnitude > 0.0001f)
        {
            float targetYaw = Mathf.Atan2(movement.x, movement.z) * Mathf.Rad2Deg;
            float smoothedYaw = Mathf.SmoothDampAngle(
                transform.eulerAngles.y,
                targetYaw,
                ref playerRotationVelocity,
                rotationSmoothTime);

            transform.rotation = Quaternion.Euler(0f, smoothedYaw, 0f);
        }
    }

    private void RefreshCameraTransform()
    {
        if (Camera.main != null)
        {
            cameraTransform = Camera.main.transform;
        }
    }

    private void HandleGravity()
    {
        if (characterController.isGrounded && verticalVelocity.y < 0f)
        {
            verticalVelocity.y = -2f;
        }

        verticalVelocity.y += gravity * Time.deltaTime;
        characterController.Move(verticalVelocity * Time.deltaTime);
    }

    private void HandleInteraction()
    {
        if (Keyboard.current == null || !Keyboard.current.eKey.wasPressedThisFrame)
        {
            return;
        }

        Collider[] hits = Physics.OverlapSphere(
            transform.position,
            interactionRadius,
            interactableLayers,
            QueryTriggerInteraction.Collide);

        Interactable closestInteractable = null;
        float closestDistance = float.MaxValue;

        foreach (Collider hit in hits)
        {
            Interactable interactable = hit.GetComponentInParent<Interactable>();
            if (interactable == null || !interactable.CanInteract)
            {
                continue;
            }

            float distance = Vector3.Distance(transform.position, interactable.transform.position);
            if (distance < closestDistance)
            {
                closestDistance = distance;
                closestInteractable = interactable;
            }
        }

        if (closestInteractable != null)
        {
            closestInteractable.Interact();
        }
    }

    
}