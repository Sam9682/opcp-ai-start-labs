# Docker Applications with MIG GPU Lab Module

## Objective

Learn how to launch Docker applications with shared GPU resources using Multi-Instance
GPU (MIG) profiles on the AI-Powered-Store platform. Understand MIG profile configurations,
GPU resource allocation, utilization monitoring, and proper resource release.

## Prerequisites

- Install Bare-Metal (install-bare-metal)
- Adding Applications (adding-applications)
- Starting Applications (starting-applications)

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | List MIG Profiles | List available MIG profile configurations on the platform |
| 2 | Deploy with MIG Profile | Deploy a Docker application requesting a specific MIG profile |
| 3 | Monitor GPU Utilization | Monitor GPU compute utilization from within a MIG-enabled container |
| 4 | Release GPU Resources | Release allocated MIG GPU resources and verify deallocation |

## Key Concepts

- **MIG Profile**: A Multi-Instance GPU configuration that partitions a physical GPU into
  isolated instances for shared workloads. Each profile specifies compute and memory
  resources allocated to the instance.
- **GPU Allocation**: The process of assigning a MIG profile to a container, confirmed by
  the platform within 30 seconds of deployment.
- **Compute Accessibility**: Verification that GPU compute is accessible from within the
  container by executing a sample compute operation (must complete within 60 seconds).
- **Profile Release**: Deallocation of MIG resources when an application is stopped,
  confirmed by the profile no longer appearing in active GPU allocation status within
  30 seconds.
- **Alternative Profile Suggestion**: When a requested profile is at capacity, the platform
  suggests the closest available alternative in compute capability.
