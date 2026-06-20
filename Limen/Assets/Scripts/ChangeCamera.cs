using UnityEngine;
using Unity.Cinemachine;

public class ChangeCamera : MonoBehaviour
{
    [SerializeField] private int activePriority = 100;
    [SerializeField] private int inactivePriority = 0;
    [SerializeField] private CinemachineCamera enterCamera;
    [SerializeField] private CinemachineCamera interactCamera;
    [SerializeField] private string playerTag = "Player"; // Pour éviter que n'importe quel objet déclenche la caméra

    // Déclenchement automatique à l'entrée dans le Trigger
    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag(playerTag))
        {
            SwitchOnEnter();
        }
    }

    public void SwitchOnEnter()
    {
        SwitchToCamera(enterCamera);
    }

    // Reste disponible pour être appelé uniquement par tes UnityEvents / Events
    public void SwitchOnInteract()
    {
        SwitchToCamera(interactCamera);
    }

    public void SwitchToCamera(CinemachineCamera targetCamera)
    {
        if (targetCamera == null)
        {
            return;
        }

        CinemachineCamera[] allCameras = FindObjectsByType<CinemachineCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None);

        foreach (CinemachineCamera camera in allCameras)
        {
            if (camera == null)
            {
                continue;
            }

            camera.Priority = camera == targetCamera ? activePriority : inactivePriority;
        }
    }

}