# Grafana Proof Notes

Use Grafana through port-forwarding for screenshots. Do not expose Grafana through public ingress for the burst.

```bash
# WHAT: local-only access for proof capture.
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Login:
# user: admin
# password: finrag-change-me
```

## Capture These Panels

- GPU utilization over time: `DCGM_FI_DEV_GPU_UTIL` grouped by `pod`.
- GPU memory used/free: `DCGM_FI_DEV_FB_USED` and `DCGM_FI_DEV_FB_FREE`.
- GPU temperature: `DCGM_FI_DEV_GPU_TEMP`.
- NIM latency and throughput: NIM service metrics or Triton metrics exposed by each NIM.
- Kubernetes pod count: replicas for `llama-3-1-8b-instruct` and `nv-embedqa-e5-v5`.
- HPA status: desired replicas versus current replicas while Locust load ramps.

## Dashboard Hints

- Start from the NVIDIA DCGM dashboard if imported by the GPU Operator chart.
- Add a FinRAG row with three queries: GPU util, NIM request rate/latency, pod replica count.
- Annotate screenshots with the timestamp and Locust user count so the proof tells a clear story.
