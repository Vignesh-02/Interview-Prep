# 30. DevOps Red Flags & Best Practices (Consolidated)

## Q1. (Beginner) What is a "red flag" in DevOps context? Give two examples.

**Answer:**  
**Red** **flag**: **practice** or **pattern** that **increases** **risk** of **outage**, **security** **breach**, or **debt**. **Examples**: (1) **No** **rollback** **procedure** ( **can’t** **revert** **bad** **deploy**). (2) **Secrets** in **code** or **config** in **repo** ( **leak** **risk**). **Others**: **no** **monitoring**, **manual** **deploy**, **no** **tests** in **pipeline**, **running** as **root** in **containers**.

---

## Q2. (Beginner) Why is "it works on my machine" a DevOps red flag?

**Answer:**  
**Indicates**: **environment** **drift** ( **local**/staging ≠ **prod**); **no** **parity**; **no** **consistent** **build** ( **artifact** **not** **same** **everywhere**). **Red** **flag** because **prod** **failures** **likely**; **debugging** **wasteful**. **Fix**: **build** **once** ( **image**); **deploy** **same** **artifact**; **config** **from** **env**; **document** **and** **reduce** **differences** **between** **envs**.

---

## Q3. (Beginner) What does "cattle not pets" mean? How does it relate to red flags?

**Answer:**  
**Cattle**: **servers**/ **pods** are **disposable**; **replace** **instead** of **manual** **fix**; **automation** **and** **code** **define** **state**. **Pets**: **unique** **servers** **hand-maintained**; **SSH** **fix**; **snowflakes**. **Red** **flag**: **treating** **prod** **like** **pets** ( **manual** **changes**, **no** **automation**) → **drift**, **no** **reproducibility**, **risky** **changes**. **Aim**: **cattle** ( **IaC**, **immutable** **deploys**, **replace** **on** **failure**).

---

## Q4. (Beginner) Why is skipping tests or quality gates to "unblock" a release a red flag?

**Answer:**  
**Short-term**: **release** **goes** **out**. **Risk**: **bugs** or **vulnerabilities** **reach** **prod**; **outage** or **security** **incident**; **reputation** and **user** **impact**. **Red** **flag**: **habit** of **skipping** → **gate** **becomes** **meaningless**; **tech** **debt** **grows**. **Fix**: **fix** **flaky** **tests**; **tune** **gate** ( **meaningful** **thresholds**); **exception** **process** with **approval** and **time** **limit**; **never** **skip** **without** **record**.

---

## Q5. (Intermediate) List red flags in deployment and release management.

**Answer:**  
**No** **rollback** **procedure** or **automation**. **Deploy** **without** **approval**/ **gate** for **prod**. **Rebuilding** **per** **environment** ( **not** **build** **once**). **No** **staging** or **canary** ( **big** **bang** **prod**). **No** **post-deploy** **verification** ( **smoke** **test**). **Secrets** in **pipeline** **code** or **logs**. **No** **pipeline** **as** **code** ( **only** **UI** **config**). **No** **release** **tracking** ( **what** **version** is **in** **prod**?). **Manual** **steps** **without** **runbook**.

---

## Q6. (Intermediate) List red flags in monitoring and observability.

**Answer:**  
**No** **alerts** or **alert** **on** **everything** ( **noise**). **No** **SLO**/ **error** **budget** ( **no** **target**). **No** **runbook** for **alerts** ( **what** to **do**?). **High** **cardinality** **metrics** ( **blow-up**). **No** **logs**/ **traces** **correlation** ( **hard** **debug**). **Short** **retention** **no** **archival** ( **can’t** **investigate** **past**). **Monitoring** **only** **infra** ( **no** **app** **metrics**). **No** **dashboard** for **on-call** ( **blind** **response**).

---

## Q7. (Intermediate) List red flags in security (DevSecOps).

**Answer:**  
**Secrets** in **code**, **config**, or **logs**. **No** **dependency** or **image** **scan** in **CI**. **Running** as **root** in **containers**; **privileged** **pods** **without** **need**. **No** **network** **policy** ( **allow** **all**). **No** **admission** **policy** ( **any** **image**/ **config**). **Broad** **RBAC** ( **admin** **for** **everyone**). **No** **audit** of **access** or **changes**. **Security** **only** at **end** ( **no** **shift-left**).

---

## Q8. (Intermediate) List red flags in infrastructure and configuration.

**Answer:**  
**Manual** **changes** to **managed** **resources** ( **drift**). **No** **IaC** or **state** **not** **versioned** ( **no** **repro**). **State** **local** and **unlocked** ( **corruption**/ **concurrent** **apply**). **No** **resource** **limits** in **K8s** ( **noisy** **neighbor**; **OOM**). **Single** **point** of **failure** ( **one** **AZ**, **one** **DB**). **No** **backup** or **disaster** **recovery** **test**. **Config** **not** **in** **Git** ( **no** **audit**; **drift**).

---

## Q9. (Intermediate) What is the "blast radius" mindset? How does it reduce red flags?

**Answer:**  
**Blast** **radius**: **limit** **scope** of **impact** of **change** or **failure** ( **canary**, **feature** **flag**, **small** **deploy** **batch**). **Reduces** **red** **flags**: **avoid** " **deploy** **everything** **at** **once**" ( **big** **bang**); **avoid** " **one** **config** **for** **all** **regions**" ( **one** **mistake** = **global**). **Practice**: **gradual** **rollout**; **isolate** **failure** **domains**; **small** **changes**; **easy** **rollback**.

---

## Q10. (Intermediate) How do you turn "red flag" practices into green (best practices)?

**Answer:**  
**Secrets** → **secret** **store** ( **Vault**, **cloud**); **never** in **repo**. **No** **rollback** → **automate** **rollback** ( **kubectl** **rollout** **undo** or **re-deploy** **previous** **tag**); **runbook**. **No** **tests** **gate** → **fix** **flaky** **tests**; **meaningful** **gate**; **no** **skip** **without** **exception** **process**. **Manual** **deploy** → **pipeline** **as** **code**; **approval** **gate**. **No** **monitoring** → **RED**/ **USE** **metrics**; **alerts** with **runbooks**; **SLO**. **Drift** → **IaC**; **no** **manual** **change**; **drift** **detection** in **CI**. **Document** **and** **prioritize**; **tackle** **one** **at** a **time**.

---

## Q11. (Advanced) Production scenario: You join a team with many red flags (no SLO, secrets in env files in repo, no rollback). How do you prioritize and fix?

**Answer:**  
**Prioritize** by **risk** and **effort**: (1) **Secrets** **immediately** — **rotate** **exposed** **secrets**; **move** to **Vault**/ **cloud** **store**; **remove** from **repo** ( **history** **rewrite** if **needed**); **CI** **scan** to **prevent** **recurrence**. (2) **Rollback** **procedure** — **document** **last** **good** **tag**/ **commit**; **runbook** ( **kubectl** **rollout** **undo** or **redeploy**); **test** **rollback** in **staging**. (3) **SLO** — **define** **one** **availability** **SLI**; **instrument**; **dashboard**; **alert** on **breach**; **error** **budget** **policy** **later**. (4) **Pipeline** **and** **parity** — **pipeline** **as** **code**; **no** **manual** **deploy**; **staging** **parity** **doc**. **Communicate** **plan** to **team**; **small** **increments**; **no** **blame**.

---

## Q12. (Advanced) What are anti-patterns in incident response and post-mortem?

**Answer:**  
**Blaming** **individuals** ( **names** in **doc**; **sanctions**). **No** **post-mortem** ( **we** **fixed** it). **Vague** **action** **items** ( **improve** **monitoring** — **how**?). **Action** **items** **not** **tracked** ( **forgotten**). **No** **communication** during **incident** ( **silent** **for** **hours**). **War** **room** **chaos** ( **no** **incident** **commander**; **everyone** **talking**). **No** **runbook** ( **ad-hoc** **every** **time**). **Same** **incident** **repeats** ( **no** **learning** **or** **remediation**). **Fix**: **blameless** **culture**; **documented** **runbooks**; **tracked** **actions**; **IC** **role**; **post-mortem** **within** **48** h.

---

## Q13. (Advanced) What are red flags specific to Kubernetes and containers?

**Answer:**  
**latest** **tag** or **no** **resource** **requests**/limits. **Stateful** **workload** **without** **PVC**. **Liveness** **same** as **readiness** or **too** **aggressive** ( **restart** **loop**). **Secrets** in **plain** **YAML** in **Git**. **No** **PDB** for **HA** **apps** ( **drain** **kills** **all**). **Privileged** or **host** **network** **without** **justification**. **No** **NetworkPolicy** ( **allow** **all**). **Single** **replica** **critical** **service**. **No** **readiness** ( **traffic** to **unready** **pods**). **Image** **from** **untrusted** **registry** **without** **scan**.

---

## Q14. (Advanced) What are red flags in CI/CD and pipeline design?

**Answer:**  
**No** **tests** or **skip** **tests** to **pass**. **No** **approval** **gate** for **prod** ( **or** **blind** **auto** **deploy** **no** **SLO** **check**). **Rebuild** **per** **env** ( **not** **promotion**). **Secrets** in **pipeline** **code** or **logs**. **No** **post-deploy** **verification**. **Long** **sequential** **pipeline** ( **no** **parallel**/ **cache**). **No** **pipeline** **as** **code**. **Deploy** **from** **local** **laptop** ( **no** **audit**). **No** **rollback** **automation**. **Single** **branch** **deploy** **to** **prod** **without** **staging** **validation**.

---

## Q15. (Advanced) How do you establish a "red flag" review in design or architecture meetings?

**Answer:**  
**Checklist** or **lens** in **design** **review**: **blast** **radius** ( **what** **if** **this** **fails**?); **rollback** ( **how** **do** **we** **revert**?); **secrets** ( **where** **stored**?); **observability** ( **what** **do** **we** **alert** on?); **parity** ( **how** **do** **we** **test** in **staging**?); **security** ( **least** **privilege**? **scan**?). **Document** **decisions** and **accepted** **risks**; **follow-up** **actions** for **red** **flags** **accepted** **short-term** ( **tech** **debt** **ticket**). **Culture**: **safe** to **raise** **red** **flags**; **no** **shame**; **improve** **system**.

---

## Q16. (Advanced) What is the relationship between red flags and tech debt? How do you track both?

**Answer:**  
**Red** **flags** **often** **are** **tech** **debt** ( **shortcuts** that **increase** **risk**). **Track**: **tech** **debt** **backlog** ( **tickets** with **label** **tech-debt** or **red-flag**); **priority** by **impact** and **likelihood**; **sprint** **allocation** (e.g. **20%** **capacity** for **debt**). **Link** **to** **post-mortems** ( **action** **items** = **debt** **reduction**). **Dashboard**: **open** **debt** **items**; **age**; **category** ( **security**, **reliability**, **observability**). **Review** **quarterly**; **don’t** **allow** **unbounded** **growth**.

---

## Q17. (Advanced) How do you balance "ship fast" with avoiding red flags (e.g. startup pressure)?

**Answer:** **Accept** **temporary** **risk** **explicitly**: **document** (e.g. " **no** **canary** **until** Q2"); **time-bound** **debt** **ticket**; **review** **date**. **Minimum** **viable** **safety**: **secrets** **never** in **repo**; **rollback** **possible** ( **even** **manual** **runbook**); **one** **meaningful** **alert** ( **error** **rate** or **down**); **deploy** **via** **pipeline** ( **not** **ad-hoc**). **Improve** **incrementally**: **add** **canary** when **stable**; **add** **SLO** when **reliability** **matters**; **don’t** **boil** **ocean**. **Communicate** **to** **stakeholders**: " **We** **ship** **fast** **with** **these** **risks**; **we** **reduce** **them** by **X**."

---

## Q18. (Advanced) What red flags should a senior DevOps engineer raise when reviewing a new system?

**Answer:**  
**No** **rollback** or **no** **last** **known** **good** **artifact**. **Secrets** in **code**/ **config**/ **logs**. **No** **monitoring** or **SLO** for **critical** **path**. **Single** **point** of **failure** ( **one** **AZ**, **one** **DB** **no** **replica**). **No** **resource** **limits** ( **K8s**/ **containers**). **Default** **allow** **network** ( **no** **NetworkPolicy**). **Manual** **deploy** or **no** **pipeline** **as** **code**. **No** **staging** or **parity** **doc**. **Privileged** **pods** or **root** **without** **justification**. **No** **runbook** for **on-call**. **Raising**: **constructive** ( **risk** + **suggestion**); **prioritized** ( **P0** vs **P2**); **offer** to **help** **remediate**.

---

## Q19. (Advanced) How do you create a "red flag" checklist for production readiness?

**Answer:**  
**Checklist** **categories**: **Deploy** ( **pipeline** **as** **code**; **rollback** **tested**; **approval** **gate** for **prod**; **no** **secrets** in **repo**). **Observability** ( **metrics** **RED**/ **USE**; **alerts** with **runbook**; **logs** **correlated**; **SLO** **defined**). **Security** ( **secrets** in **store**; **image** **scan**; **non-root**; **NetworkPolicy** **or** **justified** **allow**). **Reliability** ( **replicas** ≥ 2 for **HA**; **PDB**; **resource** **limits**; **health** **checks**). **Config** ( **config** in **Git**; **parity** **doc**; **no** **manual** **prod** **change**). **Incident** ( **runbook**; **on-call** **defined**; **post-mortem** **process**). **Gate**: **sign-off** per **category** ( **go**/ **no-go**); **exceptions** **documented** with **owner** and **date**.

---

## Q20. (Advanced) Senior red flags: consolidated list and how to fix them

**Answer:**  
**Deploy**: No rollback → automate and document. Rebuild per env → build once, promote. No approval gate → add gate; SLO check optional. **Observability**: No SLO → define SLI/SLO and alert. No runbook → link runbook to alerts. High cardinality → reduce labels. **Security**: Secrets in repo → move to store; scan in CI. No scan → add dependency and image scan. No NetworkPolicy → default deny + allow list. **Infra**: Manual change → IaC; drift detection. State local → remote backend + lock. No limits → set requests/limits. **Incident**: Blame in post-mortem → blameless process. No action items → create tickets; track. **Culture**: Skip tests → fix flaky; no skip without exception. No parity doc → document and reduce diffs. **Fix**: Prioritize by risk; one improvement at a time; document and track tech debt; review readiness with checklist.

---

**Tradeoffs:** Startup: minimal checklist (secrets, rollback, one alert). Medium: full deploy and observability checklist; security baseline. Enterprise: production readiness gate, red flag review in design, tech debt allocation.
