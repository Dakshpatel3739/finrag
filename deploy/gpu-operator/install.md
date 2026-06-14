# NVIDIA GPU Operator Install

This is a runbook fragment, not an automated script. It installs the operator that manages NVIDIA drivers, container runtime integration, device plugin, MIG manager, and DCGM exporter on the GPU node group.

## Commands

```bash
# WHAT: NVIDIA publishes the GPU Operator chart from the NGC Helm repo.
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# WHY: privileged namespace is required because the operator manages host drivers
# and device plugins on GPU worker nodes.
kubectl create namespace gpu-operator --dry-run=client -o yaml | kubectl apply -f -
kubectl label --overwrite namespace gpu-operator pod-security.kubernetes.io/enforce=privileged

# WHAT: installs GPU Operator with DCGM exporter enabled so Prometheus can scrape
# GPU utilization, memory, temperature, and pod attribution metrics.
# WHY enablePodLabels/enablePodUID: the HPA adapter needs namespace/pod labels on
# DCGM metrics to expose a per-pod custom metric.
helm upgrade --install gpu-operator nvidia/gpu-operator \
  --namespace gpu-operator \
  --version v26.3.2 \
  --wait \
  --set dcgmExporter.enabled=true \
  --set dcgmExporter.enablePodLabels=true \
  --set dcgmExporter.enablePodUID=true
```

## Verification

```bash
# WHAT: confirms the device plugin advertises GPUs to Kubernetes.
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu

# WHAT: proves the host driver is working from inside Kubernetes.
kubectl run nvidia-smi \
  --rm -it \
  --restart=Never \
  --image=nvidia/cuda:12.4.1-base-ubuntu22.04 \
  --overrides='{"spec":{"tolerations":[{"key":"nvidia.com/gpu","operator":"Equal","value":"true","effect":"NoSchedule"}],"containers":[{"name":"nvidia-smi","image":"nvidia/cuda:12.4.1-base-ubuntu22.04","command":["nvidia-smi"],"resources":{"limits":{"nvidia.com/gpu":"1"}}}]}}'

# WHAT: checks operator-managed pods.
kubectl get pods -n gpu-operator
```

## Notes

- A NIM pod showing `0/1 Running`, `ContainerCreating`, or `NotReady` during first boot is often downloading models or building/loading the selected profile. Do not treat it as failure until logs and events show a hard error.
- Keep GPU nodes tainted. The NIM manifests include tolerations; regular app pods should remain on the CPU node group.
- If EKS uses a GPU AMI with pre-installed drivers, install with `--set driver.enabled=false` only after verifying the driver version is compatible with the selected NIMs.
