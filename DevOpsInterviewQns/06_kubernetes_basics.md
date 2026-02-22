# 6. Kubernetes Basics

## Q1. (Beginner) What is a Pod? Why is it the smallest deployable unit and not a container?

**Answer:**  
**Pod**: one or more **containers** that share **network** (IP) and **storage** (volumes); same node. **Smallest unit**: Kubernetes **schedules** and **scales** pods; containers in a pod are **always** together. So you deploy a **pod** (e.g. app + sidecar); Kubernetes manages pods, not raw containers.

---

## Q2. (Beginner) What is a Deployment? What does it provide over creating Pods directly?

**Answer:**  
**Deployment**: **declarative** updates for Pods (and ReplicaSet); **rolling** update, **rollback**; **desired** replica count. **Over raw Pods**: **replicas** (maintains N pods); **self-healing** (recreates failed pods); **rolling** strategy; **history** for rollback. **Don’t** create Pods directly for workloads; use **Deployment**.

---

## Q3. (Beginner) What is a Service? What are ClusterIP, NodePort, and LoadBalancer?

**Answer:**  
**Service**: **stable** network endpoint for pods (selector); load-balances to pod IPs. **ClusterIP**: **internal** cluster IP (default). **NodePort**: expose on **each node’s** port (30000–32767). **LoadBalancer**: cloud **LB** (e.g. AWS ELB). **Use**: ClusterIP for in-cluster; NodePort for dev; LoadBalancer for external.

---

## Q4. (Beginner) How do you get a shell inside a running pod? How do you view logs of a container?

**Answer:**  
**Shell**: `kubectl exec -it <pod> -- /bin/sh` (or bash). **Logs**: `kubectl logs <pod>`; **follow**: `kubectl logs -f <pod>`; **previous** (crashed): `kubectl logs <pod> --previous`.

---

## Q5. (Intermediate) Write a minimal Deployment YAML for an app image `myapp:v1` with 3 replicas and a ClusterIP Service on port 80.

**Answer:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v1
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

---

## Q6. (Intermediate) What is a ConfigMap and a Secret? How do you mount them into a pod?

**Answer:**  
**ConfigMap**: **non-sensitive** config (key-value or file). **Secret**: **sensitive** data (base64 or opaque). **Mount**: **volume** in pod: `volumes`: from **configMap** or **secret**; **volumeMounts** in container. **Env**: `envFrom` or `valueFrom` (configMapKeyRef/secretKeyRef). **Never** put real secrets in Git; use **external** secret store (e.g. Vault, cloud) and sync to K8s Secret.

---

## Q7. (Intermediate) What is a namespace? When would you create separate namespaces?

**Answer:**  
**Namespace**: **virtual** cluster; resource names are scoped; **RBAC** and **quotas** can be per-namespace. **Use**: **env** (dev, staging, prod); **team**; **multi-tenant**. **Default**: `default`; **kube-system** for system. Create namespaces for **isolation** and **policy**.

---

## Q8. (Intermediate) What is a liveness probe vs a readiness probe? What happens when each fails?

**Answer:**  
**Liveness**: is the **process** alive? **Fail** → **restart** container. **Readiness**: is the app **ready** to receive traffic? **Fail** → **remove** from Service endpoints (no restart). **Use**: **liveness** for “stuck” process; **readiness** for “warming up” or “overloaded”. **Example**: liveness = /healthz; readiness = /ready (checks DB).

---

## Q9. (Intermediate) How do you set resource requests and limits on a container? What happens when a container exceeds its memory limit?

**Answer:**  
**In spec**: `resources: requests: memory: "128Mi" cpu: "100m"; limits: memory: "256Mi" cpu: "200m"`. **Exceeds memory limit**: **OOMKilled** (exit 137). **Requests**: used for **scheduling** (node must have that much available). **Limits**: **cap**; CPU is throttled; memory is hard limit.

---

## Q10. (Intermediate) What is kubectl apply vs create? What is declarative vs imperative?

**Answer:**  
**create**: **imperative**; create resource once. **apply**: **declarative**; create or **patch** to match file; **three-way** merge (last applied, current, new). **Prefer apply** for **GitOps** and **repeated** updates. **Declarative**: you describe **desired** state; K8s **reconciles**. **Imperative**: you run **commands** (create, replace).

---

## Q11. (Advanced) Production scenario: A pod is not starting. What is your systematic debugging sequence using kubectl?

**Answer:**  
(1) **Pod**: `kubectl get pods` (Pending? CrashLoopBackOff?); `kubectl describe pod <name>` (Events, conditions). (2) **Pending**: **scheduling** (node selector, resources, taints); check **Events**. (3) **CrashLoopBackOff**: `kubectl logs <pod> --previous`; **image** pull? **config**? **liveness** failing? (4) **ImagePullBackOff**: **image** name, **pull secret**, **network**. (5) **Not Ready**: **readiness** failing; check **probe** endpoint. (6) **describe** and **logs** are the main tools; then **exec** if pod is running.

---

## Q12. (Advanced) What is a ReplicaSet? How does it relate to a Deployment?

**Answer:**  
**ReplicaSet**: maintains **desired** number of pod **replicas** (by selector); **no** rollout strategy. **Deployment**: **manages** ReplicaSets; **rolling** update creates new ReplicaSet, scales it up, scales old down; **rollback** = switch to previous ReplicaSet. You **don’t** create ReplicaSets directly; you create **Deployments**.

---

## Q13. (Advanced) How do you expose a Deployment to the internet (e.g. HTTP) on a cloud cluster? What resources are involved?

**Answer:**  
(1) **Service** type **LoadBalancer** (or **Ingress**). (2) **LoadBalancer**: K8s creates cloud **LB** (e.g. AWS ELB); **Ingress** controller (e.g. nginx, AWS ALB) creates **LB** and routes by host/path. (3) **Ingress** resource: host, path → **Service** (ClusterIP). (4) **TLS**: **Ingress** with **tls** and **cert-manager** or cloud cert. **Result**: external traffic → LB → Service → Pods.

---

## Q14. (Advanced) What is the difference between an emptyDir volume and a PersistentVolumeClaim? When would you use each?

**Answer:**  
**emptyDir**: **temporary**; created with pod; **deleted** when pod is removed; **same node**. **Use**: cache, scratch. **PVC**: **persistent**; binds to **PV** (storage); **survives** pod restart; can be **shared** (depending on storage class). **Use**: **DB data**, **stateful** app. **StatefulSet** often uses **PVC** per pod.

---

## Q15. (Advanced) Production scenario: You need to run a one-off migration job (e.g. DB migrate) in the cluster. How do you run it without a long-running Deployment?

**Answer:**  
**Job**: create a **Job** resource; runs **one** or more pods until **success** (completions); **restart** on failure (backoffLimit). **Example**: image with migrate script; **Job** with **restartPolicy: OnFailure**; **env** or **Secret** for DB URL. **CronJob** if it’s **scheduled**. **Don’t** use Deployment for one-off; use **Job**.

---

## Q16. (Advanced) How do you run a Pod on a specific node (e.g. a node with GPU)? What are nodeSelector and affinity?

**Answer:**  
**nodeSelector**: **simple** key-value; pod runs only on nodes with that label. **Affinity** (nodeAffinity): **richer** (in/notIn, exists); **preferred** vs **required**. **Example**: `nodeSelector: gpu: "true"` or **nodeAffinity** requiredDuringScheduling with **label** gpu=true. **Taints/tolerations**: **reverse** — node **taints**; pod needs **toleration** to run there.

---

## Q17. (Advanced) What is a HorizontalPodAutoscaler (HPA)? What metrics can it use?

**Answer:**  
**HPA**: **scales** Deployment (or other) by **replicas** based on **metrics**. **Metrics**: **CPU** (default), **memory** (metrics-server); **custom** (Prometheus) with custom metrics API. **Example**: scale when **CPU** > 70%; min 2, max 10. **Requires** **metrics-server** (or adapter for custom) for metrics.

---

## Q18. (Advanced) How do you give a Pod access to AWS (e.g. S3) without putting keys in the image or ConfigMap?

**Answer:**  
**IRSA** (IAM Roles for Service Accounts): (1) **ServiceAccount** with **annotation** (eks.amazonaws.com/role-arn). (2) **IAM** role with **trust** to that ServiceAccount (OIDC). (3) **Pod** uses this **serviceAccountName**; gets **temporary** credentials via projected volume. **No** keys in image or ConfigMap; **least privilege** IAM role.

---

## Q19. (Advanced) Production scenario: A Deployment has 3 replicas but only 1 is Ready; the other 2 are in CrashLoopBackOff. How do you find the root cause and fix it?

**Answer:**  
(1) **Which**: `kubectl get pods`; **describe** and **logs** for a **crashing** pod: `kubectl logs <pod> --previous`. (2) **Common**: **app** error (config, DB connection); **OOM**; **liveness** too aggressive; **image** or **command** wrong. (3) **Fix**: fix **config**/Secret, **increase** memory or fix **leak**, **relax** liveness (or fix endpoint), fix image. (4) **Rollback** if needed: `kubectl rollout undo deployment/myapp`. (5) **Prevent**: **resource limits**, **health** checks, **staging** tests.

---

## Q20. (Advanced) Senior red flags to avoid in Kubernetes

**Answer:**  
- **Creating Pods** directly (use Deployment/StatefulSet).  
- **No resource** requests/limits (noisy neighbor, bad scheduling).  
- **Secrets** in image or plain ConfigMap.  
- **No liveness/readiness** (or wrong probe).  
- **latest** tag in production (use digest or version tag).  
- **No namespace** or RBAC (everything in default, overly broad).  
- **Ignoring** HPA and scaling (single replica in prod).  
- **No** network policy (all pods can talk to all).

---

**Tradeoffs:** Startup: minimal YAML, single namespace. Medium: HPA, limits, probes, RBAC. Enterprise: GitOps, policy, scanning, multi-tenant.
