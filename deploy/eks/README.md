# FinRAG Phase 5 EKS GPU Burst

**COST SAFETY FIRST: tear down with `eksctl delete cluster -f deploy/eks/cluster.yaml --wait` as soon as proof is captured.**

This folder pre-stages the EKS cluster definition for the Phase 5 GPU proof. It does not run anything by itself.

## Prerequisites

- AWS CLI authenticated to the target account and region.
- `eksctl`, `kubectl`, and `helm` installed locally.
- EC2 GPU quota for `g5.xlarge` in the selected region.
- An NVIDIA NGC API key with access to NIM containers and model assets.
- An EFS CSI StorageClass named `efs-sc` before applying `deploy/storage/pvc.yaml`.
- AWS Load Balancer Controller installed before applying `deploy/app/ingress.yaml`.

## Create The Cluster

```bash
# Review region, node sizes, and maxSize before creating billable resources.
eksctl create cluster -f deploy/eks/cluster.yaml

# eksctl normally writes kubeconfig automatically; this makes the context explicit.
aws eks update-kubeconfig --region us-east-1 --name finrag-phase5-gpu
```

## Verify Nodes

```bash
# WHAT: confirms the CPU and GPU node groups joined the EKS control plane.
kubectl get nodes -L finrag.io/node-pool,nvidia.com/gpu.product

# WHY: the GPU Operator later advertises nvidia.com/gpu allocatable capacity.
kubectl describe nodes | grep -A4 -E "Allocatable|nvidia.com/gpu"
```

## Install Remaining Layers

Apply the folders in this order so dependencies exist before consumers:

```bash
# 1. NVIDIA GPU Operator
less deploy/gpu-operator/install.md

# 2. EFS-backed RWX model cache PVC
kubectl apply -f deploy/storage/pvc.yaml

# 3. NVIDIA NIM Operator and NIM CRs
less deploy/nim-operator/install.md

# 4. Milvus, chain-server, observability, adapter, HPA, Locust
less deploy/PHASE5-RUNBOOK.md
```

## Teardown

```bash
# Prominent duplicate on purpose: this cluster contains GPU nodes.
eksctl delete cluster -f deploy/eks/cluster.yaml --wait
```

Do not leave the cluster up overnight. The intended proof window is one day: create, capture `nvidia-smi`, Grafana panels, HPA scaling, and NIM logs, then delete.
