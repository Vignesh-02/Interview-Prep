# 24. Compliance as Code (OPA, Policy)

## Q1. (Beginner) What is "policy as code" or "compliance as code"?

**Answer:**  
**Policy** **as** **code**: **rules** that **govern** **infra** and **apps** are **defined** in **code** ( **versioned**, **reviewed**, **automated**). **Compliance** **as** **code**: **compliance** **requirements** (e.g. " **no** **public** **S3**") **expressed** as **rules** and **checked** **automatically**. **Benefits**: **consistent** **enforcement**; **audit** **trail**; **no** **manual** **checklists**.

---

## Q2. (Beginner) What is OPA (Open Policy Agent)? What is it used for?

**Answer:**  
**OPA**: **general** **policy** **engine**; **input** (JSON) → **policy** ( **Rego** **language**) → **output** (allow/deny or **data**). **Used** for: **K8s** **admission** ( **validating** **webhook**); **Terraform** **plan** **review**; **API** **authz**; **CI** **policies**. **Decouple** **policy** from **app** **code**; **single** **language** for **many** **use** **cases**.

---

## Q3. (Beginner) What is Rego? Give a simple example (e.g. allow if role is admin).

**Answer:**  
**Rego**: **declarative** **language** for **OPA** **policies**. **Example**:
```rego
package authz
default allow = false
allow if {
  input.role == "admin"
}
allow if {
  input.role == "user" and input.action == "read"
}
```
**Input** = **request** (user, **action**, **resource**); **allow** = **true** if **conditions** **met**.

---

## Q4. (Beginner) What is a Kubernetes admission controller? How does it relate to policy?

**Answer:**  
**Admission** **controller**: **intercepts** **request** to **API** **server** ( **create**/update **resource**); **can** **mutate** or **validate**; **allow** or **deny**. **Policy**: **OPA** **Gatekeeper** (or **plain** **OPA** **webhook**) **evaluates** **incoming** **resource** against **policy** (e.g. " **no** **privileged** **pod**"); **deny** if **violation**. **Result**: **non-compliant** **resources** **never** **created**.

---

## Q5. (Intermediate) Write an OPA/Rego rule that denies a Kubernetes pod if it has hostNetwork: true.

**Answer:**
```rego
package kubernetes.admission
deny[msg] {
  input.request.kind.kind == "Pod"
  input.request.object.spec.hostNetwork == true
  msg := "Pods must not use hostNetwork"
}
```
**Gatekeeper** **ConstraintTemplate** **uses** **Rego**; **Constraint** **binds** **template** to **scope** (e.g. **all** **namespaces**). **Admission** **webhook** **calls** **OPA** with **request**; **deny** **response** if **deny** **set** **non-empty**.

---

## Q6. (Intermediate) How do you use OPA to ensure Terraform plan has no public S3 buckets?

**Answer:**  
**Export** **plan** as **JSON**: `terraform show -json plan.tfplan > plan.json`. **OPA** **input** = **plan** **JSON**; **policy** **traverses** **resource_changes** for **aws_s3_bucket** and **aws_s3_bucket_public_access_block**; **deny** if **bucket** **has** **no** **public_access_block** or **block_public_acls** = **false**. **CI**: **terraform plan** → **conftest** ( **OPA** **for** **config**) **test** **plan.json**; **fail** **pipeline** if **violations**. **Rego** **example**: **deny** if **resource** is **aws_s3_bucket** and **no** **matching** **block** **config**.

---

## Q7. (Intermediate) What is Gatekeeper? How does it relate to OPA?

**Answer:**  
**Gatekeeper**: **K8s** **admission** **controller** that **uses** **OPA**; **CRDs** **ConstraintTemplate** ( **Rego** **code**) and **Constraint** ( **instance** with **params**). **API** **server** **sends** **admission** **review** to **Gatekeeper**; **Gatekeeper** **evaluates** **Rego**; **allows** or **denies** **request**. **OPA** = **engine**; **Gatekeeper** = **K8s** **integration** + **audit** ( **reports** **existing** **violations**).

---

## Q8. (Intermediate) How do you test OPA policies (unit test style)?

**Answer:**  
**OPA** **test** **command**: **rego** **files** with **test** **prefix** (e.g. **test_allow**); **run** `opa test .`. **Tests** **define** **input** and **assert** **output** (e.g. **allow** = **true**). **Conftest** **test** for **config** **files** ( **yaml**, **tf**). **CI**: **run** **opa test** in **pipeline**; **policy** **changes** **require** **tests**. **Result**: **safe** **refactor** and **documentation** of **expected** **behavior**.

---

## Q9. (Intermediate) What is a ConstraintTemplate vs Constraint in Gatekeeper?

**Answer:**  
**ConstraintTemplate**: **reusable** **template**; **contains** **Rego** and **schema** for **params** (e.g. " **require** **labels**" with **param** **list** of **required** **labels**). **Constraint**: **instance** of **template** (e.g. " **require** **labels** **app** and **env**" for **namespace** **prod**). **One** **template** → **many** **constraints** ( **different** **params** or **scopes**).

---

## Q10. (Intermediate) How do you enforce "all images must come from approved registry" in Kubernetes?

**Answer:**  
**Gatekeeper** **ConstraintTemplate**: **Rego** **checks** **containers**[].**image**; **deny** if **image** **does** **not** **start** with **allowed** **registry** **prefix** (e.g. **myregistry.io/**). **Constraint** **params**: **allowedPrefixes**: ["myregistry.io/"]. **Admission** **denies** **pod**/Deployment **create** if **image** **from** **other** **registry**. **Alternative**: **OPA** **without** **Gatekeeper** ( **validating** **webhook** that **calls** **OPA**).

---

## Q11. (Advanced) Production scenario: You need to ensure all Terraform changes comply with "no instance without encryption at rest" and "no public RDS". How do you implement it?

**Answer:**  
**Policy** **as** **code**: **Rego** ( **conftest** or **OPA**) that **reads** **terraform** **plan** **JSON**. **Rules**: (1) **resource** **aws_instance** or **aws_ebs_*** → **check** **ebs** **block** has **encrypted** = **true** (or **default** **encryption**); **deny** if **not**. (2) **resource** **aws_db_instance** → **check** **publicly_accessible** = **false**; **deny** if **true**. **CI**: **terraform plan -out=tfplan**; **terraform show -json tfplan > plan.json**; **conftest test plan.json -p policy/**; **fail** if **violations**. **Result**: **non-compliant** **plans** **never** **applied**.

---

## Q12. (Advanced) How do you audit existing Kubernetes resources for policy violations (not just admission)?

**Answer:**  
**Gatekeeper** **audit**: **periodically** **scans** **existing** **resources** ( **inventory** from **API** **server**); **evaluates** **same** **Rego**; **reports** **violations** in **Constraint **status** ( **violations** **list**). **Dashboard** or **controller** **that** **reports** **violations** (e.g. **Slack**). **Remediation**: **manual** **fix** or **automated** (e.g. **Kyverno** **mutate** or **job** that **patches** **resources**). **Result**: **visibility** into **drift** from **policy**.

---

## Q13. (Advanced) What is the difference between OPA and Kyverno? When would you choose one?

**Answer:**  
**OPA**/**Gatekeeper**: **generic** **policy** **engine**; **Rego**; **any** **input** (K8s, **Terraform**, **API**). **Kyverno**: **K8s**-native; **policies** in **YAML** ( **match** **resources**, **validate**/mutate **rules**); **no** **Rego**. **Choose** **Kyverno**: **simpler** for **K8s**-only; **easier** for **teams** **without** **Rego**. **Choose** **OPA**/**Gatekeeper**: **same** **engine** for **K8s** + **Terraform** + **API**; **complex** **logic** in **Rego**; **already** **using** **OPA** **elsewhere**.

---

## Q14. (Advanced) How do you implement "compliance as code" for PCI or SOC2 (e.g. encryption, access control)?

**Answer:**  
**Map** **controls** to **automated** **checks**: (1) **Encryption**: **OPA** **policy** ( **Terraform** **plan** + **K8s**) — **no** **unencrypted** **storage**; **TLS** **only**. (2) **Access** **control**: **RBAC** **policies** in **code**; **OPA** **audit** that **no** **overly** **broad** **bindings**. (3) **Secrets**: **policy** **no** **secrets** in **config**; **scan** in **CI**. **Run** **policies** in **CI** ( **plan** **review**) and **admission** ( **K8s**); **audit** **report** **periodically** ( **Gatekeeper** **violations** → **compliance** **dashboard**). **Document** **control** ↔ **policy** **mapping** for **auditors**.

---

## Q15. (Advanced) Production scenario: A developer deploys a Deployment with runAsRoot. Policy says no root. How does the request get blocked and what do they see?

**Answer:**  
**Gatekeeper** (or **OPA** **webhook**) **evaluates** **admission** **request**; **Rego** **checks** **spec.securityContext.runAsNonRoot** or **container** **securityContext**; **deny** if **runAsUser** = **0** or **runAsNonRoot** **false**/missing. **API** **server** **returns** **403** **Forbidden** to **client** ( **kubectl**); **message** from **policy** (e.g. " **Pods** **must** **not** **run** as **root**"). **Developer** **sees** **error**; **fixes** **manifest** ( **runAsNonRoot**: **true**, **runAsUser** **non-zero**) and **retries**. **Audit** **log** **records** **denied** **request**.

---

## Q16. (Advanced) How do you version and roll out policy changes (e.g. new rule) without breaking existing workloads?

**Answer:**  
(1) **Policy** in **Git**; **version** with **tag** or **branch**. (2) **Dry-run** or **audit** **mode** **first**: **Gatekeeper** **constraint** **enforcementAction**: **dryrun** ( **report** **violations** but **don’t** **deny**); **fix** **violations**; **switch** to **deny**. (3) **Rollout**: **deploy** **new** **ConstraintTemplate**; **create** **Constraint** with **dryrun**; **remediate**; **change** to **deny**. (4) **Exemptions** ( **namespaces** or **labels**) for **legacy** **during** **migration**; **remove** **exemptions** when **compliant**.

---

## Q17. (Advanced) How do you write a policy that allows a specific namespace to bypass a rule (exception)?

**Answer:**  
**Rego**: **deny** only if **resource** **violates** **and** **namespace** **not** in **exemption** **list**. **Example**:
```rego
deny[msg] {
  input.request.object.metadata.namespace != "exempt-namespace"
  input.request.object.spec.hostNetwork == true
  msg := "hostNetwork not allowed"
}
```
**Constraint** **params**: **exemptNamespaces**: ["exempt-namespace"]. **Or** **Gatekeeper** **Constraint** **match** **exclude** **namespaces** (if **supported**). **Document** **exemptions** and **review** **periodically**.

---

## Q18. (Advanced) How do you integrate OPA with Terraform Cloud or CI (plan review)?

**Answer:**  
**CI**: **terraform plan -out=tfplan**; **terraform show -json tfplan | conftest test -p policy/ -**. **Terraform** **Cloud**: **sentinel** ( **native** **policy** **language**) or **external** **CI** that **fetches** **plan** and **runs** **conftest**/OPA. **Policy** **repo** or **bundled** with **repo**; **CI** **fails** if **conftest** **exit** **code** **non-zero**. **Result**: **no** **apply** of **non-compliant** **plan**.

---

## Q19. (Advanced) What is policy testing and how do you avoid regressions when updating policies?

**Answer:**  
**Policy** **testing**: **unit** **tests** for **Rego** ( **opa test**); **test** **cases** with **input** (e.g. **allowed** **request**, **denied** **request**); **assert** **allow**/deny **output**. **Regression**: **add** **test** for **every** **bug** **fix** ( **violation** that **was** **allowed**); **test** **must** **deny** **now**. **CI**: **opa test** on **every** **commit**; **no** **merge** if **tests** **fail**. **Version** **tests** with **policy**; **document** **expected** **behavior**.

---

## Q20. (Advanced) Senior red flags to avoid with compliance as code

**Answer:**  
- **No** **tests** for **policies** ( **regressions**; **unclear** **behavior**).  
- **Deny** **everything** by default with **no** **exemption** **process** ( **block** **legit** **work**).  
- **Policy** **only** at **admission** ( **no** **audit** of **existing** **resources**).  
- **Overly** **broad** **exemptions** ( **whole** **namespace** **bypass**).  
- **Policy** **not** **versioned** or **reviewed** ( **no** **Git** **workflow**).  
- **No** **dry-run** before **enforce** ( **break** **deploys**).  
- **Policy** and **docs** **out** of **sync** ( **auditors** **confused**).  
- **Only** **K8s** ( **ignore** **Terraform**/API **policy**).

---

**Tradeoffs:** Startup: manual checklist, basic K8s PSA. Medium: Gatekeeper or Kyverno for K8s, conftest for Terraform. Enterprise: OPA across K8s + Terraform + API, audit, exemptions process, compliance mapping.
