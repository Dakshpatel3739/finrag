# Phase 5 GPU Burst Runbook

**TEARDOWN FIRST: `eksctl delete cluster -f deploy/eks/cluster.yaml --wait`**

This runbook is ordered for a one-day GPU proof: apply infrastructure, capture evidence, then tear down. All prices are rough planning estimates. Verify current regional prices in AWS Pricing Calculator before running.

## 0. Cost Guardrails

| Guardrail | Time | Rough cost |
|---|---:|---:|
| Set a calendar alarm for teardown before creating the cluster. | 1 min | $0 |
| Keep GPU node group at `maxSize: 3`. | 1 min | Avoids runaway GPU spend |
| Confirm the final command is ready: `eksctl delete cluster -f deploy/eks/cluster.yaml --wait`. | 1 min | $0 |

## 1. Prerequisites And NGC Key

| Action | Time | Rough cost |
|---|---:|---:|
| Confirm AWS CLI, `eksctl`, `kubectl`, `helm`, `jq`, Docker, and Locust. | 10 min | $0 |
| Confirm EC2 quota for `g5.xlarge` in the selected region. | 5 min | $0 |
| Export NGC key: `export NGC_API_KEY='<key>'`. | 1 min | $0 |
| Confirm EFS CSI StorageClass plan named `efs-sc`. | 5-20 min | EFS storage only for used cache data |

Why: NIM containers and model profiles are gated by NGC access, and the shared NIM cache needs RWX storage before model pods start.

## 2. Create EKS

```bash
eksctl create cluster -f deploy/eks/cluster.yaml
aws eks update-kubeconfig --region us-east-1 --name finrag-phase5-gpu
kubectl get nodes -L finrag.io/node-pool,nvidia.com/gpu.product
```

| Action | Time | Rough cost |
|---|---:|---:|
| EKS control plane and node groups come up. | 15-25 min | EKS standard support is about $0.10/hr plus EC2 |
| One `m6i.large` CPU node runs system pods. | same | About cents per hour |
| One to three `g5.xlarge` nodes run NIMs. | same | Usually the dominant cost, roughly dollars per GPU-node hour |

Why: the CPU node group carries system and app pods; the GPU group is tainted and capped for inference only.

## 3. NVIDIA GPU Operator

```bash
# Follow the commented install notes.
less deploy/gpu-operator/install.md
```

Proof commands:

```bash
kubectl get pods -n gpu-operator
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu
```

| Action | Time | Rough cost |
|---|---:|---:|
| Install driver/runtime/device-plugin/DCGM stack. | 10-20 min | GPU nodes continue billing while drivers settle |
| Capture `nvidia-smi` proof. | 2 min | Included in node runtime |

Why: Kubernetes must advertise `nvidia.com/gpu` before NIM pods can schedule.

## 4. Storage And PVC

```bash
# Ensure efs-sc exists before this.
kubectl apply -f deploy/storage/pvc.yaml
kubectl get pvc -n nim-service
```

| Action | Time | Rough cost |
|---|---:|---:|
| Bind RWX model-cache PVC. | 2-10 min | EFS storage and request activity; delete after teardown |

Why: hostPath fails multi-node scheduling. EFS/RWX lets all NIM replicas share downloaded model profiles.

## 5. NIM Operator And Three NIMs

```bash
less deploy/nim-operator/install.md

kubectl apply -f deploy/nim-operator/nimcache.yaml
kubectl get nimcaches.apps.nvidia.com -n nim-service -w

kubectl apply -f deploy/nim-operator/nimservice-llm.yaml
kubectl apply -f deploy/nim-operator/nimservice-embed.yaml
kubectl apply -f deploy/nim-operator/nimservice-rerank.yaml
kubectl get pods -n nim-service -w
```

| Action | Time | Rough cost |
|---|---:|---:|
| Install NIM Operator CRDs/controller. | 5-10 min | CPU node runtime |
| Download/cache model profiles. | 20-60 min | GPU node runtime, EFS storage, NGC egress if applicable |
| Start LLM, embedding, reranking NIMs. | 10-30 min | GPU node runtime |

Notes:

- `0/1 Running`, `ContainerCreating`, or `NotReady` can mean model/profile loading, not immediate failure.
- First boot inspects the GPU and chooses a profile, normally TensorRT-LLM for supported LLM profiles or a fallback such as vLLM.
- Verify `NIMCache.status.profiles[].name`; pin the matching hash in `NIMService.spec.storage.nimCache.profile` if preserving final manifests.
- NIMs stay `ClusterIP`. Do not expose them through ALB, NodePort, or LoadBalancer.

## 6. Milvus And Chain-Server

```bash
helm repo add milvus https://zilliztech.github.io/milvus-helm
helm repo update
helm upgrade --install finrag-milvus milvus/milvus \
  --namespace milvus \
  --create-namespace \
  -f deploy/app/milvus-values.yaml

# WHAT: create namespace before the secret so pods do not start with a missing
# Secret reference. The deployment file also declares the namespace for review.
kubectl create namespace finrag --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic finrag-api-secret \
  --namespace finrag \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)" \
  --from-literal=NIM_API_KEY="${NGC_API_KEY}"

# Build and push the image named in chain-server-deployment.yaml before apply.
kubectl apply -f deploy/app/chain-server-deployment.yaml
kubectl apply -f deploy/app/service.yaml

# WHAT: expose only the chain-server/frontend edge through ALB.
# WHY: NIMs and Milvus stay ClusterIP/internal.
kubectl apply -f deploy/app/ingress.yaml
```

| Action | Time | Rough cost |
|---|---:|---:|
| Install standalone Milvus. | 10-20 min | CPU node plus gp3 EBS volumes |
| Build/push chain-server image. | 5-15 min | ECR storage is negligible for burst |
| Start chain-server replicas. | 2-5 min | CPU node runtime |

Why: the chain-server is the public API edge and talks to internal Milvus/NIM services by ClusterIP DNS.

## 7. Observability

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f deploy/observability/prometheus-values.yaml

kubectl apply -f deploy/observability/servicemonitor-nim.yaml
less deploy/observability/dcgm-exporter.md
less deploy/observability/grafana-notes.md
```

| Action | Time | Rough cost |
|---|---:|---:|
| Install Prometheus/Grafana stack. | 10-15 min | CPU node runtime, short retention |
| Confirm DCGM metrics. | 5 min | Included in GPU Operator runtime |

Why: proof requires Grafana screenshots and Prometheus time series before HPA can work.

## 8. Prometheus Adapter And HPA

```bash
helm upgrade --install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  --create-namespace \
  -f deploy/observability/prometheus-adapter-values.yaml

kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/nim-service/pods/*/gpu_utilization" | jq .

kubectl apply -f deploy/autoscaling/hpa-llm.yaml
kubectl apply -f deploy/autoscaling/hpa-embed.yaml
kubectl get hpa -n nim-service
```

| Action | Time | Rough cost |
|---|---:|---:|
| Register custom GPU metric. | 5-10 min | CPU node runtime |
| Apply HPA resources. | 1 min | Cost only when replicas scale |

Why: the required chain is Prometheus scrape -> Adapter query -> custom-metrics API -> HPA read -> NIM replica scale.

## 9. Locust Load Test

```bash
less deploy/loadtest/run.md
kubectl get hpa -n nim-service -w
kubectl get pods -n nim-service -o wide -w
```

| Action | Time | Rough cost |
|---|---:|---:|
| Ramp 60-80 users for 20 minutes. | 20-30 min | May scale GPU nodes/pods up to configured max |
| Capture HPA and Grafana proof while load is active. | 10 min | Same as active runtime |

Why: HPA needs sustained load and at least a few Prometheus samples before desired replicas change.

## 10. Proof Checklist

Capture these before teardown:

- `nvidia-smi` from a Kubernetes GPU pod.
- `kubectl get nodes` showing `nvidia.com/gpu` allocatable.
- `kubectl get nimcaches.apps.nvidia.com -n nim-service` showing caches Ready.
- `kubectl get nimservices.apps.nvidia.com -n nim-service` showing services Ready.
- NIM logs showing selected model/profile and successful startup.
- Grafana panels for GPU utilization, GPU memory, NIM latency/throughput, and pod count.
- `kubectl get hpa -n nim-service` showing desired replicas above 1 under load.
- Locust screenshot or terminal output showing active users and request rate.
- ALB or port-forward request proof for `POST /query`.

## 11. Tear Down

```bash
# Delete app-level Helm releases first if you want cleaner logs, then delete EKS.
helm uninstall prometheus-adapter -n monitoring || true
helm uninstall kube-prometheus-stack -n monitoring || true
helm uninstall finrag-milvus -n milvus || true
helm uninstall nim-operator -n nim-operator || true
helm uninstall gpu-operator -n gpu-operator || true

# Final cost stop.
eksctl delete cluster -f deploy/eks/cluster.yaml --wait
```

| Action | Time | Rough cost |
|---|---:|---:|
| Delete Helm releases and cluster. | 20-40 min | Billing stops as EC2/EBS/EFS/ALB resources delete |

**TEARDOWN AGAIN: `eksctl delete cluster -f deploy/eks/cluster.yaml --wait`**
