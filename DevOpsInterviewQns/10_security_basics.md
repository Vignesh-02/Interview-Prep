# 10. Security Basics (DevSecOps)

## Q1. (Beginner) What is the principle of least privilege? Give one example in DevOps.

**Answer:**  
**Least privilege**: grant **only** the **minimum** access needed. **Example**: **CI** role can **read** repo and **write** to **one** artifact bucket; **cannot** delete bucket or access prod DB. **K8s**: **ServiceAccount** per app with **only** needed RBAC. **SSH**: user only on servers they need.

---

## Q2. (Beginner) What is a vulnerability scan? What is the difference between SAST and DAST?

**Answer:**  
**Vulnerability scan**: **find** known **weaknesses** (CVEs, misconfig). **SAST** (Static): **source** code (or config) **without** running; **DAST** (Dynamic): **running** app (e.g. HTTP probes). **SAST** = code/config; **DAST** = runtime. **Use both**: SAST in **CI**; DAST in **staging** or prod.

---

## Q3. (Beginner) What is secret sprawl? How do you avoid it?

**Answer:**  
**Secret sprawl**: **secrets** in **code**, **config**, **logs**, **screenshots**. **Avoid**: (1) **Never** commit secrets; use **secret** store (Vault, cloud). (2) **Scan** (pre-commit, CI) for patterns. (3) **Rotate** after leak. (4) **Inject** at **runtime** (env, file from vault). (5) **Least** privilege for who can read secrets.

---

## Q4. (Beginner) What is a base image? Why scan it?

**Answer:**  
**Base image**: **parent** image in Dockerfile (e.g. node:18-alpine). **Scan**: find **CVEs** in **OS** and **packages**; **outdated** or **vulnerable** layers. **Tool**: Trivy, Snyk, Clair. **Use**: **block** build or **alert** on **critical**; **update** base and **rebuild**. **Pin** base **tag** (not latest).

---

## Q5. (Intermediate) What is dependency scanning? How do you integrate it into CI?

**Answer:**  
**Dependency scan**: check **app** deps (npm, pip, Maven) for **known** CVEs. **CI**: **step** after install (e.g. `npm audit`, `pip-audit`, or **Snyk/Trivy**); **fail** or **warn** on **high/critical**. **Report** in pipeline; **fix** by upgrading or patching. **Shift-left**: catch before **merge**.

---

## Q6. (Intermediate) What is image signing (e.g. cosign)? Why would you use it?

**Answer:**  
**Signing**: **cryptographic** signature on **image** (digest); **verify** before **run**. **cosign**: **keyless** or **key-based** signing (e.g. in CI). **Use**: **ensure** image is from **trusted** build (not tampered); **policy** (e.g. only signed images in prod). **Supply chain** security.

---

## Q7. (Intermediate) What is a security group (cloud) vs network policy (K8s)? What do they control?

**Answer:**  
**Security group** (AWS, etc.): **firewall** at **instance** or **ENI**; **allow** by IP/port and **other** SG. **NetworkPolicy** (K8s): **allow/deny** **pod** traffic by **pod** selector and **namespace**. **Both**: **restrict** who can talk to whom. **SG** = node/VM level; **NP** = pod level.

---

## Q8. (Intermediate) What is RBAC? How does it apply in Kubernetes?

**Answer:**  
**RBAC** (Role-Based Access Control): **roles** (set of **permissions**); **bindings** (who has which role). **K8s**: **Role** (namespace-scoped) or **ClusterRole**; **RoleBinding** / **ClusterRoleBinding** (subject = user, group, ServiceAccount). **Example**: **dev** Role = get/list pods in namespace; **prod** = read-only. **Principle**: **least** privilege per role.

---

## Q9. (Intermediate) What is OWASP Top 10? Name three and how DevOps can help mitigate.

**Answer:**  
**OWASP Top 10**: top **web** app risks. **Examples**: **A01 Broken Access Control** — **auth** and **RBAC**; **A02 Cryptographic Failures** — **TLS**, no sensitive in logs. **A03 Injection** — **parameterized** queries; **WAF**. **A07 Identifies and Auth** — **MFA**, **secrets** in vault. **DevOps**: **WAF**, **TLS**, **secret** management, **scan** (SAST/DAST), **hardened** images.

---

## Q10. (Intermediate) How do you handle secrets in a CI/CD pipeline (e.g. deploy key, API token)?

**Answer:**  
**Store**: **Jenkins** credentials, **Vault**, **cloud** (Secrets Manager); **never** in repo. **Use**: **withCredentials** (Jenkins), **env** from secret (K8s), **fetch** at runtime (app). **Pipeline**: **reference** by **id**; **mask** in logs. **Rotate** periodically; **audit** access. **Least** privilege for pipeline **role**.

---

## Q11. (Advanced) Production scenario: A container image in your registry has a critical CVE. The image is used in 20 deployments. How do you remediate without long downtime?

**Answer:**  
(1) **Fix**: **rebuild** image with **patched** base or **dependency**; **push** new tag (e.g. v1.0.1). (2) **Deploy**: **rolling** update — change **deployment** image to new tag; **rollout** (K8s) or **replace** tasks (ECS). (3) **Scan** again to **confirm** CVE gone. (4) **Retire** old tag (don’t use). (5) **Prevent**: **block** deploy of **critical** CVE in **CI** (gate); **automated** rebuild on base update. **Tradeoff**: Startup = manual; enterprise = auto-scan gate and patching pipeline.

---

## Q12. (Advanced) What is shift-left security? Give two examples in CI/CD.

**Answer:**  
**Shift-left**: **security** earlier in **lifecycle** (design, code, build) not only in prod. **CI examples**: (1) **SAST** in **pipeline** (code scan); **fail** on **high**. (2) **Dependency** and **image** scan in **build**; **block** on **critical**. (3) **IaC** scan (Terraform, K8s YAML) for **misconfig**. (4) **Secrets** scan (no commit). **Result**: **find** and **fix** before **deploy**.

---

## Q13. (Advanced) What is a software bill of materials (SBOM)? Why is it important for supply chain security?

**Answer:**  
**SBOM**: **list** of **components** (packages, versions) in an **artifact** (image, app). **Format**: SPDX, CycloneDX. **Why**: **know** what you ship; **respond** to **CVE** (is this lib in our image?); **compliance** and **audit**. **Generate**: in **CI** (e.g. Syft, Trivy); **store** and **query** when **CVE** is announced.

---

## Q14. (Advanced) Production scenario: You need to allow a third-party to deploy to your cluster (e.g. vendor) with minimal access. How do you design RBAC and namespaces?

**Answer:**  
(1) **Namespace**: **dedicated** namespace (e.g. `vendor-x`). (2) **Role**: **Role** in that namespace — **get/list/update** **their** resources (Deployments, Pods, ConfigMaps in that namespace only); **no** **cluster** admin, **no** other namespaces. (3) **ServiceAccount** (or **user**) for vendor; **RoleBinding** to that Role. (4) **NetworkPolicy**: **limit** egress to **needed** (e.g. their API only). (5) **Audit**: **log** their actions. **Least** privilege: **only** that namespace and **only** needed verbs.

---

## Q15. (Advanced) What is policy as code (e.g. OPA)? How does it enforce "no privileged containers" in Kubernetes?

**Answer:**  
**Policy as code**: **rules** in **code** (e.g. Rego); **evaluated** against **config** or **admission**. **OPA** (Open Policy Agent): **admission** controller in K8s; **validates** (and can **mutate**) **pod** spec. **Rule**: **deny** if `container.securityContext.privileged == true`. **Result**: **no** pod with **privileged** can be **created**; **central** enforcement.

---

## Q16. (Advanced) How do you implement "no root" and "read-only filesystem" for containers at scale (enforcement)?

**Answer:**  
(1) **Pod Security** (K8s 1.23+): **standards** (restricted, baseline); **enforce** or **audit** in **namespace**. (2) **OPA/Gatekeeper**: **policy** — deny if **runAsNonRoot** not true or **readOnlyRootFilesystem** not true. (3) **Image** build: **USER** non-root; **Dockerfile** lint in CI. (4) **Scan**: **Trivy** etc. can **report** run-as-root. **Enforce** at **admission** so **no** one can run root/read-write by default.

---

## Q17. (Advanced) What is secrets rotation? How do you rotate a DB password used by 10 pods without downtime?

**Answer:**  
**Rotation**: **change** secret **periodically** (e.g. 90 days). **Zero-downtime**: (1) **Add** new secret (e.g. **new** password in **Vault** or K8s Secret **v2**). (2) **Dual-write** or **support both** old and new in DB. (3) **Roll** pods (restart with **new** secret); they use **new** password. (4) **Decommission** old password in DB. **K8s**: **update** Secret; **rolling** restart (e.g. **kubectl rollout restart**) so pods **remount** new secret. **App** must **re-read** secret on startup (or use **reload** from vault).

---

## Q18. (Advanced) Production scenario: A developer commits an AWS key to a public repo. The key is already in history. What steps do you take?

**Answer:**  
(1) **Revoke** key **immediately** in AWS (IAM). (2) **Rotate** — create **new** key if still needed; update **all** uses. (3) **Remove** from **history**: **BFG** or **git filter-repo**; **force-push**; **notify** team to **re-clone**. (4) **Scan** for **other** leaks (TruffleHog, git-secrets). (5) **Prevent**: **pre-commit** hook; **secret** scan in **CI**; **block** push if detected. (6) **Audit** what the key could access; **review** logs for **abuse**.

---

## Q19. (Advanced) What is a zero-trust network model? How does it differ from "trust internal network"?

**Answer:**  
**Zero-trust**: **never** trust by **location**; **verify** every **request** (identity, device, context). **Internal** = still **auth** and **authorize**. **Traditional**: **inside** VPN/firewall = trusted. **Zero-trust**: **mTLS**, **auth** per service, **micro-segmentation** (e.g. **NetworkPolicy**), **least** privilege. **DevOps**: **service** identity (certs, JWT); **deny** by default; **encrypt** in transit.

---

## Q20. (Advanced) Senior red flags to avoid in security (DevOps)

**Answer:**  
- **Secrets** in code, config, or **logs**.  
- **No** image or **dependency** scan in CI.  
- **Containers** running as **root** or **privileged**.  
- **Overly broad** RBAC or **security groups**.  
- **No** **TLS** or **weak** TLS in production.  
- **Ignoring** CVEs ("we'll fix later").  
- **No** **audit** or **access** review.  
- **Default** allow **network** (no deny-default).

---

**Tradeoffs:** Startup: secrets in vault, basic scan. Medium: SAST/DAST, image scan, RBAC. Enterprise: policy as code, SBOM, zero-trust, rotation.
