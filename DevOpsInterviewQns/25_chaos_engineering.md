# 25. Chaos Engineering

## Q1. (Beginner) What is chaos engineering? What is its goal?

**Answer:**  
**Chaos** **engineering**: **experiments** that **intentionally** **inject** **failure** (e.g. **kill** **pod**, **network** **delay**) to **test** **system** **resilience** and **discover** **weaknesses**. **Goal**: **build** **confidence** that **system** **handles** **real** **failures**; **find** **bugs** and **single** **points** of **failure** **before** **incidents**. **Principle**: **steady** **state** (e.g. **SLO**); **hypothesis** (e.g. " **if** **DB** **slow**, **API** **degrades** **gracefully**"); **experiment**; **learn**.

---

## Q2. (Beginner) What is a blast radius? Why does it matter in chaos?

**Answer:**  
**Blast** **radius**: **scope** of **impact** of an **experiment** (e.g. **one** **pod** vs **whole** **region**). **Matters**: **limit** **blast** **radius** so **experiment** doesn’t **cause** **real** **outage**; **start** **small** ( **one** **node**, **one** **service**); **expand** as **confidence** **grows**. **Use** **abort** **conditions** (e.g. **error** **rate** **spike** → **stop** **experiment**).

---

## Q3. (Beginner) Name two types of faults you might inject in a chaos experiment.

**Answer:**  
**Pod** **kill** ( **terminate** **container**/pod); **network** **delay** or **partition** ( **between** **services**); **CPU**/memory **stress**; **disk** **full**; **clock** **skew**; **dependency** **failure** ( **mock** **down**). **K8s**: **pod** **kill**, **network** **policy** **block**, **node** **failure** ( **drain**). **Application**: **latency** **injection**, **error** **injection** ( **5xx** **rate**).

---

## Q4. (Beginner) What is the difference between chaos engineering and testing?

**Answer:**  
**Testing**: **assert** **known** **behavior** ( **unit**/integration **test**); **pass**/fail. **Chaos** **engineering**: **observe** **behavior** under **failure**; **hypothesis**-driven; **may** **discover** **unknown** **failure** **modes**. **Chaos** **complements** **tests** ( **tests** = **correct** **logic**; **chaos** = **resilience** under **real** **world** **failures**).

---

## Q5. (Intermediate) How do you run a safe chaos experiment in Kubernetes (e.g. kill one pod)?

**Answer:**  
**Tool**: **Litmus** **Chaos**, **Chaos** **Mesh**, or **manual** **kubectl delete pod**. **Safe** **practice**: (1) **Target** **one** **pod** ( **Deployment** **recreates** it). (2) **Run** in **staging** **first**. (3) **Define** **abort** **condition** (e.g. **error** **rate** > **5%** → **stop**). (4) **Monitor** **SLO** during **experiment**. (5) **Time** **bound** (e.g. **5** min **max**). (6) **Runbook** and **rollback** ( **stop** **experiment** **immediately**). **Example** **Chaos** **Mesh**: **PodChaos** **action** **pod-kill**; **selector** **one** **pod**; **duration** **30s**.

---

## Q6. (Intermediate) What is Chaos Mesh? What kinds of faults does it support?

**Answer:**  
**Chaos** **Mesh**: **K8s** **operator** for **chaos** **experiments**; **CRDs** for **fault** **types**. **Supports**: **PodChaos** ( **kill**, **failure**); **NetworkChaos** ( **delay**, **loss**, **partition**); **StressChaos** ( **CPU**/memory **stress**); **TimeChaos** ( **clock** **skew**); **DNSChaos**; **HTTPChaos** ( **abort**/delay **by** **path**). **Schedule** **experiments** ( **cron**); **limit** **scope** by **namespace**/label.

---

## Q7. (Intermediate) How do you verify system behavior during and after a chaos experiment?

**Answer:**  
**During**: **metrics** ( **Prometheus** — **error** **rate**, **latency**); **dashboards** ( **Grafana**); **alerts** ( **should** **not** **fire** if **resilient**, or **expected** **degradation**). **After**: **compare** **steady** **state** **before**/after; **check** **recovery** ( **pods** **back**, **traffic** **normal**); **logs** for **errors**/retries. **Automate**: **Litmus** **probes** ( **success** **criteria**); **Chaos** **Mesh** **status** ( **phase** **Running**/ **Paused**). **Report**: **experiment** **result** ( **hypothesis** **confirmed** or **not**).

---

## Q8. (Intermediate) What is a steady state hypothesis? Why define it before chaos?

**Answer:**  
**Steady** **state** **hypothesis**: **metric** or **behavior** that **defines** " **normal**" (e.g. **availability** **99.9%**, **error** **rate** < **0.1%**). **Define** **before**: **experiment** **validates** that **system** **returns** to **steady** **state** (or **degrades** **predictably**); **abort** if **hypothesis** **violated** **unexpectedly**. **Example**: " **During** **pod** **kill**, **error** **rate** **remains** < **1%** and **recovers** to **< 0.1%** within **2** min."

---

## Q9. (Intermediate) How do you limit blast radius in a network partition experiment?

**Answer:**  
**Partition** **only** **specific** **pods**/namespaces (e.g. **block** **traffic** **between** **service** A and **DB**; **not** **whole** **cluster**). **Tool**: **NetworkChaos** with **selector** ( **only** **app=frontend** and **app=backend**); **direction** ( **one** **way** or **both**). **Scope**: **one** **namespace**; **one** **replica** of **service**. **Abort**: **automated** **rollback** if **SLO** **breach** (e.g. **error** **rate** **threshold**).

---

## Q10. (Intermediate) What is GameDay? How does it relate to chaos engineering?

**Answer:**  
**GameDay**: **planned** **event** where **team** **runs** **failure** **scenarios** (e.g. **region** **down**, **DB** **failover**) and **observes** **response**; **often** **manual** **or** **semi-automated**. **Relation**: **chaos** **engineering** **practice**; **GameDay** = **structured** **chaos** **experiment** with **people** **in** **loop** ( **runbooks**, **communication**). **Automate** **injection**; **humans** **monitor** and **decide** **abort**/remediation.

---

## Q11. (Advanced) Production scenario: Explain how you would implement chaos to test resilience of a microservices architecture (e.g. 5 services, DB, cache).

**Answer:**  
**Hypothesis**: " **If** **one** **service** or **dependency** **fails**, **others** **degrade** **gracefully** ( **circuit** **breaker**, **retry**, **cached** **data**) and **recover**." **Experiments** ( **staging** **first**): (1) **Kill** **one** **pod** per **service** ( **verify** **replica** **takes** **traffic**; **no** **cascade**). (2) **Network** **partition** **service** ↔ **DB** ( **verify** **timeout**/circuit **breaker**; **no** **hang**). (3) **Kill** **cache** **pod** ( **verify** **cold** **cache** **handled**; **DB** **doesn’t** **overload**). (4) **Inject** **latency** **DB** ( **verify** **timeout** and **degraded** **response**). **Metrics**: **error** **rate**, **latency** **p99**, **dependency** **health**. **Abort** if **error** **rate** > **N%** or **latency** **>** **SLO**. **Document** **findings** and **fix** **weak** **points** ( **retry** **policy**, **circuit** **breaker**).

---

## Q12. (Advanced) How do you run chaos experiments in production safely (e.g. only during business hours, with approval)?

**Answer:**  
(1) **Approval**: **manual** **trigger** or **change** **request**; **not** **scheduled** **blind** in **prod**. (2) **Time** **window**: **business** **hours** ( **low** **traffic**) or **maintenance** **window**; **exclude** **critical** **dates**. (3) **Blast** **radius**: **one** **instance**/pod; **canary** **only**; **one** **AZ**. (4) **Abort**: **automated** **rollback** on **SLO** **breach**; **manual** **stop** **button**. (5) **Communication**: **notify** **on-call** and **stakeholders**; **runbook** **ready**. (6) **Gradual**: **start** in **staging**; **prod** **only** after **proven** **safe** **scenarios**.

---

## Q13. (Advanced) What is fault injection in service mesh (e.g. Istio)? How do you use it for chaos?

**Answer:**  
**Istio** **fault** **injection**: **VirtualService** **fault** ( **delay**, **abort** **percentage**). **Example**: **50%** **delay** **5s** to **reviews** **service**; **10%** **HTTP** **500** to **ratings**. **Use**: **test** **client** **timeout** and **retry**; **test** **fallback** (e.g. **reviews** **default** when **ratings** **down**). **Controlled** ( **percentage**, **duration**); **no** **pod** **kill**; **complement** **pod** **chaos** with **dependency** **failure** **simulation**.

---

## Q14. (Advanced) How do you implement abort conditions (e.g. stop experiment if error rate spikes)?

**Answer:**  
**Chaos** **Mesh**: **optional** **integration** with **Prometheus** ( **metrics** **check**); **custom** **controller** that **pauses**/deletes **chaos** **CR** when **condition** **met**. **Litmus**: **probes** ( **prometheus** **probe**) **fail** → **experiment** **fail**/abort. **Custom**: **sidecar** or **CI** **script** that **polls** **Prometheus** (e.g. **error** **rate** > **5%**); **kubectl** **delete** **chaos** **resource** or **call** **Chaos** **Mesh** **API** to **pause**. **Result**: **experiment** **stops** **before** **user** **impact** **grows**.

---

## Q15. (Advanced) Production scenario: You want to validate that your API gracefully handles database failover. Design the experiment.

**Answer:**  
**Hypothesis**: " **During** **DB** **failover** ( **30–60s** **unavailability**), **API** **returns** **503** or **retries** and **recovers** within **2** min **without** **data** **loss**." **Experiment**: (1) **Staging** **first**: **trigger** **DB** **failover** ( **RDS** **reboot** or **promote** **replica**); **or** **simulate** ( **block** **traffic** to **primary** **DB** **pod**). (2) **Measure**: **API** **error** **rate**, **latency**; **DB** **connection** **pool** **exhaustion**; **recovery** **time**. (3) **Abort**: if **error** **rate** > **50%** for **> 5** min or **data** **loss** **detected**. (4) **Fix**: **connection** **retry**, **timeout**, **circuit** **breaker**; **repeat** until **hypothesis** **met**. **Prod**: **run** during **maintenance** **window** with **approval**; **same** **metrics** and **abort**.

---

## Q16. (Advanced) What is chaos engineering for serverless (e.g. Lambda)? What can you inject?

**Answer:**  
**Inject**: **throttling** ( **concurrent** **execution** **limit**); **delay** ( **simulate** **cold** **start** or **dependency** **slow**); **failure** **rate** ( **mock** **dependency** **returns** **error**); **timeout** ( **function** **timeout**). **Tool**: **AWS** **Fault** **Injection** **Simulator** ( **FIS**); **custom** **lambda** that **calls** **downstream** with **delay**/error. **Test**: **retry** **behavior**, **DLQ**, **circuit** **breaker** (e.g. **Step** **Functions** **retry**).

---

## Q17. (Advanced) How do you document and socialize chaos experiments (runbooks, outcomes)?

**Answer:**  
**Document**: **experiment** **template** ( **hypothesis**, **fault**, **scope**, **duration**, **abort** **conditions**); **runbook** ( **how** to **run**, **how** to **abort**); **results** ( **pass**/fail, **metrics** **before**/after, **findings**). **Store** in **wiki** or **Git** ( **chaos** **repo**); **link** to **service** **runbook**. **Socialize**: **blameless** **review** of **failed** **experiments** ( **what** we **learned**); **share** **in** **SRE** **forum**; **schedule** **GameDays**; **onboard** **new** **teams** to **chaos** **practice**.

---

## Q18. (Advanced) How do you avoid chaos experiments causing real incidents?

**Answer:**  
(1) **Start** in **staging**; **only** **prod** when **proven** **safe**. (2) **Minimal** **blast** **radius** ( **one** **pod**, **one** **AZ**). (3) **Abort** **conditions** **automated** ( **SLO** **breach** → **stop**). (4) **Time** **box** (e.g. **5** min **max**). (5) **Approval** and **communication** for **prod**. (6) **Rollback** **plan** ( **delete** **chaos** **CR**; **verify** **recovery**). (7) **Don’t** **run** **untested** **scenarios** in **prod**; **don’t** **run** **during** **critical** **launch**.

---

## Q19. (Advanced) What is continuous chaos (e.g. Chaos Monkey)? How does it differ from planned experiments?

**Answer:**  
**Continuous** **chaos**: **automated** **injection** on **schedule** (e.g. **daily** **kill** **random** **instance**); **no** **manual** **trigger**. **Chaos** **Monkey** (Netflix): **terminates** **random** **instances** **during** **business** **hours**. **Difference**: **planned** = **hypothesis**-driven, **controlled** **scope**; **continuous** = **ongoing** **resilience** **validation**, **small** **blast** **radius**. **Use** **continuous** when **system** **already** **resilient** ( **proven** by **planned** **experiments**); **start** with **planned** **first**.

---

## Q20. (Advanced) Senior red flags to avoid in chaos engineering

**Answer:**  
- **Running** **chaos** in **prod** **without** **staging** **validation**.  
- **No** **abort** **condition** ( **experiment** **runs** **until** **manual** **stop**).  
- **Large** **blast** **radius** ( **whole** **service**/region **down**).  
- **No** **hypothesis** or **steady** **state** ( **random** **breaking** **things**).  
- **No** **communication** ( **on-call** **surprised** by **alerts**).  
- **Ignoring** **findings** ( **run** **experiment** but **don’t** **fix** **weaknesses**).  
- **Chaos** **as** **blame** ( **post-mortem** **blameless**; **focus** on **systems**).  
- **No** **rollback** **plan** ( **can’t** **stop** **experiment** **fast**).

---

**Tradeoffs:** Startup: manual GameDay, no prod chaos. Medium: Chaos Mesh in staging, planned experiments. Enterprise: continuous chaos (small scope), automated abort, prod GameDays with approval.
