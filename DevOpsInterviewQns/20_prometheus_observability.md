# 20. Prometheus & Observability

## Q1. (Beginner) What is Prometheus? What is the pull model?

**Answer:**  
**Prometheus**: **metrics** **DB** + **scraping** + **alerting**. **Pull**: Prometheus **scrapes** **targets** (HTTP **/metrics**) at **interval**; **targets** don’t **push**. **Contrast**: **push** (e.g. **StatsD**) = **app** **sends** to **collector**. **Pull** = **simpler** **targets**; **Prometheus** **controls** **scrape**; **discovery** (e.g. **K8s**) **finds** **targets**.

---

## Q2. (Beginner) What is a metric type in Prometheus? Name the four types.

**Answer:**  
**Counter**: **monotonically** **increasing** (requests **total**, **errors** **total**). **Gauge**: **value** that **goes** **up/down** (memory **usage**, **active** **connections**). **Histogram**: **buckets** + **count** + **sum** (e.g. **latency** **distribution**). **Summary**: **client-side** **quantiles** (e.g. p99). **Use** **histogram** for **latency** in **Prometheus** (query **quantiles** with **histogram_quantile**).

---

## Q3. (Beginner) What is a label? Why are labels important?

**Answer:**  
**Label**: **dimension** on a **metric** (e.g. **method**, **status**, **pod**). **Query** and **group** by **label**; **aggregate** across **instances**. **Important**: **filter** (e.g. **errors** by **env**); **join** (e.g. **rate** by **job**); **cardinality** (don’t **over-label** — **high** **cardinality** = **memory** **blow-up**).

---

## Q4. (Beginner) What is the PromQL query to get request rate per second for the last 5 minutes?

**Answer:**  
**rate(http_requests_total[5m])** — **per-second** **rate** of **counter** over **5m** **window**. **By** **path**: **rate(http_requests_total[5m])** **by** **(path)**. **Sum** **all**: **sum(rate(http_requests_total[5m]))**.

---

## Q5. (Intermediate) How do you expose metrics from a Node.js app for Prometheus?

**Answer:**  
**Library**: **prom-client** (or **similar**). **Create** **registry**; **Counter** **http_requests_total** (labels: **method**, **path**, **status**); **Histogram** **http_request_duration_seconds**; **increment**/observe in **middleware**. **Expose**: **GET** **/metrics** returning **text** format. **Example**:
```js
const { Counter, register } = require('prom-client');
const counter = new Counter({ name: 'http_requests_total', help: '...', labelNames: ['method', 'path', 'status'] });
// in handler: counter.labels(req.method, req.path, res.statusCode).inc();
app.get('/metrics', (req, res) => { res.setHeader('Content-Type', register.contentType); res.end(register.metrics()); });
```

---

## Q6. (Intermediate) What is a recording rule? Why use it?

**Answer:**  
**Recording** **rule**: **precompute** **PromQL** and **store** as **new** **metric** (in **same** **Prometheus** or **query** **layer**). **Use**: **expensive** **queries** (e.g. **rate** over **30d**); **dashboard** **speed**; **alert** on **precomputed** **metric**. **Config**: **rule_files** with **groups**; **record**: **name**; **expr**: **PromQL**.

---

## Q7. (Intermediate) What is an alerting rule? What is the difference between Alertmanager and Prometheus alert rules?

**Answer:**  
**Alert** **rule**: **PromQL** **condition**; **when** **true** → **fire** **alert** (sent to **Alertmanager**). **Prometheus**: **evaluates** **rules**; **sends** **firing** **alerts** to **Alertmanager**. **Alertmanager**: **dedupe**, **group**, **route**, **silence**; **sends** **notifications** (Slack, PagerDuty). **Prometheus** = **when** to **alert**; **Alertmanager** = **where** and **how** to **notify**.

---

## Q8. (Intermediate) How do you compute error rate (e.g. 5xx / total) in PromQL?

**Answer:**  
**rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])** — **ratio** of **5xx** **rate** to **total** **rate**. **Or** **sum** by **job**: **sum(rate(...{status=~"5.."}[5m])) by (job) / sum(rate(...[5m])) by (job)**.

---

## Q9. (Intermediate) What is service discovery in Prometheus? Give one example (e.g. Kubernetes).

**Answer:**  
**Service** **discovery**: **automatically** **find** **targets** (no **static** **config**). **Kubernetes**: **kubernetes_sd_config** — **discover** **pods**, **services**, **nodes**; **relabel** to **set** **__address__**, **labels** (pod, **namespace**). **Other**: **ec2**, **consul**, **dns**. **Result**: **new** **pods** **scraped** **automatically**.

---

## Q10. (Intermediate) What is the difference between rate() and irate()?

**Answer:**  
**rate()**: **average** **per-second** **rate** over **window**; **smooths** **spikes**. **irate()**: **instant** **rate** from **last** **two** **samples**; **more** **reactive** to **short** **spikes** but **can** **miss** **trend**. **Use** **rate** for **alerting** and **dashboards** (stable); **irate** for **very** **short** **spikes** (e.g. **debug**).

---

## Q11. (Advanced) Production scenario: You need SLO alerting (e.g. 99.9% availability). How do you implement burn-rate alerting?

**Answer:**  
**Burn rate** = **how fast** **error** **budget** is **consumed**. **Recording** **rules**: **error** **rate** and **SLO** **ratio**; **burn** **rate** = **error_rate / (1 - SLO)** (e.g. **14.4** = **fast** **burn**). **Alert**: **short** **window** (1h) **fast** **burn** → **page**; **long** **window** (6h) **slow** **burn** (1×) → **ticket**. **PromQL** example: **rate(errors[1h]) / rate(total[1h]) > 0.00144** (for **99.9%** **SLO** **fast** **burn**). **Multi-window** **multi-burn** = **fewer** **false** **positives**; **catch** **incidents** **early**.

---

## Q12. (Advanced) How do you monitor a service that runs in multiple regions and aggregate metrics?

**Answer:**  
**Label** **region** (or **datacenter**) on **metrics** (scrape **config** or **app** **labels**). **Aggregate**: **sum(rate(...[5m])) by (region)** for **per-region**; **sum(rate(...[5m]))** for **global**. **Federation** or **Thanos**/Cortex if **multiple** **Prometheus** **per** **region** ( **aggregate** at **query** **time**). **Dashboards**: **panel** per **region** + **global** **sum**.

---

## Q13. (Advanced) What is high cardinality? How does it affect Prometheus and how do you avoid it?

**Answer:**  
**High** **cardinality**: **many** **unique** **label** **combinations** (e.g. **user_id**, **request_id**). **Effect**: **memory** **and** **disk** **blow-up**; **slow** **queries**. **Avoid**: **don’t** **label** by **unbounded** **values** (user **id**, **trace** **id**); **use** **bounded** **labels** (status, **path** **template**, **env**). **Logs**/traces for **per-request** **detail**; **metrics** for **aggregates**.

---

## Q14. (Advanced) Production scenario: Alerts are noisy (many false positives). How do you reduce noise?

**Answer:**  
(1) **Tune** **thresholds** (e.g. **higher** **duration** **for** **for** **clause**). (2) **Burn-rate** **style** (multi-window) **instead** of **single** **threshold**. (3) **Alertmanager** **grouping** and **inhibition** (e.g. **down** **instance** **inhibits** **high** **error** **rate** for that **instance**). (4) **Silence** **known** **maintenance**. (5) **Runbook** and **auto-remediation** so **only** **actionable** **alerts** **page**. (6) **Review** **alert** **logic** (alert on **symptom** user **cares** about, not **every** **anomaly**).

---

## Q15. (Advanced) How do you achieve long-term retention and global view (e.g. Thanos, Cortex)?

**Answer:**  
**Thanos**: **sidecar** **uploads** **blocks** to **object** **store**; **Querier** **queries** **Prometheus** + **store**; **long** **retention** **cheap**. **Cortex**: **remote** **write** from **Prometheus** to **Cortex**; **Cortex** **stores** in **object** **store**; **multi-tenancy**. **Result**: **weeks/months** **retention**; **multi-cluster** **query**; **same** **PromQL**.

---

## Q16. (Advanced) What is the RED method? How do you implement it in Prometheus?

**Answer:**  
**RED**: **Rate** (requests/sec), **Errors** (error **rate**), **Duration** (latency **distribution**) per **service**. **Implement**: **Counter** **requests_total** (labels: **status**); **Histogram** **request_duration_seconds**; **PromQL**: **rate(requests_total[5m])**, **rate(requests_total{status=~"5.."}[5m])/rate(requests_total[5m])**, **histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))**. **Dashboard** one **panel** per **R**, **E**, **D**.

---

## Q17. (Advanced) How do you secure Prometheus (auth, TLS, RBAC)?

**Answer:**  
**Scrape** **TLS**: **scheme: https** and **tls_config** (e.g. **insecure_skip_verify** or **ca**). **Auth**: **Prometheus** **doesn’t** **auth** **scrape** by default; **targets** can **require** **auth** (e.g. **bearer** **token** in **scrape** **config** **authorization**). **UI/API**: **reverse** **proxy** with **auth** (e.g. **OAuth**); **Grafana** for **read** with **auth**. **RBAC**: **Grafana** **roles**; **Prometheus** **read** **restricted** by **network**/proxy. **Alertmanager**: **same** (proxy + **auth**).

---

## Q18. (Advanced) What is the USE method? When do you use it vs RED?

**Answer:**  
**USE**: **Utilization**, **Saturation**, **Errors** (for **resources** — CPU, **disk**, **network**). **Use** **USE** for **infra** (nodes, **disks**); **RED** for **services** (requests). **Prometheus**: **node_cpu_seconds_total** → **utilization**; **saturation** = **queue** or **wait** **time**; **errors** = **device** **errors**. **Dashboard** **USE** for **hosts**; **RED** for **APIs**.

---

## Q19. (Advanced) How do you run Prometheus in Kubernetes (Deployment, ConfigMap, ServiceMonitor)?

**Answer:**  
**Deploy** **Prometheus**: **Deployment** + **ConfigMap** (prometheus.yml); **PVC** for **storage**; **Service**. **ServiceMonitor** (Prometheus **Operator**): **CRD** that **selects** **Services** and **generates** **scrape** **config**; **Prometheus** **discovers** **ServiceMonitors**. **RBAC**: **ServiceAccount** with **list** **pods**/services. **Alternative**: **static** **config** or **annotations** on **Services** for **scrape** **discovery** (non-operator).

---

## Q20. (Advanced) Senior red flags to avoid with Prometheus and observability

**Answer:**  
- **High** **cardinality** **labels** (user_id, **request_id**).  
- **Alert** on **everything** (noise; **alert** on **user** **impact**).  
- **No** **recording** **rules** for **heavy** **queries** (slow **dashboards**).  
- **No** **runbook** or **playbook** for **alerts**.  
- **Short** **retention** with **no** **long-term** **store** (can’t **investigate** **past**).  
- **Scraping** **sensitive** **paths** without **auth**.  
- **No** **SLO**/error **budget** (only **ad-hoc** **thresholds**).  
- **Metrics** **only** (no **logs**/traces for **debug**).

---

**Tradeoffs:** Startup: single Prometheus, basic alerts. Medium: recording rules, Alertmanager, Grafana. Enterprise: Thanos/Cortex, SLO/burn-rate, multi-region, RBAC.
