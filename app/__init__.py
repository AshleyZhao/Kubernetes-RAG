# app/__init__.py

# Import tools from kubernetes_tools.py
from .kubernetes_tools import list_kubernetes_pods, restart_all_pods

# Optional: define __all__ for clarity
__all__ = ["list_kubernetes_pods", "restart_all_pods"]