"""Solution for Exercise 02: Start Application via REST API.

Reference solution demonstrating how to start an application
by posting to the /api/deployments endpoint.
"""

import sys
import time

import requests


def start_application_api(
    app_name: str,
    api_base_url: str,
    api_token: str = "",
) -> None:
    """Start an application using the platform REST API.

    Args:
        app_name: Name of the registered application to start.
        api_base_url: Base URL of the platform API (e.g., https://store.example.com).
        api_token: Optional bearer token for authentication.
    """
    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    # POST to /api/deployments with action "start"
    deploy_url = f"{api_base_url.rstrip('/')}/api/deployments"
    payload = {
        "app_name": app_name,
        "action": "start",
    }

    print(f"Starting application '{app_name}' via REST API...")
    print(f"POST {deploy_url}")

    response = requests.post(deploy_url, json=payload, headers=headers, timeout=30)
    print(f"Response: {response.status_code} - {response.json()}")

    if response.status_code not in (200, 201, 202):
        print(f"API returned error: {response.text}")
        sys.exit(1)

    # Poll for running status
    status_url = f"{api_base_url.rstrip('/')}/api/deployments/{app_name}/status"
    print(f"Polling status at: {status_url}")

    deadline = time.time() + 120
    while time.time() < deadline:
        status_resp = requests.get(status_url, headers=headers, timeout=10)
        if status_resp.status_code == 200:
            data = status_resp.json()
            status = data.get("status", "unknown")
            print(f"  Status: {status}")
            if status == "running":
                print("Application is running!")
                return
            if status in ("error", "failed"):
                print(f"Application failed: {data.get('reason', 'unknown')}")
                sys.exit(1)
        time.sleep(5)

    print("Timeout: application did not reach running state within 120 seconds.")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 02_solution.py <app_name> <api_base_url> [api_token]")
        sys.exit(1)

    token = sys.argv[3] if len(sys.argv) > 3 else ""
    start_application_api(sys.argv[1], sys.argv[2], token)
