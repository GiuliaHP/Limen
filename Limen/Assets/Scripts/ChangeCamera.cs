using UnityEngine;
using Unity.Cinemachine;

public class ChangeCamera : MonoBehaviour
{
    [SerializeField] private int activePriority = 100;
    [SerializeField] private int inactivePriority = 0;
    [SerializeField] private CinemachineCamera enterCamera;
    [SerializeField] private CinemachineCamera interactCamera;

    private CinemachineCamera baseCamera;

    public void SwitchToBaseCamera()
    {
        SwitchToCamera(baseCamera);
        baseCamera = null;
    }

    public void SwitchOnEnter()
    {
        CacheBaseCamera();
        SwitchToCamera(enterCamera);
    }

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

    private void CacheBaseCamera()
    {
        if (baseCamera != null)
        {
            return;
        }

        CinemachineCamera[] allCameras = FindObjectsByType<CinemachineCamera>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
        CinemachineCamera activeCamera = null;
        int highestPriority = int.MinValue;

        foreach (CinemachineCamera camera in allCameras)
        {
            if (camera == null)
            {
                continue;
            }

            if (camera.Priority > highestPriority)
            {
                highestPriority = camera.Priority;
                activeCamera = camera;
            }
        }

        baseCamera = activeCamera;
    }
}
