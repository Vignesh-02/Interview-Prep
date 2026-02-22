# 14. Build, Artifacts & Registries

## Q1. (Beginner) What is a build artifact? Give two examples.

**Answer:**  
**Artifact**: **output** of a **build** that is **reused** (deploy, test, share). **Examples**: **JAR**/WAR (Java), **Docker image**, **npm** package (tgz), **binary** (Go), **zip** of static assets. **Stored** in **registries** or **repos** (Docker registry, Nexus, Artifactory, S3).

---

## Q2. (Beginner) What is a container image registry? Name two.

**Answer:**  
**Registry**: **store** and **serve** **container** **images** (by **name:tag**). **Examples**: **Docker Hub**, **Amazon ECR**, **GCR**, **Azure ACR**, **Harbor**, **Nexus**. **Push**: `docker push registry.io/myapp:v1`; **pull**: `docker pull registry.io/myapp:v1`. **K8s** uses **image** field and **imagePullSecrets** for **private** registries.

---

## Q3. (Beginner) What is the difference between a Docker image tag and digest?

**Answer:**  
**Tag**: **human** label (e.g. `v1.2`, `latest`); **mutable** (can point to **different** digest over time). **Digest**: **immutable** **hash** of image (e.g. `sha256:abc123...`); **unique** per **content**. **Use digest** for **reproducible** deploys; **use tag** for **convenience** (e.g. `latest`, `staging`). **Pin** in **prod** with **digest** or **immutable** tag.

---

## Q4. (Beginner) What does "build once, deploy everywhere" mean? Why is it important?

**Answer:**  
**Build** the **artifact** (e.g. **image**) **once** in **CI**; **deploy** the **same** artifact to **dev**, **staging**, **prod**. **No** rebuild per env. **Important**: **consistency** (same binary); **no** "works in staging, fails in prod" from **build** differences; **faster** deploys; **audit** (one artifact ID). **Environments** differ by **config**, not **artifact**.

---

## Q5. (Intermediate) How do you pull a private image in Kubernetes? Show the minimal setup.

**Answer:**  
**imagePullSecrets** on **ServiceAccount** or **Pod**. **Create secret**:  
`kubectl create secret docker-registry regcred --docker-server=<registry> --docker-username=<user> --docker-password=<token> --docker-email=<email>`  
**Pod**:  
```yaml
spec:
  imagePullSecrets:
  - name: regcred
  containers:
  - name: app
    image: myregistry.io/myapp:v1
```  
**Or** **default** ServiceAccount: `kubectl patch serviceaccount default -p '{"imagePullSecrets":[{"name":"regcred"}]}'`.

---

## Q6. (Intermediate) What is a multi-stage Docker build? Why use it?

**Answer:**  
**Multi-stage**: **multiple** **FROM** in one Dockerfile; **later** stages **copy** from **earlier**; **final** image **only** has **runtime** (no build tools). **Why**: **smaller** image; **fewer** **attack** surfaces; **no** compilers in prod. **Example**: **stage1** = build (Node, Maven); **stage2** = run (only **node**, **app** files).

---

## Q7. (Intermediate) How do you version artifacts for production (tagging strategy)?

**Answer:**  
**Options**: (1) **SemVer** tag: `v1.2.3` from **git** tag or **version** file. (2) **Git SHA**: `abc1234` (short commit); **reproducible**. (3) **CI build ID**: `build-12345`. (4) **Combo**: `v1.2.3-abc1234`. **Prod**: **avoid** `latest`; use **immutable** (digest or **fixed** tag). **Promotion**: **same** image **retag** (e.g. `staging` → `prod`) or **deploy** by **digest**.

---

## Q8. (Intermediate) What is artifact retention? Why set a policy?

**Answer:**  
**Retention**: **how long** to **keep** artifacts (images, logs, builds); **delete** or **archive** after **N** days or **N** versions. **Why**: **storage** cost; **compliance**; **reduce** **attack** surface (old vulnerable images). **Policy**: e.g. keep **last** 30 **tags**; keep **prod** tags **longer**; **delete** **untagged** after 7 days (ECR, Harbor).

---

## Q9. (Intermediate) How do you avoid storing secrets in a Docker image?

**Answer:**  
**Don’t** **COPY** secrets or **ENV** secrets in Dockerfile. **Use**: **runtime** **env** (K8s **Secret**, **env** vars); **mount** (K8s **Secret** as file); **external** (Vault, cloud secrets). **Build-time** secrets: **BuildKit** `--secret` (e.g. **npm** token) **not** in **final** layer. **Scan** images for **secrets** (e.g. **gitleaks**, **trivy**).

---

## Q10. (Intermediate) What is a package registry for language packages (e.g. npm, Maven)? How does CI use it?

**Answer:**  
**Registry**: **store** for **packages** (npm, Maven, PyPI, NuGet). **CI**: **install** deps from **registry**; **publish** **built** package (version from tag or file). **Private** registry (Nexus, Artifactory, GitHub Packages) for **private** deps and **proxy** to public. **Auth**: **token** in **CI** secret; **.npmrc** or **settings.xml** with **env** var.

---

## Q11. (Advanced) Production scenario: Build produces a Docker image; you need to deploy the same image to staging then prod after approval. How do you avoid rebuilding?

**Answer:**  
**Build once** in CI; **push** with **tag** (e.g. `git-SHA` or `build-123`). **Staging**: deploy that **tag** (or **digest**). **Approval**: **manual** gate or **automated** (tests). **Prod**: **same** image — **retag** to `prod-YYYYMMDD` for **audit** or **deploy** by **same** tag/digest. **No** rebuild; **promotion** = **pointer** (tag) or **re-deploy** same **image** ref. **Pipeline**: build → push → deploy staging → gate → deploy prod (same ref).

---

## Q12. (Advanced) How do you implement artifact signing (e.g. cosign) and verify in Kubernetes?

**Answer:**  
**Sign**: **cosign** (Sigstore) **sign** image: `cosign sign --key cosign.key myregistry.io/myapp:v1`. **Push** **signature** to **registry** (OCI artifact). **Verify**: **admission** (e.g. **Connaisseur**, **Gatekeeper** with **image** policy) **reject** if **unsigned** or **wrong** key. **K8s**: **ValidatingWebhook** that **checks** **image** **signature** before **pod** create. **Result**: only **signed** images **run** in cluster.

---

## Q13. (Advanced) What is a monorepo build strategy? How do you only build artifacts for changed services?

**Answer:**  
**Monorepo**: **many** services in **one** repo. **Build** only **changed**: **detect** **changed** **paths** (e.g. `git diff main --name-only`); **map** paths to **services**; **build** only those **services**. **Tools**: **Nx**, **Turborepo**, **Bazel** (with **targets**). **CI**: **matrix** or **parallel** jobs per **changed** service; **publish** only **changed** artifacts. **Cache**: **reuse** **layers**/deps for **unchanged** services.

---

## Q14. (Advanced) Production scenario: Your registry is down; deployments fail. How do you reduce impact next time?

**Answer:**  
(1) **Cache** in **cluster**: **pull-through** cache or **local** mirror; **nodes** pull from **cache** when **upstream** down. (2) **Multi-registry**: **push** to **two** registries; **deploy** from **secondary** if **primary** down. (3) **Image** **replication** (Harbor, ECR replication) to **another** region. (4) **Keep** **last** N **images** on **nodes** (don’t **evict** immediately) so **restart** can use **cached** image. (5) **SLO** and **alerting** for **registry**; **runbook** for **failover**.

---

## Q15. (Advanced) How do you scan images for vulnerabilities in CI and block deploy if critical?

**Answer:**  
**Scan** in **CI** after **build**: **Trivy**, **Snyk**, **Clair** (e.g. `trivy image --exit-code 1 --severity CRITICAL myimage:tag`). **Block**: **exit code 1** on **CRITICAL** → **fail** pipeline; **no** push to **prod** registry. **Optional**: **allow** **exceptions** (CVE **waiver** with **ticket**); **report** to **dashboard**. **Runtime**: **admission** or **periodic** scan in **cluster** as **second** layer.

---

## Q16. (Advanced) What is an artifact repository (Nexus, Artifactory) vs a container registry? When use both?

**Answer:**  
**Artifact repo**: **generic** (JAR, npm, raw); **versioning**, **proxy** to public, **single** place. **Container registry**: **OCI**/Docker **images**. **Both**: **Artifactory**/Nexus can **hold** **both** (containers + packages). **Use both** when: **one** org **tool** for **all** artifacts; **compliance** (scan, retention); **single** **auth**. **Use** **only** registry when **containers** only and **simplicity** preferred.

---

## Q17. (Advanced) How do you clean up old images (untagged, by age) in a registry without breaking running workloads?

**Answer:**  
**Identify** **in use**: **images** referenced by **running** **pods**/replicasets (e.g. **K8s** API or **deploy** history). **Delete** only **not** in use and **older** than **N** days or **untagged**. **Tools**: **registry** **GC** (Harbor, ECR **lifecycle**); **script** that **lists** tags, **checks** **usage**, **deletes** safe ones. **Safety**: **never** delete **tag** that **prod** uses; **retain** **min** versions per **app**; **dry-run** first.

---

## Q18. (Advanced) Production scenario: You have 50 microservices; each produces an image. How do you organize registry and naming?

**Answer:**  
**Naming**: **registry/org/team/service:tag** (e.g. `ecr.io/acme/order-service:v1.2`). **Organize**: **repo** per **service** or **path** per **team**; **tags** = **version** or **SHA**. **Automate**: **CI** **derives** **name** from **repo**/path; **single** **pipeline** **template** per **service**. **Policy**: **immutable** tags for **prod**; **retention** per **repo**. **Discovery**: **catalog** API or **convention** (all under **org**).

---

## Q19. (Advanced) How do you replicate images from one registry to another (e.g. region or DR)?

**Answer:**  
**Push** to **both** in CI (parallel push) or **single** push + **replication**. **Replication**: **Harbor** replication **rules**; **ECR** **replication**; **custom** job that **pulls** from **source**, **pushes** to **target**. **Trigger**: **webhook** on **push** or **scheduled**. **Sync** **tags** and **signatures**; **DR**: **deploy** from **replica** if **primary** region down.

---

## Q20. (Advanced) Senior red flags to avoid with builds and registries

**Answer:**  
- **Rebuilding** per env (not **build once**).  
- **Using** `latest` or **mutable** tag in **prod**.  
- **Secrets** in **image** or **Dockerfile**.  
- **No** **vulnerability** scan before **deploy**.  
- **No** **retention** (unbounded **storage**).  
- **No** **signing** (no **integrity** guarantee).  
- **Single** registry **no** **failover** plan.  
- **No** **naming** convention (chaos in **50** services).

---

**Tradeoffs:** Startup: single registry, tag by SHA. Medium: retention, scan in CI, naming convention. Enterprise: signing, replication, artifact repo, monorepo build.
