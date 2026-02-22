# 17. Docker Advanced

## Q1. (Beginner) What is a multi-stage build? Write a two-stage Dockerfile for a Node app.

**Answer:**  
**Multi-stage**: **multiple** **FROM**; **copy** artifacts from **earlier** stage; **final** image has **no** build tools. **Example**:
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

---

## Q2. (Beginner) What is the difference between COPY and ADD? When use ADD?

**Answer:**  
**COPY**: **copy** **files** from **context** (preferred). **ADD**: **copy** + **extract** **tar**; **fetch** **URL** (not **recommended** for URL). **Use** **ADD** only for **local** **tar** **extract**; **otherwise** **COPY** and **RUN** **curl**/wget for **URLs** (better **cache** and **control**).

---

## Q3. (Beginner) What does "running as root" in a container mean? How do you avoid it?

**Answer:**  
**Default** **user** in **container** is **root**. **Risk**: **breakout** or **host** **impact** if **compromised**. **Avoid**: **USER** **non-root** in Dockerfile (e.g. **USER** **node** or **create** **user** and **USER** **uid**). **K8s**: **securityContext.runAsNonRoot**; **readOnlyRootFilesystem** where possible.

---

## Q4. (Beginner) What is an image layer? Why does order of Dockerfile instructions matter?

**Answer:**  
**Layer**: **each** **instruction** (RUN, COPY, etc.) **adds** a **layer** (cached). **Order**: **change** **early** line → **invalidate** **cache** for **all** **later** lines. **Best**: **copy** **deps** **first** (package.json), **RUN** **install**, **then** **COPY** **source** so **code** **changes** don’t **rebuild** **deps**.

---

## Q5. (Intermediate) How do you pass a build-time secret (e.g. private npm token) without leaving it in the image?

**Answer:**  
**BuildKit**: **--secret** at **build**: `docker build --secret id=npm,src=$HOME/.npmrc .` **Dockerfile**: `RUN --mount=type=secret,id=npm npm ci` (mount **secret** during **run**; **not** in **layer**). **CI**: **token** from **secret** store; **write** to **file** or **env** and **pass** as **secret**. **Never** **COPY** **.npmrc** with **token** into **image**.

---

## Q6. (Intermediate) What is the difference between ENTRYPOINT and CMD? How do they work together?

**Answer:**  
**CMD**: **default** **args** for **container**; **overridden** by **docker run** **args**. **ENTRYPOINT**: **fixed** **executable**; **docker run** **args** become **args** to **entrypoint**. **Together**: **ENTRYPOINT** ["exec"] **CMD** ["arg1"] → **exec** **arg1**; **run** **args** **replace** **CMD**. **Use** **ENTRYPOINT** for **wrapper** (e.g. **docker-entrypoint.sh**); **CMD** for **default** **args**.

---

## Q7. (Intermediate) How do you reduce image size for a compiled app (e.g. Go)?

**Answer:**  
**Multi-stage**: **build** in **full** image (e.g. **golang**); **copy** **binary** to **scratch** or **alpine**. **Static** **binary**: **CGO_ENABLED=0** for **Go**. **Result**: **final** image = **binary** + **ca-certs** (if **HTTPS**). **Example** final: `FROM scratch` or `FROM alpine`; **COPY** **--from=builder** **/app/bin** **/app**.

---

## Q8. (Intermediate) What is Docker build cache? When is a layer cache invalidated?

**Answer:**  
**Cache**: **each** **layer** is **cached** by **content** (instruction + **parent** **layers**). **Invalidation**: **any** **change** in **instruction** or **input** **files** (COPY **checksum**) **invalidates** that **layer** and **all** **following**. **Optimize**: **least** **frequently** **changing** **first** (deps → source); **pin** **base** **image** **digest**.

---

## Q9. (Intermediate) How do you run a container with a read-only root filesystem? Why would you?

**Answer:**  
**Run**: `docker run --read-only ...` **K8s**: **securityContext.readOnlyRootFilesystem: true**. **Why**: **attackers** can’t **write** to **filesystem**; **tampering** **reduced**. **Need** **writable** **dir**: **mount** **tmpfs** or **volume** for **tmp**/cache (e.g. **/tmp**).

---

## Q10. (Intermediate) What is the OCI image spec? Why does it matter?

**Answer:**  
**OCI**: **Open** **Container** **Initiative** **spec** for **image** **format** (layers, **config**, **manifest**). **Matters**: **interop** (Docker, **Podman**, **containerd**, **K8s** all **consume** **OCI**); **registries** **store** **OCI**; **tooling** (buildah, **kaniko**) **produce** **OCI**. **Same** **image** **runs** **everywhere**.

---

## Q11. (Advanced) Production scenario: Image build is slow in CI. What strategies do you use to speed it up?

**Answer:**  
(1) **Cache**: **registry** **cache** (e.g. **docker build --cache-from**); **CI** **cache** **layer** **cache** (GHA **cache**, **BuildKit** **cache** **mount**). (2) **Multi-stage**: **small** **final** **stage**; **parallel** **stages** if **BuildKit**. (3) **Deps** **first**: **copy** **package.json** only; **install**; **then** **copy** **source**. (4) **Smaller** **base** (alpine, **distroless**). (5) **Build** **only** **changed** **services** (monorepo). (6) **Remote** **build** (e.g. **Kaniko** in **cluster**) to **avoid** **docker** **daemon** **bottleneck**.

---

## Q12. (Advanced) How do you scan an image for vulnerabilities in the Dockerfile and block push if critical?

**Answer:**  
**Scan** after **build**: **Trivy** `trivy image --exit-code 1 --severity CRITICAL,HIGH myimg:tag`; **Snyk**; **Docker** **scan**. **CI**: **step** after **build**; **fail** **pipeline** if **exit-code 1**. **Block** **push**: **registry** **policy** (Harbor **CVE** **block**) or **admission** in **K8s** (only **approved** **images**). **Remediate**: **rebuild** with **updated** **base**; **pin** **base** **digest** and **rebase** **regularly**.

---

## Q13. (Advanced) What is distroless image? When would you use it?

**Answer:**  
**Distroless**: **minimal** **image** (no **shell**, **package** **manager**); **only** **app** + **runtime** (e.g. **node**, **java**). **Use**: **smaller** **surface**; **no** **shell** to **exec** into (harder to **abuse**). **Debug**: **sidecar** or **ephemeral** **container** with **debug** **image**; **or** **local** **build** with **shell** for **dev**. **Best** for **prod** **images**.

---

## Q14. (Advanced) Production scenario: Container runs as root and was compromised. Attacker wrote files under /. How do you prevent this in future?

**Answer:**  
(1) **Run** as **non-root**: **USER** in Dockerfile; **runAsNonRoot** in K8s. (2) **Read-only** **root** **filesystem**; **writable** **volumes** only where **needed** (e.g. **/tmp** **tmpfs**). (3) **Drop** **capabilities**; **no** **privileged**. (4) **Network** **policy** to **limit** **egress**. (5) **Image** **scan** and **patch**; **admission** to **block** **privileged**/root. **Post-incident**: **rotate** **secrets**; **rebuild** **image** with **hardening**; **forensics** from **logs**/audit.

---

## Q15. (Advanced) How do you achieve reproducible builds (same digest for same source)?

**Answer:**  
**Pin** **base** **image** by **digest** (not **tag**). **Pin** **deps** (npm **lock**, **go** **sum**, **pip** **lock**). **Deterministic** **build** **order**; **no** **timestamps** in **output** (e.g. **SOURCE_DATE_EPOCH**). **Build** in **clean** **env** (same **builder** **image**). **Result**: **same** **source** → **same** **layers** → **same** **digest**. **Verify**: **rebuild** and **compare** **digest**.

---

## Q16. (Advanced) What is Docker socket (/var/run/docker.sock) mount? Why is it dangerous?

**Answer:**  
**Mount** **docker.sock** into **container** = **container** can **talk** to **Docker** **daemon** (run **containers**, **see** **all** **containers**). **Danger**: **privilege** **escalation** (run **privileged** **container** = **host** **access**). **Avoid** in **prod**; **if** **needed** (e.g. **DinD** in CI) **isolate** (dedicated **node**, **read-only** where possible). **Prefer** **Kaniko**/build **outside** **daemon** in CI.

---

## Q17. (Advanced) How do you run Docker build in a environment with no Docker daemon (e.g. restricted CI)?

**Answer:**  
**Kaniko**: **build** **image** **inside** **container** (no **daemon**); **reads** **Dockerfile** and **context** (e.g. **GCS**, **S3**); **pushes** to **registry**. **Buildah**: **rootless** **build**; **output** **OCI**. **BuildKit** **remote** **builder**: **daemon** elsewhere. **CI**: **run** **Kaniko** **image** with **context** **mounted**; **push** to **registry**. **No** **docker** **socket** **needed**.

---

## Q18. (Advanced) How do you limit container resource usage (CPU, memory) at runtime in Docker and Kubernetes?

**Answer:**  
**Docker**: `docker run --cpus=0.5 --memory=512m ...` **K8s**: **resources.limits** (and **requests**) in **pod** spec: **cpu: "500m"**, **memory: "512Mi"**. **Enforcement**: **Docker** uses **cgroups**; **K8s** **kubelet** **enforces** **limits** (OOMKill if **over** **memory**). **Always** set **limits** in **prod** to **avoid** **noisy** **neighbor**.

---

## Q19. (Advanced) What is image signing (e.g. cosign)? How does it improve supply chain security?

**Answer:**  
**Signing**: **sign** **image** **digest** with **key** (e.g. **cosign** **sign**); **signature** stored as **OCI** **artifact** or **in** **registry**. **Verify**: **admission** or **policy** **rejects** **unsigned** or **wrong** **key** **images**. **Improves**: **integrity** (image **not** **tampered**); **provenance** (built by **trusted** **pipeline**). **Part** of **supply** **chain** **security** (build → sign → verify → run).

---

## Q20. (Advanced) Senior red flags to avoid with Docker

**Answer:**  
- **Running** as **root** in **prod**.  
- **Secrets** in **image** or **COPY** **.env**.  
- **No** **multi-stage** (huge **prod** **image** with **build** **tools**).  
- **Using** **latest** **tag** for **base** or **app**.  
- **No** **vulnerability** **scan** before **push**.  
- **Mounting** **docker.sock** in **prod**.  
- **No** **resource** **limits** (CPU/memory).  
- **Non-reproducible** **builds** (no **lock** **files**, **floating** **base** **tag**).

---

**Tradeoffs:** Startup: single-stage, small base. Medium: multi-stage, non-root, scan in CI. Enterprise: distroless, signing, Kaniko, reproducible builds.
