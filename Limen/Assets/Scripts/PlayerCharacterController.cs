using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(CharacterController))]
public class PlayerCharacterController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float gravity = -9.81f;
    [SerializeField] private Transform cameraTransform;
    [SerializeField] private Transform cameraTarget;
    [SerializeField] private float rotationSmoothTime = 0.08f;
    [SerializeField] private float mouseLookSensitivity = 0.12f;
    [SerializeField] private float arrowLookSpeed = 120f;
    [SerializeField] private float minPitch = -35f;
    [SerializeField] private float maxPitch = 70f;
    [SerializeField] private float interactionRadius = 2f;
    [SerializeField] private LayerMask interactableLayers = ~0;

    private CharacterController characterController;
    private Vector3 verticalVelocity;
    private float playerRotationVelocity;
    private float cameraYaw;
    private float cameraPitch;

    private void Awake()
    {
        characterController = GetComponent<CharacterController>();

        if (cameraTransform == null && Camera.main != null)
        {
            cameraTransform = Camera.main.transform;
        }

        if (cameraTarget != null)
        {
            Vector3 angles = cameraTarget.eulerAngles;
            cameraYaw = angles.y;
            cameraPitch = NormalizeAngle(angles.x);
        }
        else
        {
            cameraYaw = transform.eulerAngles.y;
        }
    }

    private void Update()
    {
        HandleLook();
        HandleMovement();
        HandleGravity();
        HandleInteraction();
    }

    private void HandleLook()
    {
        if (cameraTarget == null)
        {
            return;
        }

        float yawDelta = 0f;
        float pitchDelta = 0f;

        if (Mouse.current != null)
        {
            Vector2 mouseDelta = Mouse.current.delta.ReadValue();
            yawDelta += mouseDelta.x * mouseLookSensitivity;
            pitchDelta -= mouseDelta.y * mouseLookSensitivity;
        }

        if (Keyboard.current != null)
        {
            float keyYaw = 0f;
            float keyPitch = 0f;

            if (Keyboard.current.leftArrowKey.isPressed)
            {
                keyYaw -= 1f;
            }

            if (Keyboard.current.rightArrowKey.isPressed)
            {
                keyYaw += 1f;
            }

            if (Keyboard.current.upArrowKey.isPressed)
            {
                keyPitch += 1f;
            }

            if (Keyboard.current.downArrowKey.isPressed)
            {
                keyPitch -= 1f;
            }

            yawDelta += keyYaw * arrowLookSpeed * Time.deltaTime;
            pitchDelta += keyPitch * arrowLookSpeed * Time.deltaTime;
        }

        cameraYaw += yawDelta;
        cameraPitch = Mathf.Clamp(cameraPitch + pitchDelta, minPitch, maxPitch);
        cameraTarget.rotation = Quaternion.Euler(cameraPitch, cameraYaw, 0f);
    }

    private void HandleMovement()
    {
        if (cameraTransform == null && Camera.main != null)
        {
            cameraTransform = Camera.main.transform;
        }

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

        SimpleInteractable closestInteractable = null;
        float closestDistance = float.MaxValue;

        foreach (Collider hit in hits)
        {
            SimpleInteractable interactable = hit.GetComponentInParent<SimpleInteractable>();
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

    private static float NormalizeAngle(float angle)
    {
        angle %= 360f;
        if (angle > 180f)
        {
            angle -= 360f;
        }

        return angle;
    }
}