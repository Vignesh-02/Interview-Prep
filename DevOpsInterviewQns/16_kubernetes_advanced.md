# 16. Kubernetes Advanced

## Q1. (Beginner) What is a StatefulSet? When would you use it instead of a Deployment?

**Answer:**  
**StatefulSet**: **ordered** pod identity (stable **name**, **ordinal**); **stable** **storage** (PVC per pod); **ordered** deploy/scale. **Use** for **stateful** apps: **databases**, **Kafka**, **ZooKeeper**. **Deployment** for **stateless** (pods **interchangeable**).

---

## Q2. (Beginner) What is a PersistentVolume (PV) and PersistentVolumeClaim (PVC)?

**Answer:**  
**PV**: **cluster** **storage** (admin or **provisioner**); **PVC**: **request** for **storage** by **user** (size, **StorageClass**). **Binding**: **controller** binds **PVC** to **PV** (or **dynamic** **provisioning** creates **PV**). **Pod** uses **volume** from **PVC**; **data** survives **pod** **restart**.

---

## Q3. (Beginner) What is a StorageClass? What is dynamic provisioning?

**Answer:**  
**StorageClass**: **provisioner** (e.g. **ebs**, **gp2**); **params** (type, size); **reclaim** policy. **Dynamic** **provisioning**: **PVC** **creates** **PV** **on demand** (no pre-created **PV**). **Default** **StorageClass**: **PVC** without **class** uses **default**. **Use** for **cloud** disks (EBS, etc.) **per** **pod**.

---

## Q4. (Beginner) What does CrashLoopBackOff mean? What is the first thing you check?

**Answer:**  
**CrashLoopBackOff**: **container** **exits** (non-zero); K8s **restarts** with **backoff**. **First**: **logs** — `kubectl logs <pod> --previous` (crashed container); **describe** pod for **events** (OOMKilled, **image** pull, **config**). **Then**: **image**, **command**, **env**, **resources**, **mounts**.

---

## Q5. (Intermediate) Write a minimal StatefulSet for a database with one replica and a PVC (1Gi).

**Answer:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 1
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
      - name: db
        image: postgres:14
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

---

## Q6. (Intermediate) What is a readiness probe vs a liveness probe? What happens when each fails?

**Answer:**  
**Liveness**: **is** the process **alive**? **Fail** → **restart** container. **Readiness**: **should** **traffic** be **sent**? **Fail** → **remove** from **Service** (no **restart**). **Use** **readiness** for **slow** start or **temporary** unready; **liveness** for **deadlock**/hang. **Don’t** make **liveness** same as **readiness** if **failure** should not **restart**.

---

## Q7. (Intermediate) What is a PodDisruptionBudget (PDB)? When is it used?

**Answer:**  
**PDB**: **min** available or **max** unavailable **pods** (e.g. **minAvailable: 1** or **maxUnavailable: 1**). **Used** by **eviction** logic (drain, **cluster** **autoscaler**): **won’t** evict if it would **violate** **PDB**. **Use** for **HA** (e.g. **maxUnavailable: 0** for **critical** app).

---

## Q8. (Intermediate) How do you run a one-off command in the cluster (e.g. migration) without keeping a Deployment?

**Answer:**  
**Job**: **batch** workload; **run** to **completion** (0 **succeeded** = success). **Create** **Job** manifest with **restartPolicy: Never** or **OnFailure**; **command** and **args** for migration. **kubectl run** one-off: `kubectl run mig --image=myapp --restart=Never -- <cmd>`. **CronJob** for **scheduled** one-offs.

---

## Q9. (Intermediate) What is a DaemonSet? Give one use case.

**Answer:**  
**DaemonSet**: **one** pod **per** **node** (or **subset** by **selector**). **Use**: **node** **agent** (logging, **monitoring**), **storage** (e.g. **Ceph**), **network** (CNI), **security** (e.g. **Falco**). **Tolerations** often used to run on **master** nodes if needed.

---

## Q10. (Intermediate) How do you limit resource usage (CPU/memory) per pod and per namespace?

**Answer:**  
**Per pod**: **resources.limits** and **requests** in **container** spec. **Per namespace**: **ResourceQuota** (total **requests**/limits **per** namespace); **LimitRange** (default/ max **per** container or pod). **Example** LimitRange: **default** request **100m** CPU, **128Mi** memory; **max** **2** CPU.

---

## Q11. (Advanced) Production scenario: Pod is in CrashLoopBackOff. Walk through the exact kubectl sequence to find the root cause.

**Answer:**  
(1) **List**: `kubectl get pods -n <ns>` — **state** and **restarts**. (2) **Describe**: `kubectl describe pod <pod> -n <ns>` — **events** (OOMKilled, **ImagePullBackOff**, **config** error). (3) **Logs** (crashed): `kubectl logs <pod> -n <ns> --previous`. (4) **Logs** (current): `kubectl logs <pod> -n <ns> -f`. (5) **Exec** (if **stays** up briefly): `kubectl exec -it <pod> -- /bin/sh` and **inspect**. (6) **Config**: `kubectl get deployment <name> -o yaml`; **check** **image**, **env**, **volumes**. **Common**: **bad** **image**/tag, **missing** **secret**/config, **wrong** **command**, **OOM**, **readiness**/liveness **too** **aggressive**.

---

## Q12. (Advanced) How do you manage persistent data for a stateful app so data survives pod reschedule?

**Answer:**  
**PersistentVolumeClaim** (and **PV** or **StorageClass**). **StatefulSet** with **volumeClaimTemplates** so **each** pod gets **its** **PVC** (stable **name**). **Storage**: **cloud** disk (EBS, etc.) **ReadWriteOnce** or **shared** (EFS, NFS) for **ReadWriteMany** if needed. **Backup**: **snapshot** **PVC** or **dump** from **pod** to **object** store; **restore** to **new** **PVC** if **reschedule** to **new** node.

---

## Q13. (Advanced) What is the difference between rolling update and recreate strategy in a Deployment? When use each?

**Answer:**  
**Rolling**: **gradual** (max **unavailable** / **max** **surge**); **no** **downtime** if **readiness** is correct. **Recreate**: **terminate** all then **create** new; **downtime**. **Use** **rolling** for **HA**; **recreate** when **stateful** or **must** **replace** all at once (e.g. **schema** **migration** that can’t run **rolling**). **Default** is **rolling**.

---

## Q14. (Advanced) Production scenario: Node is being drained; pods are evicted but one Deployment has PDB minAvailable: 2 and only 2 replicas on that node. What happens?

**Answer:**  
**Drain** will **evict** **pods**; if **eviction** would leave **fewer** than **minAvailable** (2), **eviction** is **blocked** (API returns **error**). **Drain** **stalls** until **user** **removes** **PDB**, **scales** up, or **another** node has **replicas**. **Best**: **multiple** nodes and **PDB** so **drain** can **evict** **some** pods and **reschedule**; **or** **cordon** and **drain** in **stages** (scale up, then drain).

---

## Q15. (Advanced) How do you run a Pod on a specific node (e.g. GPU node)?

**Answer:**  
**NodeSelector**: **nodeSelector** in pod spec (e.g. **gpu: "true"**). **Node affinity** (preferred/required): **affinity.nodeAffinity** for **flexible** rules. **Taints** and **tolerations**: **taint** **GPU** nodes (e.g. **NoSchedule**); **toleration** on **pod** so **only** that **workload** schedules. **Use** **taints** when **restricting** **who** can use **nodes**; **nodeSelector** for **simple** **label** match.

---

## Q16. (Advanced) What is a HorizontalPodAutoscaler (HPA)? How do you base it on custom metrics?

**Answer:**  
**HPA**: **scale** **replicas** by **metric** (CPU, memory, or **custom**). **Custom**: **metrics** from **Metrics** **Server** or **Prometheus** (via **prometheus-adapter**); **HPA** **target** e.g. **pods** with **metric** **name** and **target** **value**. **Example**: scale on **requests_per_second** (from **adapter**). **External** metrics (e.g. **SQS** queue depth) via **external** metrics API.

---

## Q17. (Advanced) How do you debug a Service that has no endpoints (traffic not reaching pods)?

**Answer:**  
**Endpoints** = pods **matching** **Service** **selector**. **Check**: (1) `kubectl get endpoints <svc>` — **empty**? (2) **Selector** **match**: **Service** **selector** must **match** **pod** **labels**. (3) **Pods** **ready**: **readiness** **failing** → pods **not** in **endpoints**. (4) **Pods** in **same** **namespace**. **Fix**: **align** **labels**; **fix** **readiness** or **probes**; **ensure** **pods** **running** and **ready**.

---

## Q18. (Advanced) Production scenario: You need to run a legacy app that requires an init script and a main process that must never be restarted without the init. How do you model it?

**Answer:**  
**Init** **container**: **run** **script** (e.g. **migrate**, **chown**); **main** **container** **starts** after **init** **succeed**. **Single** **pod**; **shared** **volume** if **init** writes **data** for **main**. **Don’t** use **separate** **Deployments** (they can **restart** **independently**). **If** **main** **must** **never** **restart** without **re-run** **init**: **same** pod; **restartPolicy** **Never** or **OnFailure** and **handle** **restart** in **init** (idempotent **init** preferred so **restart** is **safe**).

---

## Q19. (Advanced) What are Pod security standards (restricted, baseline)? How do you enforce them?

**Answer:**  
**PSA** (Pod Security **Admission**): **baseline** (no **privileged**, **host** **paths** etc.); **restricted** (stricter, **drop** **capabilities**). **Enforce**: **namespace** **label** **pod-security.kubernetes.io/enforce: restricted** (or **baseline**). **Admission** **controller** **rejects** **non-compliant** **pods**. **Migrate**: **audit** then **warn** then **enforce**. **Alternative**: **OPA**/Gatekeeper **policies** for **custom** rules.

---

## Q20. (Advanced) Senior red flags to avoid in Kubernetes

**Answer:**  
- **Stateful** workload **without** **PVC** (data **lost** on **reschedule**).  
- **No** **resource** **requests**/limits (no **scheduling** **guarantee**; **OOM** risk).  
- **Liveness** **same** as **readiness** or **too** **aggressive** (restart **loops**).  
- **latest** **tag** or **no** **readiness** (traffic to **unready** **pods**).  
- **Secrets** in **plain** **YAML** in **Git** (use **external** **secrets**).  
- **No** **PDB** for **HA** **apps** (drain **kills** all **replicas**).  
- **Running** as **root** when **not** **needed** (use **securityContext**).  
- **No** **limits** (noise **neighbor** or **DoS**).

---

**Tradeoffs:** Startup: Deployments, single StorageClass. Medium: StatefulSets, PDB, HPA, resource limits. Enterprise: PSA, multi-tenant namespaces, custom metrics, backup/restore.
