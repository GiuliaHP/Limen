using UnityEngine;
using UnityEngine.Events;

public class SimpleInteractable : MonoBehaviour
{
    [SerializeField] private bool canInteract = true;
    [SerializeField] private UnityEvent onInteract;

    public bool CanInteract => canInteract;

    public void Interact()
    {
        if (!canInteract)
        {
            return;
        }

        onInteract?.Invoke();
    }
}