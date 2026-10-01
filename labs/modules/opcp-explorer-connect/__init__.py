"""opcp-explorer Connectivity lab module.

Teaches the agent's tool interface against the opcp-explorer platform
(AI-Powered-Store): discovering the API/CLI/MCP surface, authenticating with
a scoped token, and performing a basic tool call (list/deploy an application).

All exercises default to a self-contained SIMULATED endpoint so the lab runs
offline inside the isolated exercise container (the LabRunner uses
network_mode="none"). An opt-in `live_mode` flag lets the submission carry
real connection parameters; live calls are validated structurally here and are
intended to be executed through the Flask app / adapter layer outside the
locked-down container. Live mode is strictly opt-in.
"""
