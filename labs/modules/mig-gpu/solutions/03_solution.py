"""Reference solution for Exercise 3: Monitor GPU Utilization.

Demonstrates the correct approach to monitoring GPU compute utilization
from within a MIG-enabled container and verifying GPU compute accessibility.
"""


def get_solution() -> dict:
    """Return the reference solution submission for GPU monitoring.

    Returns:
        A dict representing a valid submission that passes all checks.
    """
    return {
        "app_name": "mig-training-app",
        "compute_command": (
            "python3 -c \"import torch; t = torch.cuda.FloatTensor(256); "
            "print('GPU compute OK')\""
        ),
        "api_endpoint": "http://localhost:5000/api",
    }


def get_expected_result() -> dict:
    """Return the expected result from a successful GPU monitoring check.

    Returns:
        Expected output when GPU compute is accessible and metrics available.
    """
    return {
        "app_name": "mig-training-app",
        "compute_accessible": True,
        "compute_output": "GPU compute OK",
        "compute_duration_seconds": 3.7,
        "gpu_utilization": 15,
        "memory_usage_mb": 512,
        "error": None,
    }


def get_gpu_utilization_command() -> str:
    """Return the API request to query GPU utilization metrics.

    Returns:
        The API endpoint to query.
    """
    return "GET /api/gpu/utilization?app=mig-training-app"


def get_compute_verification_command() -> str:
    """Return the command to verify GPU compute accessibility.

    Returns:
        The compute verification command string.
    """
    return (
        "python3 -c \"import torch; t = torch.cuda.FloatTensor(256); "
        "print('GPU compute OK')\""
    )


def get_nvidia_smi_command() -> str:
    """Return the nvidia-smi command for checking GPU visibility.

    Returns:
        The nvidia-smi command string.
    """
    return "nvidia-smi"
