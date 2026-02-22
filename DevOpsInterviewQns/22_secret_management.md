# 22. Secret Management

## Q1. (Beginner) What is secret management? Why not store secrets in code or config files?

**Answer:**  
**Secret** **management**: **store** and **deliver** **secrets** (passwords, **API** **keys**, **certs**) **securely**; **access** **control** and **audit**. **Don’t** in **code**/config: **repo** **leak** (Git **history**); **no** **rotation**; **same** **secret** **everywhere**. **Use** **dedicated** **store** (Vault, **cloud** **secrets** **manager**).

---

## Q2. (Beginner) What is HashiCorp Vault? What is the main use case?

**Answer:**  
**Vault**: **store** **secrets**; **dynamic** **secrets** (e.g. **DB** **credentials** **on demand**); **encryption** **as** **service**; **PKI**. **Use**: **central** **secrets** for **apps** and **infra**; **short-lived** **DB** **creds**; **encryption** **keys**. **Access**: **auth** (AppRole, **K8s** **auth**) then **read** **secret** via **API**.

---

## Q3. (Beginner) What is AWS Secrets Manager vs Parameter Store? When use which?

**Answer:**  
**Secrets** **Manager**: **secrets** (passwords, **API** **keys**); **rotation** **built-in** (e.g. **RDS**); **pay** per **secret**. **Parameter** **Store**: **config** and **secrets**; **Standard** (free) and **Advanced** (KMS); **hierarchical**. **Use** **Secrets** **Manager** for **rotation** and **sensitive** **values**; **Parameter** **Store** for **config** and **cheap** **secrets** (Standard). **Both** **integrate** with **IAM** and **KMS**.

---

## Q4. (Beginner) How do you inject a secret into a Kubernetes pod at runtime?

**Answer:**  
**K8s** **Secret** **resource**; **mount** as **file** ( **volume** + **volumeMounts**) or **env** ( **env** **valueFrom** **secretKeyRef**). **Create** **Secret** from **CI** or **operator** (e.g. **External** **Secrets** **Operator** **syncs** from **Vault**/AWS to **K8s** **Secret**). **Pod** **references** **Secret** by **name**; **kubelet** **injects** **value** at **start**. **Never** **commit** **Secret** **YAML** with **real** **data**; **use** **external** **source**.

---

## Q5. (Intermediate) How do you securely handle API keys in a containerized environment? Compare Vault vs AWS Secrets Manager.

**Answer:**  
**Vault**: **on-prem** or **self-hosted**; **dynamic** **secrets**; **many** **backends** (DB, **AWS**, **PKI**); **K8s** **auth** (pod **gets** **token**; **reads** **secret**). **AWS** **Secrets** **Manager**: **managed**; **rotation**; **native** **IAM**; **no** **ops** **overhead**. **Container**: **app** **calls** **Vault** or **AWS** **API** at **start** (or **sidecar** **injects** **env**); **or** **External** **Secrets** **syncs** to **K8s** **Secret**; **pod** **uses** **env**/file. **Choice**: **AWS**-only and **want** **managed** → **Secrets** **Manager**; **multi-cloud** or **dynamic** **secrets** → **Vault**.

---

## Q6. (Intermediate) What is the Kubernetes External Secrets Operator? How does it work?

**Answer:**  
**ESO**: **syncs** **secrets** from **external** **store** (Vault, **AWS**, **GCP**, **Azure**) into **K8s** **Secrets**. **User** **creates** **ExternalSecret** **CR** ( **secretStore** ref, **target** **K8s** **Secret**, **data** **mapping**). **Operator** **fetches** from **store** (using **ClusterSecretStore** **credentials**) and **creates**/updates **Secret**. **Pods** **use** **Secret** as **usual**. **Refresh** **interval** or **on** **change** (if **supported**). **Result**: **no** **secret** in **Git**; **rotation** in **store** → **sync** to **K8s**.

---

## Q7. (Intermediate) What is secret rotation? Why is it important?

**Answer:**  
**Rotation**: **periodically** **change** **secrets** (e.g. **DB** **password**); **issue** **new** **cred**; **update** **consumers**; **revoke** **old**. **Important**: **limit** **blast** **radius** of **leak**; **compliance** (e.g. **90** days). **Implement**: **Vault** **dynamic** **secrets** (short-lived; **no** **manual** **rotation**); **AWS** **Secrets** **Manager** **rotation** **lambda** (e.g. **RDS**); **or** **custom** **job** that **updates** **secret** and **restarts** **apps** (or **reload**).

---

## Q8. (Intermediate) How do you give a Jenkins pipeline access to secrets (e.g. deploy key) without exposing in logs?

**Answer:**  
**Store** in **Jenkins** **Credentials** (or **Vault**); **reference** by **id** in **pipeline** (e.g. **credentials('my-deploy-key')**); **never** **echo** or **print**. **File** **binding**: **write** to **temp** **file**; **use**; **delete** in **post** **cleanup**. **Env** **var**: **withCredentials([sshUserPrivateKey(...)]) { ... }** — **masked** in **logs**. **Vault**: **Jenkins** **plugin** or **script** that **fetches** and **sets** **env** **inside** **withCredentials**; **no** **plain** **text** in **config** **file**.

---

## Q9. (Intermediate) What is the risk of secrets in environment variables? How do you reduce it?

**Answer:**  
**Risk**: **env** **visible** in **proc** (e.g. **/proc/pid/environ**); **child** **processes** **inherit**; **logs**/dumps may **leak**. **Reduce**: **mount** as **file** (e.g. **K8s** **Secret** **volume**); **read** in **app**; **file** **permissions** **restrict**; **or** **fetch** at **runtime** from **Vault** (no **long-lived** **env**). **Still** **use** **env** when **convenient** but **restrict** **access** to **pod**; **never** **log** **env**.

---

## Q10. (Intermediate) How do you bootstrap Vault in Kubernetes (initial unseal, auth)?

**Answer:**  
**Deploy** **Vault** (StatefulSet or **Helm**); **init** → **unseal** **keys** and **root** **token** ( **store** **securely**; **root** only for **bootstrap**). **Configure** **K8s** **auth** **method**: **enable** **auth**; **create** **role** ( **service_account** **bound** to **namespace**/name); **policy** for **secret** **paths**. **App** **pods**: **ServiceAccount** **token**; **auth** to **Vault**; **get** **secret**; **start** **app**. **Auto-unseal**: **KMS** or **Cloud** **KMS** so **restart** doesn’t **need** **manual** **unseal**.

---

## Q11. (Advanced) Production scenario: How do you securely handle DB credentials for 50 microservices? Prefer dynamic secrets and rotation.

**Answer:**  
**Vault** **database** **backend**: **dynamic** **creds** ( **CREATE** **USER** per **lease**); **each** **service** **gets** **unique** **short-lived** **cred** (e.g. **1h**). **App** **auth** (e.g. **K8s** **auth**) → **read** **db/creds/myrole** → **get** **username**/password → **connect** to **DB**. **Rotation**: **Vault** **rotates** **root** **cred** ( **config** **connection** **url**); **dynamic** **creds** **unchanged** (new **lease** = new **cred**). **50** **services** = **50** **leases**; **no** **shared** **password**; **revoke** **per** **service** if **compromised**. **Alternative**: **AWS** **Secrets** **Manager** + **rotation** **lambda**; **sync** to **K8s** via **ESO** ( **one** **secret** per **service** or **shared** **secret** with **rotation**).

---

## Q12. (Advanced) How do you integrate security (secrets) earlier in CI without slowing builds?

**Answer:**  
(1) **Fetch** **secrets** in **CI** from **Vault**/cloud ( **cached** or **short** **step**); **never** **store** in **repo**. (2) **Scan** **code** for **secret** **patterns** ( **gitleaks**, **truffleHog**) in **PR** — **fast**; **fail** if **found**. (3) **Build** **secrets** (e.g. **npm** **token**): **BuildKit** **--secret** or **CI** **secret** **env**; **no** **bake** into **image**. (4) **Image** **scan** ( **Trivy**) in **parallel** with **test**; **don’t** **block** **critical** **path** unless **critical** **CVE**. (5) **Policy** ( **OPA**) **evaluate** **config** (e.g. **no** **secret** in **env** **from** **literal**). **Result**: **shift-left** with **minimal** **latency** (parallel **steps**, **small** **overhead**).

---

## Q13. (Advanced) What is Vault Agent injector (Kubernetes)? How does it inject secrets without app code change?

**Answer:**  
**Vault** **Agent** **Injector**: **mutating** **webhook**; **pod** **annotation** (e.g. **vault.hashicorp.com/agent-inject**) **triggers** **inject** of **init** and **sidecar** **containers**. **Init** **container**: **Vault** **agent** **auth** (e.g. **K8s** **auth**) and **template** **secrets** to **shared** **volume** ( **file**). **App** **container** **reads** **file** (or **env** from **template**). **No** **app** **code** **change** if **app** **reads** **file** or **env** ( **convention**). **Sidecar** **keeps** **lease** **renewed** and **can** **re-template** on **renewal**.

---

## Q14. (Advanced) Production scenario: A secret was leaked (e.g. in a public PR). What steps do you take?

**Answer:**  
(1) **Revoke** **secret** **immediately** (rotate **password**/key in **Vault** or **cloud**). (2) **Identify** **scope**: **which** **repos**/commits; **Git** **history** ( **rewrite** **history** to **remove** if **allowed** — **force** **push**; **notify** **users**). (3) **Notify** **affected** **parties** ( **internal**; **customers** if **customer** **data**). (4) **Audit**: **who** **accessed** **secret** (Vault **audit** **log**; **cloud** **trail**). (5) **Fix** **process**: **pre-commit** **hook** or **CI** **scan** ( **gitleaks**); **no** **secret** in **repo**; **use** **external** **store**. (6) **Compliance**: **incident** **report** if **required**.

---

## Q15. (Advanced) How do you manage secrets for multiple environments (dev, staging, prod) without mixing?

**Answer:**  
**Separate** **secret** **paths** or **stores** per **env**: **Vault** **path** **secret/dev/** vs **secret/prod/**; **AWS** **Secrets** **Manager** **prefix** or **separate** **accounts**. **Access** **control**: **dev** **role** can’t **read** **prod**; **IAM**/Vault **policy** per **env**. **CI**: **pipeline** **per** **branch**/env **fetches** from **that** **env** **path**; **K8s** **ExternalSecret** **secretStore** **per** **namespace** (e.g. **prod** **namespace** → **prod** **store**). **No** **copy** **prod** **secret** to **dev**; **separate** **values** per **env**.

---

## Q16. (Advanced) What is encryption at rest for secrets? How does Vault or AWS KMS help?

**Answer:**  
**At rest**: **secrets** **encrypted** in **storage** ( **key** in **KMS**). **Vault**: **barrier** **encryption** ( **master** **key**); **auto-unseal** with **KMS** so **Vault** **key** **encrypted** by **KMS**. **AWS** **Secrets** **Manager**: **each** **secret** **encrypted** with **KMS** **key**; **IAM** **controls** **decrypt**. **Help**: **leak** of **disk** doesn’t **expose** **plain** **text**; **access** **control** via **KMS** **policy** and **audit** ( **CloudTrail**).

---

## Q17. (Advanced) How do you audit secret access (who read what, when)?

**Answer:**  
**Vault**: **audit** **log** ( **file** or **syslog**); **every** **read** **logged** ( **path**, **client** **token**/identity). **AWS**: **CloudTrail** for **Secrets** **Manager** **API** **calls** ( **GetSecretValue**). **K8s**: **audit** **log** ( **get** **secret**); **RBAC** **audit**. **Correlate**: **token** → **service** **account** → **app**; **alert** on **unusual** **access** (e.g. **prod** **secret** from **dev** **namespace**).

---

## Q18. (Advanced) How do you avoid secrets in Terraform state while provisioning resources that need a password?

**Answer:**  
(1) **Variable** **sensitive** = true; **don’t** **commit** **tfvars** with **value**; **env** **TF_VAR_xxx** or **Vault** **data** **source**. (2) **Resource** **that** **accepts** **password**: **reference** **variable**; **never** **hardcode**. (3) **State**: **remote** **backend** with **encryption**; **restrict** **access**; **consider** **null** **resource** + **local-exec** to **set** **secret** **outside** **Terraform** (e.g. **Vault** **write**) so **Terraform** **state** doesn’t **hold** **password**. (4) **Dynamic** **secret** from **Vault** ( **database** **backend**) so **Terraform** **only** **stores** **reference**; **actual** **password** **generated** at **read** **time**.

---

## Q19. (Advanced) Production scenario: Migrate 20 apps from config-file secrets to Vault without downtime.

**Answer:**  
(1) **Deploy** **Vault** and **populate** **secrets** (same **values** as **current**). (2) **Dual-read**: **app** **code** **change** to **read** from **Vault** **first**; **fallback** to **env**/file if **Vault** **unavailable** (or **inject** via **sidecar** so **no** **code** **change**). (3) **Roll** **out** **per** **service** ( **canary**); **validate** **Vault** **path** and **auth**. (4) **Remove** **fallback** and **old** **config** after **all** **migrated**. (5) **Rotate** **secrets** in **Vault** ( **new** **values**); **old** **config** **no** **longer** **valid**. **No** **downtime** if **dual-read** and **same** **values** during **cutover**.

---

## Q20. (Advanced) Senior red flags to avoid with secrets

**Answer:**  
- **Secrets** in **code** or **config** in **repo** (even **encrypted** if **policy** says **no**).  
- **No** **rotation** ( **long-lived** **creds**).  
- **Shared** **root**/admin **password** across **all** **services**.  
- **Logging** or **echoing** **secrets** ( **mask** in **CI**).  
- **Secrets** in **Terraform** **state** without **restriction** ( **sensitive** **var** + **remote** **backend** **encryption**).  
- **No** **audit** (can’t **tell** **who** **read** **what**).  
- **Prod** **secret** **in** **dev** **store** or **env** ( **mix** **envs**).  
- **No** **scan** in **CI** for **leaked** **secrets**.

---

**Tradeoffs:** Startup: cloud secrets or single Vault, env/file injection. Medium: ESO, rotation, separate env paths. Enterprise: Vault dynamic secrets, audit, K8s auth, shift-left scan.
