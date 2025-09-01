import kubernetes
from kubernetes.config import ConfigException
from kubernetes.client.rest import ApiException
from kubernetes.client import V1DeleteOptions
from langchain_core.tools import tool


@tool
def list_kubernetes_pods(namespace: str = "default") -> str:
    """
    A tool to list all pods in a given Kubernetes namespace (default: "default"). ONLY use when the user is clearly requesting an action like 'list pods' or 'please list pods'. DO NOT use when the user is asking for an explanation or instructions


    Args:
        namespace (str): The namespace to list pods from. Defaults to "default".

    Returns:
        str: A formatted list of pod names and statuses, or an error message.
    """
    try:
        kubernetes.config.load_kube_config()
        v1 = kubernetes.client.CoreV1Api()
        
        pod_list = v1.list_namespaced_pod(namespace)
        
        if not pod_list.items:
            return f"No pods found in namespace '{namespace}'."
            
        pods = [f"{pod.metadata.name} (Status: {pod.status.phase})" for pod in pod_list.items]
        return f"Pods in namespace '{namespace}':\n" + "\n".join(pods)

    except ConfigException:
        return "Kubernetes configuration not found. Please ensure your ~/.kube/config file is set up correctly."
    except ApiException as e:
        return f"Kubernetes API Error: {e.reason}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@tool
def restart_all_pods(namespace: str = "default", confirm: bool = False) -> str:
    """
    Restart all pods in a given Kubernetes namespace. ONLY use when the user is clearly requesting an action like 'restart pods'.
    
    Args:
        namespace (str): Namespace in which to restart all pods. Defaults to "default".
        confirm (bool): If True, actually deletes the pods. If False, just previews which pods would be restarted.

    Returns:
        str: Preview of pods to be restarted, or success/error message.
    """
    try:
        kubernetes.config.load_kube_config()
        v1 = kubernetes.client.CoreV1Api()

        pod_list = v1.list_namespaced_pod(namespace)
        if not pod_list.items:
            return f"No pods found in namespace '{namespace}'."

        pods = [pod.metadata.name for pod in pod_list.items]
        preview = f"The following pods would be restarted in namespace '{namespace}':\n" + "\n".join(pods)

        if not confirm:
            return preview + "\n\nPass confirm=True to actually restart these pods."

        # Actual restart
        v1.delete_collection_namespaced_pod(
            namespace=namespace,
            body=V1DeleteOptions()
        )
        return f"Successfully triggered restart of {len(pods)} pods in namespace '{namespace}'."

    except ConfigException:
        return "Kubernetes configuration not found. Please ensure your ~/.kube/config file is set up correctly."
    except ApiException as e:
        return f"Kubernetes API Error: {e.reason}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
