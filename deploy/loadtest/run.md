# Locust Load Test Runbook

Locust creates the pressure needed to show GPU utilization and HPA scale-out. Run it only after NIMs are Ready, Prometheus Adapter exposes `gpu_utilization`, and the HPA resources are applied.

## Chain-Server Mode

```bash
# WHAT: port-forward the public edge locally if ALB DNS is not ready.
kubectl port-forward -n finrag svc/chain-server 8000:8000

# WHAT: run a realistic ramp against /query.
# WHY: 80 users at 5 users/sec gives Prometheus and HPA enough time to react.
FINRAG_TARGET_MODE=chain \
FINRAG_USERNAME=owner@example.com \
FINRAG_PASSWORD='<password>' \
locust -f deploy/loadtest/locustfile.py \
  --host http://localhost:8000 \
  --users 80 \
  --spawn-rate 5 \
  --run-time 20m
```

## Direct NIM Mode

Use this if the goal is to isolate NIM GPU pressure from chain-server auth/Milvus readiness.

```bash
# WHAT: route local traffic to the internal LLM NIM service.
kubectl port-forward -n nim-service svc/llama-3-1-8b-instruct 8001:8000

FINRAG_TARGET_MODE=nim \
FINRAG_NIM_MODEL=meta/llama-3.1-8b-instruct \
locust -f deploy/loadtest/locustfile.py \
  --host http://localhost:8001 \
  --users 60 \
  --spawn-rate 3 \
  --run-time 20m
```

## Watch During The Run

```bash
# WHAT: HPA desired/current replicas should rise under sustained GPU load.
kubectl get hpa -n nim-service -w

# WHAT: confirms NIM replica count and pod placement on GPU nodes.
kubectl get pods -n nim-service -o wide -w

# WHAT: confirms the custom metric exists before blaming HPA.
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/nim-service/pods/*/gpu_utilization" | jq .
```

Capture screenshots when replicas climb, not after the scale-down stabilization window expires.
