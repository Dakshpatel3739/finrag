# NVIDIA NIM Operator Install

This runbook fragment installs the NIM Operator and creates the NGC secrets used by `NIMCache` and `NIMService` resources.

## Commands

```bash
# WHAT: NIM services live in their own namespace so GPU inference, cache PVCs,
# and secrets can be inspected and deleted as a unit.
kubectl create namespace nim-service --dry-run=client -o yaml | kubectl apply -f -

# WHAT: the operator controller lives separately from model-serving workloads.
kubectl create namespace nim-operator --dry-run=client -o yaml | kubectl apply -f -

# WHAT: NIM containers and model artifacts are pulled from nvcr.io using an NGC
# API key. The docker-registry secret is used for image pulls.
kubectl create secret docker-registry ngc-secret \
  --namespace nim-service \
  --docker-server=nvcr.io \
  --docker-username='$oauthtoken' \
  --docker-password="${NGC_API_KEY}"

# WHAT: generic secret read by NIM/NIMCache as NGC_API_KEY.
# WHY: model profile downloads require authenticated NGC access.
kubectl create secret generic ngc-api-secret \
  --namespace nim-service \
  --from-literal=NGC_API_KEY="${NGC_API_KEY}"

helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# WHAT: installs the CRDs and controller for NIMCache, NIMService, and NIMPipeline.
helm upgrade --install nim-operator nvidia/k8s-nim-operator \
  --namespace nim-operator \
  --version 3.1.1 \
  --wait
```

## Apply FinRAG NIM Resources

```bash
# WHAT: creates three cache jobs backed by the shared RWX model-cache PVC.
kubectl apply -f deploy/nim-operator/nimcache.yaml

# WHY: wait for cache status before starting services so first request latency
# does not include model downloads.
kubectl get nimcaches.apps.nvidia.com -n nim-service -w

# WHAT: inspect the profile hash selected for the actual GPU shape.
kubectl get nimcache -n nim-service llama-3-1-8b-instruct \
  -o=jsonpath='{.status.profiles}' | jq .

# WHAT: starts the internal-only NIM services.
kubectl apply -f deploy/nim-operator/nimservice-llm.yaml
kubectl apply -f deploy/nim-operator/nimservice-embed.yaml
kubectl apply -f deploy/nim-operator/nimservice-rerank.yaml
```

## Profile Pinning Note

On first boot, each NIM inspects the available GPU and selects a profile. For LLMs this normally means a TensorRT-LLM profile when supported, otherwise a fallback such as vLLM. A profile-hash mismatch can crash the pod, so the burst run must verify `NIMCache.status.profiles[].name` and pin the matching hash in each `NIMService.spec.storage.nimCache.profile` before preserving the final evidence branch.

All NIM services are `ClusterIP`. They are internal dependencies for the chain-server and should never be exposed through ALB, NodePort, or LoadBalancer.
