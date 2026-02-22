# 27. Environment Parity & Staging vs Prod

## Q1. (Beginner) What is environment parity? Why does it matter?

**Answer:**  
**Parity**: **staging**/dev **resemble** **prod** ( **config**, **infra**, **data** **shape**, **dependencies**). **Matters**: **bugs** that **only** **appear** in **prod** (" **works** on **my** **machine**") **often** due to **differences** ( **scale**, **config**, **versions**). **Closer** **parity** = **fewer** **prod** **surprises**. **Tradeoff**: **cost** and **complexity** ( **full** **prod** **clone** **expensive**); **aim** for **high** **parity** on **critical** **paths**.

---

## Q2. (Beginner) What are common causes of "works in staging, fails in prod"?

**Answer:**  
**Config** **diff**: **env** **vars**, **feature** **flags**, **URLs** ( **prod** **endpoints** **different**). **Infra** **diff**: **smaller** **staging** ( **fewer** **replicas**, **different** **node** **size**); **network** **policy**; **missing** **prod** **dependency** ( **queue**, **DB** **version**). **Data** **diff**: **empty** or **small** **DB** in **staging**; **prod** **data** **shape**/volume **different**. **Secrets**/ **permissions**: **staging** **has** **test** **creds**; **prod** **permissions** **stricter**. **Timing**/ **scale**: **race** **conditions** under **load** only in **prod**.

---

## Q3. (Beginner) What is a systematic approach to debug "works in staging, fails in prod"?

**Answer:**  
(1) **Reproduce** **in** **staging**: **same** **request**/ **payload**; **same** **config** ( **copy** **prod** **config** where **safe**). (2) **Compare** **config**: **diff** **env** **vars**, **feature** **flags**, **versions** ( **app**, **DB**, **libs**). (3) **Compare** **infra**: **replicas**, **resources**, **network**; **prod**-like **staging** **test** ( **scale** **up**). (4) **Logs**/traces: **same** **path** in **staging** vs **prod**; **where** **behavior** **diverges**. (5) **Canary** or **feature** **flag** in **prod** to **narrow** **scope** ( **which** **region**/ **user**). (6) **Check** **data**: **anonymized** **prod** **copy** in **staging** if **possible**.

---

## Q4. (Beginner) What is config drift between environments? How do you detect it?

**Answer:**  
**Config** **drift**: **staging** and **prod** **config** ( **env** **vars**, **K8s** **ConfigMaps**, **feature** **flags**) **diverge** over **time**. **Detect**: **config** **in** **code** ( **Git**); **diff** **between** **env** **dirs** (e.g. **staging** **vs** **prod** **overlays**). **Tool**: **script** that **exports** **config** from **each** **env** and **diffs**; **dashboard** of **known** **differences** ( **documented** **intentional** **diff**). **CI** **check**: **deploy** **config** **must** **pass** **schema**/ **lint**; **alert** if **prod** **config** **changed** **outside** **Git**.

---

## Q5. (Intermediate) How do you make staging more like prod without cloning full prod (cost)?

**Answer:**  
**Infra** **parity**: **same** **K8s** **version**, **same** **node** **image**; **same** **replica** **count** (or **scaled** **down** but **same** **topology**); **same** **ingress**/ **LB** **type**. **Config** **parity**: **same** **env** **var** **names** ( **values** **different** — **staging** **URLs**, **test** **secrets**); **same** **feature** **flags** ( **default** **off** in **staging**). **Data**: **anonymized** **prod** **snapshot** or **synthetic** **data** with **prod** **shape**; **DB** **version** **match**. **Skip**: **full** **prod** **scale** ( **smaller** **nodes**/replicas); **expensive** **external** **deps** ( **mock** or **stub**). **Document** **known** **differences** and **accept** **risk** for **low** **impact** **areas**.

---

## Q6. (Intermediate) What is the role of feature flags in environment parity?

**Answer:**  
**Feature** **flags**: **toggle** **features** by **env**, **user**, **percentage**. **Parity**: **same** **flag** **names** and **config** **structure** in **all** **envs**; **values** **differ** ( **staging** = **on** for **testing**, **prod** = **gradual** **rollout**). **Avoid** **code** **paths** that **only** **exist** in **prod** ( **flag** **missing** in **staging** = **bug**). **Test** **both** **states** ( **on**/ **off**) in **staging**; **prod** **behavior** **predictable** from **staging** **tests**.

---

## Q7. (Intermediate) How do you use infrastructure as code to maintain parity?

**Answer:**  
**Same** **IaC** ( **Terraform** **modules**, **K8s** **base** **manifests**) for **all** **envs**; **only** **inputs** **differ** ( **env** **name**, **size**, **replica** **count**). **Example**: **one** **module** " **app**"; **staging** **tfvars** ( **replicas** = 2), **prod** **tfvars** ( **replicas** = 10). **Result**: **infra** **shape** **same**; **drift** **reduced** ( **change** **once**, **apply** **everywhere**). **Config** **management** ( **K8s** **overlays**, **Helm** **values** per **env**) **same** **structure**; **values** **env-specific**.

---

## Q8. (Intermediate) What is blue-green or canary for reducing prod-only failures?

**Answer:**  
**Gradual** **exposure**: **new** **version** to **small** **traffic** ( **canary**) or **parallel** **env** ( **blue-green**); **observe** **metrics** before **full** **cutover**. **Reduces** **prod-only** **failures**: **real** **prod** **traffic** and **config** **exercised** on **new** **version**; **rollback** if **errors** **spike** ( **no** **full** **blast**). **Complements** **staging** ( **staging** = **pre**-prod **validation**; **canary** = **prod** **validation** with **real** **load** and **data**).

---

## Q9. (Intermediate) How do you document and review intentional differences between staging and prod?

**Answer:**  
**Doc**: **single** **doc** or **README** (e.g. **env-differences.md**) listing **intentional** **diffs**: **replica** **count**, **DB** **size**, **feature** **flags** **default**, **external** **API** ( **mock** vs **real**), **retention** **period**. **Review**: **on** **change** ( **PR** that **adds** **diff** **must** **update** **doc** and **justify**); **periodic** **audit** ( **quarterly** — **are** **diffs** **still** **needed**?). **Result**: **onboarding** and **debugging** know **what** **to** **expect**; **unintended** **drift** **easier** to **spot**.

---

## Q10. (Intermediate) What is production-like data in staging? How do you get it without exposing PII?

**Answer:**  
**Production-like**: **volume**, **shape**, **relationships** **similar** to **prod** ( **so** **queries**, **indexes**, **edge** **cases** **appear**). **Get** **it**: **anonymized** **dump** ( **replace** **PII** with **fake** **data**); **subset** ( **sample** **10%**); **synthetic** **data** **generator** that **matches** **schema** and **distributions**. **PII**: **never** **copy** **raw** **prod** **PII**; **hash**/ **mask**/ **replace**; **compliance** **review** ( **GDPR**, **internal** **policy**). **Refresh** **periodically** so **staging** **doesn’t** **stale**.

---

## Q11. (Advanced) Production scenario: Code works in staging but fails in prod. Describe your systematic approach to find the discrepancy.

**Answer:**  
(1) **Reproduce**: **exact** **request**/ **payload** from **prod** ( **logs**/traces); **replay** in **staging** ( **same** **headers**, **body**). **If** **staging** **passes**, **diff** **envs**. (2) **Config** **diff**: **export** **env** **vars** and **ConfigMaps** from **staging** and **prod**; **diff** ( **ignore** **secrets** **values**; **compare** **keys** and **structure**). (3) **Infra** **diff**: **K8s** **manifests** ( **resources**, **replicas**); **DB** **version**; **network** **policy**. (4) **Data**: **same** **input** **data** in **staging**? **Prod** **edge** **case** ( **null**, **large** **payload**)? (5) **Observability**: **trace** **same** **request** in **both**; **where** **code** **path** **diverges** ( **log** **line**, **branch**). (6) **Temporary** **prod** **logging**: **add** **debug** **log** ( **feature** **flag**); **deploy** **canary**; **repro** and **inspect**. (7) **Fix** and **add** **test** ( **integration** or **e2e**) that **would** **catch** **this** in **staging** ( **prod**-like **config** or **data**).

---

## Q12. (Advanced) How do you test database migrations in a way that matches prod?

**Answer:**  
**Staging** **DB**: **same** **engine** and **version** as **prod**; **migration** **run** in **CI** against **staging** **DB** ( **or** **copy** of **prod** **schema** + **anonymized** **data**). **Test**: **migration** **up** and **down**; **application** **smoke** **test** **after** **migration**; **large** **table** **behavior** ( **lock** **time**, **timeout**) if **possible** with **prod**-sized **data**. **Prod** **migration**: **backup** **first**; **run** in **maintenance** **window** if **breaking**; **canary** **migration** ( **one** **replica** **first**) if **supported**. **Version** **parity**: **staging** **DB** **version** = **prod** ( **upgrade** **staging** **first**).

---

## Q13. (Advanced) What is ephemeral environment (e.g. per-PR staging)? How does it affect parity?

**Answer:**  
**Ephemeral** **env**: **short-lived** **env** per **PR** ( **namespace** or **cluster**); **destroy** after **merge**. **Parity**: **same** **base** **config** and **infra** **template** as **staging**/prod; **may** **skip** **costly** **deps** ( **shared** **staging** **DB** or **mock**). **Affect**: **good** **parity** for **app** **config** and **topology**; **weaker** **parity** for **data** and **external** **services**. **Use** for **quick** **validation**; **full** **staging** **and** **prod**-like **tests** in **shared** **staging** before **release**.

---

## Q14. (Advanced) How do you handle secrets and external service URLs across environments?

**Answer:**  
**Secrets**: **separate** **secret** **store** per **env** ( **path** or **account**); **same** **keys** (e.g. **DB_HOST**, **API_KEY**); **values** **different** ( **staging** **DB** **host**, **prod** **DB** **host**). **URLs**: **config** **per** **env** ( **env** **var** or **ConfigMap**); **app** **reads** **one** **config**; **no** **hardcode**. **External** **services**: **staging** **uses** **sandbox** **or** **mock** where **available**; **document** **which** **are** **real** in **prod** **only** ( **and** **test** **those** **paths** in **staging** with **stub** or **contract** **test**).

---

## Q15. (Advanced) Production scenario: Staging has 2 replicas, prod has 20. A bug only appears with 10+ replicas (e.g. race condition). How do you catch it before prod?

**Answer:**  
(1) **Scale** **staging** **temporarily**: **run** **load** **test** or **soak** **test** with **10+** **replicas** in **staging** ( **cost** **burst**); **repro** **race**. (2) **Integration** **test** **with** **concurrency**: **test** that **simulates** **concurrent** **requests** ( **same** **resource**); **run** in **CI** ( **may** **catch** **race** **without** **full** **scale**). (3) **Chaos**/ **stress** in **staging**: **inject** **delay** or **failure** to **expose** **timing** **bugs**. (4) **Canary** in **prod**: **deploy** to **small** **subset** (e.g. **5%** **traffic**); **monitor**; **expand** only if **stable** ( **limits** **blast** **radius** if **race** **rare**). (5) **Code** **review** and **testing** for **shared** **state**; **add** **unit** **test** with **concurrent** **goroutines**/ **threads** if **applicable**.

---

## Q16. (Advanced) How do you implement "staging is prod minus scale and secrets"?

**Answer:**  
**Same** **code** **paths** and **config** **keys**: **one** **codebase**; **config** **from** **env** ( **env** **var** **names** **same**; **values** **from** **staging** or **prod** **store**). **Same** **infra** **shape**: **same** **K8s** **manifests** ( **Helm** **values** **staging** vs **prod** only **replicas**, **resources**); **same** **DB** **engine**/ **version**; **same** **ingress**/ **service** **types**. **Scale**: **staging** **replicas** = 2; **prod** = 20 ( **same** **Deployment** **spec**). **Secrets**: **different** **values** ( **staging** **DB** **password**, **prod** **API** **key**); **same** **keys** and **injection** **method**. **Document**: " **Staging** = **prod** **with** **replicas**=2 and **staging** **secrets**; **no** **other** **intentional** **diff**."

---

## Q17. (Advanced) What is the role of contract testing (e.g. Pact) in environment parity?

**Answer:**  
**Contract** **testing**: **consumer** and **provider** **agree** on **API** **contract** ( **request**/ **response**); **test** **without** **full** **provider** **deploy**. **Parity**: **staging** **consumer** **talks** to **staging** **provider**; **contract** **ensures** **compat** so **prod** **consumer** + **prod** **provider** **behave** **same**. **Reduces** " **provider** **changed** **response**; **consumer** **breaks** in **prod**" — **catch** in **CI** when **contract** **breaks**. **Complements** **parity** ( **same** **contract** **in** **all** **envs**).

---

## Q18. (Advanced) How do you detect and alert on unintended config drift (e.g. someone changed prod config manually)?

**Answer:**  
**Config** **in** **Git**: **prod** **config** **only** **changed** via **CI** ( **GitOps** or **pipeline**); **manual** **change** = **drift**. **Detect**: **periodic** **job** that **diffs** **live** **prod** **config** ( **K8s** **ConfigMap**/ **Secret** **keys**, **env** **from** **Deployment**) vs **Git**; **alert** if **diff**. **Tool**: **custom** **script**; **Drift** **detection** ( **Terraform** **plan** for **infra**); **Argo** **CD** **diff** ( **live** vs **Git**). **Remediate**: **revert** **manual** **change** or **update** **Git** and **re-apply**; **restrict** **who** can **edit** **prod** **config** ( **RBAC**, **approval**).

---

## Q19. (Advanced) How do you run load tests in a prod-like way without affecting prod?

**Answer:**  
**Staging** **or** **dedicated** **load** **env**: **same** **topology** as **prod** ( **replicas**, **resources**); **traffic** **from** **load** **generator** ( **locust**, **k6**, **Gatling**). **Prod-like** **data**: **anonymized** **prod** **snapshot** or **synthetic** **data**; **same** **DB** **version**. **Isolate**: **no** **shared** **prod** **resources**; **separate** **cluster** or **namespace**; **mock** **external** **calls** or **use** **sandbox**. **Soak** **test** and **spike** **test** to **find** **capacity** and **race** **conditions**; **tune** **prod** **based** on **results**.

---

## Q20. (Advanced) Senior red flags to avoid with environment parity

**Answer:**  
- **No** **documented** **differences** ( **unknown** **why** **staging** ≠ **prod**).  
- **Staging** **never** **updated** ( **old** **K8s**/ **DB** **version**; **parity** **erodes**).  
- **Prod** **config** **changed** **manually** ( **no** **Git**; **drift**).  
- **Testing** **only** **happy** **path** in **staging** ( **no** **prod**-like **data**/ **load**).  
- **Feature** **flags** or **code** **paths** **only** in **prod** ( **untestable** in **staging**).  
- **No** **systematic** **diff** **process** when **debugging** " **works** in **staging**".  
- **Secrets**/ **URL** **hardcoded** ( **different** **behavior** per **env**).  
- **Ignoring** **scale** **and** **concurrency** ( **only** **catch** **in** **prod**).

---

**Tradeoffs:** Startup: minimal staging, document known diffs. Medium: IaC for infra parity, config from Git, staging scale tests. Enterprise: ephemeral envs, contract tests, drift detection, prod-like data (anonymized).
