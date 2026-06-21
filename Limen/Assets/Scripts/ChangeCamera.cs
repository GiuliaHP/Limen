using UnityEngine;
using Unity.Cinemachine;

public class ChangeCamera : MonoBehaviour
{
    [SerializeField] private int activePriority = 100;
    [SerializeField] private int inactivePriority = 0;
    [SerializeField] private CinemachineCamera cameraToActivate;
    [SerializeField] private string playerTag = "Player";

    private void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag(playerTag))
        {
            SwitchCamera();
        }
    }

    public void SwitchCamera()
    {
        SwitchToCamera(cameraToActivate);
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