using UnityEngine;

public class BillboardManager : MonoBehaviour
{
    public enum RotationAxis { X, Y, Z, All }

    [Header("Configuration")]
    [Tooltip("Choisissez l'axe sur lequel l'objet a le droit de tourner pour suivre la caméra.")]
    public RotationAxis allowedAxis = RotationAxis.Y;

    private Transform cameraTransform;
    private Transform[] targets;
    private int targetCount;

    void Start()
    {
        cameraTransform = Camera.main.transform;

        int count = transform.childCount;
        targets = new Transform[count];
        for (int i = 0; i < count; i++)
        {
            targets[i] = transform.GetChild(i);
        }

        targetCount = targets.Length;
    }

    void LateUpdate()
    {
        if (cameraTransform == null || targetCount == 0) return;

        Vector3 camPos = cameraTransform.position;

        for (int i = 0; i < targetCount; i++)
        {
            Transform t = targets[i];
            if (t == null) continue;

            Vector3 direction = camPos - t.position;
            if (direction == Vector3.zero) continue;
            
            Quaternion targetRotation = Quaternion.LookRotation(direction);
            Vector3 targetEuler = targetRotation.eulerAngles;
            Vector3 currentEuler = t.eulerAngles;

            switch (allowedAxis)
            {
                case RotationAxis.X:
                    t.eulerAngles = new Vector3(targetEuler.x, currentEuler.y, currentEuler.z);
                    break;

                case RotationAxis.Y:
                    t.eulerAngles = new Vector3(currentEuler.x, targetEuler.y, currentEuler.z);
                    break;

                case RotationAxis.Z:
                    t.eulerAngles = new Vector3(currentEuler.x, currentEuler.y, targetEuler.z);
                    break;

                case RotationAxis.All:
                    t.rotation = targetRotation;
                    break;
            }
        }
    }
}