"""Solution for Exercise 03: Verify Running Status and Health Check.

Reference solution demonstrating how to verify an application is
running and its ports accept connections.
"""

import socket
import sys
import time

import requests


def verify_running_status(
    app_name: str,
    api_base_url: str,
    api_token: str = "",
    ports: list[dict] = None,
) -> None:
    """Verify application running status and port connectivity.

    Args:
        app_name: Name of the application to verify.
        api_base_url: Base URL of the platform API.
        api_token: Optional bearer token for authentication.
        ports: List of {"host": "...", "port": int} to check.
    """
    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    # Step 1: Check running status
    status_url = f"{api_base_url.rstrip('/')}/api/deployments/{app_name}/status"
    print(f"Checking status at: {status_url}")

    deadline = time.time() + 120
    is_running = False

    while time.time() < deadline:
        try:
            resp = requests.get(status_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                print(f"  Status: {status}")
                if status == "running":
                    is_running = True
                    break
                if status in ("error", "failed"):
                    print(f"  Application failed: {data.get('reason', '')}")
                    sys.exit(1)
        except requests.RequestException as e:
            print(f"  Request error: {e}")

        time.sleep(5)

    if not is_running:
        print("FAIL: Application did not reach running state within 120 seconds.")
        sys.exit(1)

    print("PASS: Application is running.")

    # Step 2: Check port connectivity
    if not ports:
        # Try to retrieve ports from the platform
        ports_url = f"{api_base_url.rstrip('/')}/api/deployments/{app_name}/ports"
        try:
            resp = requests.get(ports_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                ports = resp.json().get("ports", [])
        except requests.RequestException:
            ports = []

    if not ports:
        print("No exposed ports to check.")
        return

    print(f"\nChecking {len(ports)} exposed port(s)...")
    all_connected = True

    for port_info in ports:
        host = port_info.get("host", "localhost")
        port = port_info.get("port", 0)
        connected = _try_connect(host, port, timeout=30)

        if connected:
            print(f"  PASS: {host}:{port} - connected")
        else:
            print(f"  FAIL: {host}:{port} - connection refused")
            all_connected = False

    if all_connected:
        print("\nAll port checks passed.")
    else:
        print("\nSome port checks failed.")
        sys.exit(1)


def _try_connect(host: str, port: int, timeout: int = 30) -> bool:
    """Attempt TCP connection within timeout."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except (socket.error, OSError):
            pass
        time.sleep(2)

    return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 03_solution.py <app_name> <api_base_url> [api_token]")
        sys.exit(1)

    token = sys.argv[3] if len(sys.argv) > 3 else ""
    verify_running_status(sys.argv[1], sys.argv[2], token)
