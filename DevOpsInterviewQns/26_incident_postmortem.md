# 26. Incident Response & Blameless Post-Mortem

## Q1. (Beginner) What are the immediate steps when a critical service goes down?

**Answer:**  
(1) **Acknowledge** and **assess**: **confirm** **outage** ( **user** **report** or **alert**); **scope** ( **which** **service**, **which** **users**). (2) **Mitigate**: **restore** **service** ( **rollback**, **scale** **up**, **failover**, **disable** **feature**) to **stop** **bleeding**. (3) **Communicate**: **status** **page**; **internal** **channel** ( **incident** **channel**); **on-call** **coordinator**. (4) **Don’t** **blame**; **focus** on **restoration** **first**. (5) **After** **stable**: **post-mortem** and **remediation**.

---

## Q2. (Beginner) What do you monitor first when a service is down?

**Answer:**  
**User-facing**: **error** **rate**, **latency** ( **RED**); **availability** **SLO**. **Infra**: **pod**/instance **count** ( **ready**?); **deployment** **status** ( **recent** **change**?); **node** **health**. **Dependencies**: **DB**, **cache**, **downstream** **APIs** ( **latency**, **errors**). **Recent** **changes**: **deploy** **time**, **config** **change**, **traffic** **spike**. **Order**: **symptoms** ( **where** **errors**?) → **dependencies** → **recent** **changes** → **logs**/traces.

---

## Q3. (Beginner) What is a blameless post-mortem? Why is it important?

**Answer:**  
**Blameless** **post-mortem**: **review** of **incident** **focused** on **systems** and **processes**, **not** **individual** **fault**; **goal** = **learn** and **improve**. **Important**: **people** **share** **honestly**; **root** **cause** ( **why** did **system** **allow** **failure**?) **identified**; **actionable** **remediation**; **no** **fear** of **punishment**. **Output**: **timeline**, **root** **cause**, **actions** ( **fix**, **monitoring**, **process**).

---

## Q4. (Beginner) What should a post-mortem document contain?

**Answer:**  
**Summary** ( **what** **happened**, **impact**); **timeline** ( **UTC**, **events**); **root** **cause** ( **why**); **impact** ( **users**, **duration**, **SLO**); **detection** ( **how** **we** **found** **out**); **resolution** ( **how** **we** **fixed**); **action** **items** ( **owner**, **due** **date**); **lessons** **learned**. **Optional**: **what** **went** **well**; **appendix** ( **logs**, **graphs**). **No** **names** for **blame**; **focus** on **decisions** and **context**.

---

## Q5. (Intermediate) How do you decide what to monitor first during an outage? (Priority order)

**Answer:**  
**Priority**: (1) **SLO**/ **user** **impact** ( **where** **are** **errors**? **which** **region**/ **service**?). (2) **Recent** **changes** ( **deploy**, **config**, **traffic**). (3) **Dependencies** ( **DB**, **cache**, **external** **API** **health**). (4) **Resource** **saturation** ( **CPU**, **memory**, **connections**). (5) **Logs**/traces for **errors** ( **after** **narrowing** **scope**). **Dashboard** **order**: **top** = **user** **impact**; **then** **dependency** **health**; **then** **infra** and **logs**.

---

## Q6. (Intermediate) What is the difference between root cause and contributing factors?

**Answer:**  
**Root** **cause**: **primary** **reason** the **incident** **occurred** (e.g. " **deploy** **introduced** **bug**" or " **DB** **connection** **pool** **exhausted**"). **Contributing** **factors**: **conditions** that **made** **it** **worse** or **possible** (e.g. " **no** **canary**", " **alert** **threshold** **too** **high**", " **single** **AZ**"). **Post-mortem** **addresses** **both**: **fix** **root** **cause**; **improve** **contributing** **factors** ( **detection**, **mitigation**, **architecture**).

---

## Q7. (Intermediate) How do you run a blameless post-mortem meeting?

**Answer:**  
**Schedule** within **48–72** h ( **fresh** **memory**). **Attendees**: **incident** **responders**, **relevant** **teams**, **facilitator**. **Rules**: **blameless** ( **no** " **who** **screwed** **up**"); **focus** on **timeline** and **decisions** ( **what** **information** **was** **available**?); **everyone** **can** **speak**. **Agenda**: **timeline** **review**; **root** **cause** **discussion**; **action** **items**; **publish** **doc** and **track** **actions**. **Follow-up**: **action** **items** in **ticket** **system**; **review** in **2** **weeks**.

---

## Q8. (Intermediate) What is an incident severity level? How do you define P1 vs P2?

**Answer:**  
**Severity** = **impact** + **urgency**. **P1** ( **critical**): **major** **outage** ( **core** **service** **down**, **data** **loss** risk); **all** **hands**; **page** **immediately**. **P2** ( **high**): **significant** **degradation** or **partial** **outage**; **fix** **within** **hours**. **P3** ( **medium**): **limited** **impact**; **fix** **within** **days**. **P4** ( **low**): **minor**; **backlog**. **Define** per **org** ( **user** **count**, **revenue** **impact**, **SLA**).

---

## Q9. (Intermediate) How do you communicate during an incident (internal and external)?

**Answer:**  
**Internal**: **incident** **channel** ( **Slack**/Teams); **designated** **incident** **commander**; **clear** **updates** ( **what** **we** **know**, **what** **we’re** **doing**); **avoid** **noise** ( **one** **channel**, **threads** for **subtasks**). **External**: **status** **page** ( **investigating** → **identified** → **fixing** → **resolved**); **customer** **comms** if **SLA** **breach** or **data** **impact**. **Template** **updates** ( **impact**, **ETA**, **next** **update**).

---

## Q10. (Intermediate) What is a runbook? How does it help during an incident?

**Answer:**  
**Runbook**: **step-by-step** **guide** for **common** **scenarios** (e.g. " **service** **down**", " **DB** **failover**", " **rollback** **deploy**"). **Helps**: **consistent** **response**; **faster** **mitigation**; **on-call** **doesn’t** **rely** **on** **memory**. **Content**: **trigger** ( **alert**); **steps** ( **commands**, **links**); **escalation**; **verification**. **Link** **runbooks** from **alerts**; **keep** **updated** after **post-mortems**.

---

## Q11. (Advanced) Production scenario: Critical service goes down. Walk through your immediate steps and how you conduct a blameless post-mortem.

**Answer:**  
**Immediate**: (1) **Acknowledge** **alert**; **join** **incident** **channel**; **confirm** **scope** ( **dashboards**, **user** **reports**). (2) **Mitigate**: **check** **recent** **deploy** → **rollback** if **suspected**; **scale** **up** if **capacity**; **disable** **feature** if **optional**; **failover** if **DB**/region. (3) **Communicate**: **status** **page** " **Investigating**"; **internal** **update** every **15** min. (4) **Stable**: **verify** **recovery**; **status** " **Resolved**". **Post-mortem**: **schedule** within **48** h; **gather** **timeline** ( **logs**, **deploys**, **metrics**); **meeting** **blameless** ( **what** **happened**, **why** **system** **allowed** it); **root** **cause** + **contributing** **factors**; **action** **items** ( **fix**, **alert**, **test**); **publish** **doc**; **track** **actions**. **No** **naming** **individuals**; **focus** on **process** and **tech** **debt**.

---

## Q12. (Advanced) How do you decide between rollback vs fix-forward during an incident?

**Answer:**  
**Rollback**: **revert** to **last** **known** **good** ( **deploy**, **config**); **fast** **recovery** when **change** **likely** **cause**; **low** **risk** if **rollback** **tested**. **Fix-forward**: **deploy** **fix** ( **patch**, **config** **change**); **when** **rollback** **not** **possible** ( **data** **migration** **already** **run**) or **root** **cause** **clear** and **fix** **simple**. **Decision**: **time** to **rollback** vs **fix**; **risk** of **rollback** ( **data** **compat**?); **confidence** in **fix**. **Default** **prefer** **rollback** for **speed**; **fix-forward** when **necessary**.

---

## Q13. (Advanced) What are action items from a post-mortem? How do you ensure they get done?

**Answer:**  
**Action** **items**: **concrete** **tasks** ( **add** **alert**, **fix** **bug**, **improve** **runbook**, **add** **test**); **owner** and **due** **date**. **Ensure**: **create** **tickets** ( **Jira**/GitHub **Issues**); **link** to **post-mortem**; **review** in **2** **weeks** ( **post-mortem** **follow-up** **meeting**); **track** in **SRE** **dashboard** ( **open** **actions**). **Escalate** if **overdue**; **close** **post-mortem** when **critical** **actions** **done**. **No** **action** **items** = **post-mortem** **incomplete**.

---

## Q14. (Advanced) How do you handle incidents that span multiple teams? Who leads?

**Answer:**  
**Incident** **commander** ( **IC**): **one** **person** **coordinates** ( **communication**, **priorities**); **may** **not** **be** **technical** **lead** for **each** **area**. **Tech** **leads** per **area** ( **frontend**, **backend**, **DB**); **IC** **gets** **updates** and **decides** **next** **steps**. **Channel**: **single** **incident** **channel**; **IC** **posts** **updates**; **teams** **post** **findings** and **blockers**. **Escalation**: **IC** **escalates** to **management** if **need** **resources** or **customer** **comms**. **Post-mortem**: **all** **teams** **contribute**; **IC** **facilitates** or **doc** **owner**.

---

## Q15. (Advanced) Production scenario: Outage was caused by a bad deploy. How do you address it in the post-mortem without blaming the deployer?

**Answer:**  
**Frame** **blamelessly**: " **A** **deploy** **introduced** **a** **bug** that **caused** **X**; **our** **process** **did** **not** **catch** it **before** **prod**." **Focus** on **system**: **why** **did** **tests** **not** **catch** it? **Why** **no** **canary**? **Why** **no** **automated** **rollback** on **error** **rate**? **Actions**: **add** **test** ( **unit**/integration); **add** **canary** or **staged** **rollout**; **add** **automated** **rollback** ( **alert** → **rollback**); **improve** **review** ( **checklist**). **Thank** **deployer** for **participation** in **post-mortem**; **no** **sanctions** for **mistakes** that **process** **should** **have** **prevented**.

---

## Q16. (Advanced) What is a war room? How do you keep it effective?

**Answer:**  
**War** **room**: **virtual** or **physical** **space** where **incident** **responders** **coordinate** ( **channel** + **call**). **Effective**: **single** **channel** ( **no** **parallel** **chats**); **incident** **commander** **clearly** **assigned**; **mute** **non-essential** **people** ( **listen** only); **updates** in **thread** or **pinned** **message**; **recorder** ( **timeline** **scribe**); **clear** **roles** ( **mitigation**, **comms**, **investigation**). **Avoid** **too** **many** **people**; **invite** **only** **needed** **experts**.

---

## Q17. (Advanced) How do you measure and improve incident response (e.g. MTTR, MTTD)?

**Answer:**  
**MTTD** ( **Mean** **Time** to **Detect**): **time** from **start** of **incident** to **detection** ( **alert** or **report**). **MTTR** ( **Mean** **Time** to **Resolve**): **time** from **detection** to **resolution**. **Track** per **incident**; **average** per **month**; **trend** **dashboard**. **Improve**: **better** **alerts** ( **reduce** **MTTD**); **runbooks** and **automation** ( **reduce** **MTTR**); **post-mortem** **actions** ( **prevent** **recurrence**); **chaos** **and** **drills** ( **practice** **response**).

---

## Q18. (Advanced) What is the role of a status page during and after an incident?

**Answer:**  
**During**: **transparent** **communication** ( **investigating**, **identified**, **fixing**); **reduce** **support** **tickets**; **set** **expectations**. **Update** **regularly** (e.g. **every** **15** min); **avoid** **generic** " **we’re** **working** **on** it" — **add** **what** **we** **know**. **After**: **post-incident** **report** ( **summary**, **root** **cause**, **what** **we’re** **doing**); **subscriber** **notification** if **opted** in. **Integrate** with **incident** **tool** ( **PagerDuty**, **Statuspage**) for **consistency**.

---

## Q19. (Advanced) How do you learn from near-misses (no user impact but could have)?

**Answer:**  
**Treat** as **incident** **lite**: **short** **post-mortem** or **write-up** ( **what** **happened**, **why** **no** **impact** — **luck**? **safeguard**?); **what** **could** **we** **do** **better** ( **alert** **earlier**, **prevent** **condition**). **Action** **items** ( **add** **alert**, **harden** **config**). **Share** in **team** **meeting**; **no** **blame**. **Near-misses** **prevent** **future** **real** **incidents** if **acted** **on**.

---

## Q20. (Advanced) Senior red flags to avoid in incident and post-mortem

**Answer:**  
- **Blaming** **people** ( **names** in **doc**; " **X** **deployed** **bad** **code**").  
- **No** **post-mortem** ( **we** **fixed** it, **move** on).  
- **Vague** **action** **items** ( **improve** **monitoring** — **how**?).  
- **Action** **items** **not** **tracked** ( **forgotten**).  
- **No** **communication** during **incident** ( **silent** **for** **hours**).  
- **Skipping** **runbook** ( **ad-hoc** **every** **time**).  
- **No** **severity** **definition** ( **everything** **P1** or **nothing** **P1**).  
- **Post-mortem** **without** **learning** ( **same** **incident** **repeats**).

---

**Tradeoffs:** Startup: lightweight severity, single channel, doc in wiki. Medium: IC role, runbooks, status page. Enterprise: formal severity, war room, MTTR/MTTD tracking, blameless culture.
