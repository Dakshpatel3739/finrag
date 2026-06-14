# DCGM Exporter Notes

DCGM exporter emits NVIDIA GPU metrics such as utilization, memory usage, temperature, power, and per-pod attribution labels. The preferred path for this repo is to let the NVIDIA GPU Operator install DCGM exporter.

## Preferred: GPU Operator Managed

```bash
# WHAT: check that GPU Operator installed DCGM exporter.
kubectl get pods,svc -n gpu-operator | grep -i dcgm

# WHAT: confirm Prometheus can see GPU utilization samples.
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
# Open http://localhost:9090 and query:
# DCGM_FI_DEV_GPU_UTIL
```

The GPU Operator install notes enable:

```text
dcgmExporter.enabled=true
dcgmExporter.enablePodLabels=true
dcgmExporter.enablePodUID=true
```

Those labels matter because the Prometheus Adapter needs `namespace` and `pod` dimensions to register a per-pod custom metric for HPA.

## Fallback: Standalone Chart

Use this only if the GPU Operator DCGM component is disabled or not scraped.

```bash
# WHAT: standalone NVIDIA DCGM exporter chart.
helm repo add dcgm-exporter https://nvidia.github.io/dcgm-exporter/helm-charts
helm repo update

# WHY ServiceMonitor labels match kube-prometheus-stack discovery.
helm upgrade --install dcgm-exporter dcgm-exporter/dcgm-exporter \
  --namespace gpu-operator \
  --set serviceMonitor.enabled=true \
  --set serviceMonitor.additionalLabels.release=kube-prometheus-stack
```

## Proof Panels

- `DCGM_FI_DEV_GPU_UTIL` for GPU utilization under Locust load.
- `DCGM_FI_DEV_FB_USED` and `DCGM_FI_DEV_FB_FREE` for GPU memory pressure.
- `DCGM_FI_DEV_GPU_TEMP` for thermal proof.
- Per-pod GPU labels to show which NIM replica consumed the GPU.
