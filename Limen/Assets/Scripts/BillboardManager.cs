using UnityEngine;
using System.Collections.Generic;

public class BillboardManager : MonoBehaviour
{
    public enum RotationAxis { X, Y, Z, All }

    [Header("Configuration")]
    public RotationAxis allowedAxis = RotationAxis.Y; // Y est généralement le meilleur pour des arbres !

    private Transform mainCameraTransform;
    private List<Transform> children = new List<Transform>();

    void Start()
    {
        // 1. Mise en cache de la caméra
        if (Camera.main != null)
        {
            mainCameraTransform = Camera.main.transform;
        }
        else
        {
            Debug.LogWarning("Aucune caméra principale trouvée dans la scène !");
            return;
        }

        // 2. Récupération de tous les enfants directs et application immédiate
        foreach (Transform child in transform)
        {
            children.Add(child);
            
            // Applique la rotation selon l'axe choisi dès le Start
            ApplyBillboard(child);
        }
    }

    void LateUpdate()
    {
        if (mainCameraTransform == null || children.Count == 0) return;

        // 3. Mise à jour de l'orientation à chaque frame
        foreach (Transform child in children)
        {
            ApplyBillboard(child);
        }
    }

    // Fonction centralisée pour appliquer la rotation sur l'axe choisi
    private void ApplyBillboard(Transform child)
    {
        Vector3 targetDirection = mainCameraTransform.position - child.position;
        Quaternion targetRotation = Quaternion.LookRotation(-targetDirection);
        Vector3 eulerRotation = targetRotation.eulerAngles;

        Vector3 currentEuler = child.eulerAngles;

        switch (allowedAxis)
        {
            case RotationAxis.X:
                child.eulerAngles = new Vector3(eulerRotation.x, currentEuler.y, currentEuler.z);
                break;
            case RotationAxis.Y:
                child.eulerAngles = new Vector3(currentEuler.x, eulerRotation.y, currentEuler.z);
                break;
            case RotationAxis.Z:
                child.eulerAngles = new Vector3(currentEuler.x, currentEuler.y, eulerRotation.z);
                break;
            case RotationAxis.All:
                child.rotation = targetRotation;
                break;
        }
    }
}