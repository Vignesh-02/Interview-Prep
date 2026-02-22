# 13. SLI, SLO, SLA & Reliability

## Q1. (Beginner) What is an SLI? Give two examples for a web API.

**Answer:**  
**SLI** (Service Level **Indicator**): **measurable** **metric** of **service** behavior. **Examples**: **availability** (successful requests / total requests), **latency** (e.g. p99 response time). **Other**: **error rate** (5xx / total), **throughput** (req/s). **Must** be **observable** (instrumented).

---

## Q2. (Beginner) What is an SLO? How does it differ from an SLI?

**Answer:**  
**SLO** (Service Level **Objective**): **target** for an **SLI** (e.g. "availability ≥ 99.9%"). **SLI** = **what** you measure; **SLO** = **target** you aim for. **Example**: SLI = availability; SLO = 99.9% over 30 days. **Use** SLO for **prioritization** and **error budget**.

---

## Q3. (Beginner) What is an SLA? When does it involve customers?

**Answer:**  
**SLA** (Service Level **Agreement**): **contractual** **commitment** to a **level** of service; often includes **remediation** (credits, penalties) if **breach**. **Customer**: **external** customers; **SLA** is **legal**/commercial. **Internal**: teams may have **internal** SLAs or **SLOs** only (no contract). **SLO** = internal target; **SLA** = external (or formal) commitment.

---

## Q4. (Beginner) What is error budget? How is it derived from an SLO?

**Answer:**  
**Error budget**: **allowed** **unreliability** in a period; **1 - SLO**. **Example**: SLO 99.9% availability → **0.1%** error budget = **43 min** downtime per **month**. **Use**: **spend** budget on **releases**/changes; **exhausted** = **freeze** feature work, **focus** on **reliability**. **Formula**: budget = (1 - SLO) × period.

---

## Q5. (Intermediate) How do you measure "availability" for an HTTP API as an SLI? What are the pitfalls?

**Answer:**  
**SLI**: **successful** requests / **total** requests (e.g. **status** 2xx, 3xx = success); **over** a **window** (e.g. 30 days, 1 min). **Pitfalls**: **synthetic** vs **real** traffic; **exclude** **client** errors (4xx) if SLO is **server** availability; **health** endpoint vs **real** path; **sampling** (use **all** or **representative**). **Define** clearly: e.g. "availability = 1 - (5xx count / total count) over 30d".

---

## Q6. (Intermediate) What is the relationship between SLO and alerting? Why not alert on SLO breach directly?

**Answer:**  
**Alert** when **approaching** or **breaching** SLO (e.g. **error budget** burn rate **high**). **Don’t** only alert **on** breach: **too late** (user impact). **Alert** on **burn rate** (e.g. "budget will be exhausted in 4h at current rate") or **window** SLO (e.g. "availability last 1h < 99.9%"). **Action**: **page** when **actionable** (e.g. rollback, scale); **dashboard** for SLO/error budget.

---

## Q7. (Intermediate) A service has SLO 99.9% availability. It has been at 99.95% for the month. What does that mean for the team?

**Answer:**  
**99.95%** is **better** than **99.9%**; **within** SLO; **error budget** **not** exhausted (we have **surplus**). **Meaning**: team can **spend** budget (e.g. **riskier** release, **experiments**) or **keep** surplus for **next** period. **No** need to **freeze**; **optional** to **relax** next sprint or **keep** buffer.

---

## Q8. (Intermediate) How do you choose a reasonable SLO (e.g. 99.9% vs 99.99%)? What are the tradeoffs?

**Answer:**  
**Higher** SLO = **less** allowed downtime; **more** **investment** (redundancy, on-call, testing). **99.9%** = ~43 min/month; **99.99%** = ~4.3 min/month. **Choose**: **user** expectation; **dependency** SLOs (can’t be more than dependency); **cost** of **improvement**. **Start** with **measured** baseline (e.g. current 99.5%) then **improve**; **don’t** promise **99.99%** without **investment**.

---

## Q9. (Intermediate) What is a burn-rate alert? How does it help with SLO-based alerting?

**Answer:**  
**Burn rate**: **how fast** error budget is **consumed** (e.g. **error rate** vs **SLO**). **Example**: **fast** burn = 10× normal → budget gone in **hours**. **Alert**: **short** window (e.g. 1h) **high** burn → **page**; **long** window (e.g. 6h) **moderate** burn → **ticket**. **Result**: **catch** **incidents** **early** (before 30d SLO breach) and **reduce** **noise** (single spike may not breach 30d).

---

## Q10. (Intermediate) How do you expose SLI metrics (e.g. request count and errors) from an application for Prometheus?

**Answer:**  
**Instrument**: **counters** **http_requests_total** (labels: status, method); or **histogram** **http_request_duration_seconds**. **Prometheus** **client** (e.g. **prom_client** in Node.js): **increment** on each request; **observe** duration. **Expose**: **/metrics** endpoint; Prometheus **scrapes**. **SLO** query: `rate(http_requests_total{status=~"5.."}[30d]) / rate(http_requests_total[30d])` for **error ratio**.

---

## Q11. (Advanced) Production scenario: Your API has SLO 99.9% availability. Error budget is exhausted halfway through the month. What actions should the team take?

**Answer:**  
(1) **Communicate**: **announce** budget **exhausted**; **freeze** or **reduce** **risk** (no **major** releases, no **experiments**). (2) **Focus** on **reliability**: **fix** known issues, **improve** monitoring, **reduce** **incidents**. (3) **Post-mortems**: **root cause** of **outages**; **remediation**. (4) **Re-evaluate** **SLO**: was it **realistic**? **Extend** window or **adjust** next quarter. (5) **Don’t** **blame**; **blameless** review and **improve** process. **Senior**: "We’d freeze non-essential feature work, focus on reliability and post-mortems, and decide whether to extend the window or accept a breach and improve for next period."

---

## Q12. (Advanced) How do you define SLIs for a dependency (e.g. database or cache)? Why does it matter?

**Answer:**  
**Dependency SLI**: **latency** and **availability** of **calls** to that dependency (e.g. **DB** query latency, **cache** hit rate). **Measure**: **client-side** (from app) or **exporter** (e.g. Redis exporter). **Matters**: **your** SLO **can’t** be **better** than **dependency**; **cascades** (DB down → API down). **Use**: **negotiate** **SLA** with dependency owner; **circuit breaker** and **fallback** when **dependency** degrades.

---

## Q13. (Advanced) What is multi-window multi-burn-rate alerting (Google SRE)? Explain briefly.

**Answer:**  
**Idea**: **two** **windows** (e.g. 1h and 6h) and **two** **burn rates** (e.g. **fast** = 14.4×, **slow** = 1). **Alert**: **page** when **fast** burn for **short** window (immediate **incident**); **ticket** when **slow** burn for **long** window (**sustained** degradation). **Reduces** **noise** (single blip may not fire) and **catches** **both** **acute** and **chronic** SLO impact. **Implementation**: **Prometheus** **recording** rules for **burn rate**; **alert** rules with **for** and **thresholds**.

---

## Q14. (Advanced) Production scenario: You have 10 microservices; each has its own SLO. How do you set SLOs for the "user journey" (e.g. checkout) that spans 5 of them?

**Answer:**  
**User journey** **availability** ≈ **product** of **availabilities** (if **sequential** and **critical**): e.g. A × B × C × D × E. If each is **99.9%**, product ≈ **99.5%**. **Options**: (1) **Tighten** **per-service** SLO so **product** meets **journey** target. (2) **Define** **journey** SLI (e.g. **synthetic** or **real** "checkout success"); **SLO** on that; **allocate** **error budget** to **services**. (3) **SLO** per service for **ownership**; **synthetic** **journey** for **E2E** monitoring. **Tradeoff**: **per-service** = clear **ownership**; **journey** = **user**-centric.

---

## Q15. (Advanced) How do you implement "release only when error budget allows" in a pipeline?

**Answer:**  
**Gate**: **CI** step that **queries** **error budget** (e.g. from **Prometheus** or **SLO** service). **If** **remaining** budget **>** threshold (e.g. **> 0** or **> 10%**), **proceed**; **else** **block** or **require** **approval**. **Implementation**: **script** or **plugin** that **calls** API (e.g. **Sloth**, **Prometheus**); **fail** pipeline if budget **exhausted**. **Override**: **manual** approval for **critical** hotfix. **Result**: **releases** **automatically** **paused** when **reliability** is at risk.

---

## Q16. (Advanced) What is the difference between availability and latency SLOs? Can you have both?

**Answer:**  
**Availability**: **fraction** of **successful** (or **non-error**) requests. **Latency**: **percentile** (e.g. p99 < 200ms). **Both**: **yes**; **separate** SLIs and SLOs (e.g. 99.9% **availability** and p99 **latency** < 200ms). **Alert** on **both**; **error budget** can be **per** SLO or **combined** (e.g. **breach** either = budget consumed). **Common**: **availability** + **latency** (and sometimes **quality** or **throughput**).

---

## Q17. (Advanced) How do you report SLO compliance to stakeholders (e.g. monthly)?

**Answer:**  
(1) **Dashboard**: **Grafana** (or similar) with **SLO** **panels** (availability, latency, **error budget** remaining). (2) **Report**: **monthly** **summary** — **actual** vs **SLO**; **budget** **consumed**; **incidents** and **remediation**. (3) **Data**: **export** from **Prometheus** (e.g. **recording** rules for **30d** availability); **spreadsheet** or **doc**. (4) **Automate**: **script** or **tool** (e.g. **Sloth** report) that **generates** **report** from **metrics**. **Stakeholders**: **exec** summary (met/not met); **engineering** (trends, actions).

---

## Q18. (Advanced) Production scenario: SLO is 99.9% but we measure 99.7% (breach). Post-incident, how do you prevent recurrence and handle the error budget policy?

**Answer:**  
(1) **Post-mortem**: **root cause**; **actions** (fix, **monitoring**, **testing**). (2) **Prevent**: **remediation** items; **improve** **detection** (burn-rate alert); **test** **failure** modes (chaos). (3) **Policy**: **spend** next period **replenishing** (e.g. **freeze** features until **surplus**); or **formal** **review** before **next** **risk** (release). (4) **Communicate**: **internal** and **external** (if **SLA**) per policy; **credits** if **SLA**. (5) **Re-evaluate** **SLO**: **realistic**? **Dependencies**? **Adjust** or **invest** in **reliability**.

---

## Q19. (Advanced) What is an SLI backend (e.g. Prometheus + recording rules)? How do you compute "availability over last 30 days"?

**Answer:**  
**Backend**: **Prometheus** (or **similar**) **stores** **raw** metrics; **recording** rules **compute** **aggregates** (e.g. **rate**, **ratio**). **30d availability**: **ratio** of **success** **rate** to **total** **rate** over **30d** window. **Prometheus**: `sum(rate(http_requests_total{status!~"5.."}[30d])) / sum(rate(http_requests_total[30d]))`. **Recording** rule: **precompute** per **service** for **fast** **dashboards** and **alerts**. **Limitation**: **30d** window is **heavy**; use **recording** rules with **appropriate** resolution.

---

## Q20. (Advanced) Senior red flags to avoid with SLOs

**Answer:**  
- **SLO** without **measurement** (no SLI).  
- **Alerting** only on **breach** (too late).  
- **Ignoring** **error budget** (no **policy**).  
- **Unrealistic** SLO (e.g. 100% or **better** than **dependencies**).  
- **No** **review** or **reporting** (SLO forgotten).  
- **Blaming** when **budget** exhausted (blameless **post-mortem**).  
- **No** **automation** (release gate, dashboards).  
- **SLO** for **everything** (focus on **critical** user paths).

---

**Tradeoffs:** Startup: one availability SLO, basic alert. Medium: availability + latency, error budget, dashboard. Enterprise: multi-window burn rate, release gate, reporting, journey SLOs.
