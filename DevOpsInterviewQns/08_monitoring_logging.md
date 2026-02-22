# 8. Monitoring & Logging Basics

## Q1. (Beginner) What is the difference between metrics and logs? Give one example of each.

**Answer:**  
**Metrics**: **numeric** values over **time** (e.g. request rate, CPU %, error count). **Logs**: **events** or **text** (e.g. "User login failed", stack trace). **Use**: metrics for **dashboards** and **alerts**; logs for **debugging** and **audit**. **Example**: metric = `http_requests_total`; log = "ERROR: connection refused to DB".

---

## Q2. (Beginner) What is a time-series metric? What are common dimensions (labels)?

**Answer:**  
**Time-series**: **value** at each **timestamp**; often **named** and **tagged**. **Dimensions/labels**: **host**, **service**, **env**, **status_code**, **method**. **Example**: `http_requests_total{service="api", status="200"}`. **Use** dimensions for **filtering** and **grouping** (e.g. errors by service).

---

## Q3. (Beginner) What is the RED method for monitoring? What does each letter stand for?

**Answer:**  
**RED**: for **request-driven** (e.g. HTTP) services. **R**ate (requests per second), **E**rrors (error rate), **D**uration (latency, e.g. p50, p99). **Use**: **alerts** and **dashboards** on these three. **Alternative**: **USE** (Utilization, Saturation, Errors) for **resources** (CPU, disk).

---

## Q4. (Beginner) What is structured logging? Why prefer it over plain text?

**Answer:**  
**Structured**: **key-value** or **JSON** (e.g. `{"level":"error","msg":"db failed","err":"timeout"}`). **Benefits**: **query** by field (level, service); **aggregate** (count by error type); **parse** in log aggregators. **Plain text** is harder to parse and query. **Prefer** JSON or key-value for production.

---

## Q5. (Intermediate) How do you calculate and alert on "error rate" (e.g. 5xx / total requests)? What metric type do you need?

**Answer:**  
**Need**: **counter** (or rate) for **requests_total** and **errors_total** (or 5xx). **Error rate** = rate(errors_total) / rate(requests_total) over a **window** (e.g. 5 min). **Alert**: error rate **>** 0.01 (1%). **Prometheus**: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01`. **Export**: app or **exporter** exposes these counters.

---

## Q6. (Intermediate) What is a log aggregation system? Name two and their typical role.

**Answer:**  
**Aggregation**: **collect**, **store**, **search** logs from many sources. **ELK** (Elasticsearch, Logstash, Kibana): **Elasticsearch** = store/search; **Logstash** (or Beats) = ingest; **Kibana** = UI. **Loki**: **like** Prometheus for logs (label-based); **Grafana** for query. **Cloud**: CloudWatch Logs, Datadog. **Role**: **central** place to **search** and **alert** on logs.

---

## Q7. (Intermediate) What is the difference between push and pull for collecting metrics? Which does Prometheus use?

**Answer:**  
**Pull**: **collector** (e.g. Prometheus) **scrapes** targets (HTTP endpoint) at **interval**. **Push**: **targets** **push** to collector (e.g. StatsD, push gateway). **Prometheus**: **pull** (scrape). **Use push** for **short-lived** jobs (batch) or **firewall** where pull is hard; **push gateway** or **remote write** for that.

---

## Q8. (Intermediate) How do you avoid logging sensitive data (passwords, tokens) in application code? What do you do if it was logged?

**Answer:**  
**Prevent**: **never** log **passwords**, **tokens**, **PII**; use **placeholders** ("password=***"); **sanitize** in logging **library** (redact known keys). **If logged**: **rotate** secret **immediately**; **redact** or **delete** from log storage if possible; **restrict** access to logs; **audit** who accessed. **Structured** logs: redact **sensitive** keys before write.

---

## Q9. (Intermediate) What is an alert fatigue? How do you reduce it?

**Answer:**  
**Alert fatigue**: **too many** or **noisy** alerts → ignored. **Reduce**: (1) **Fewer** alerts — only **actionable** (someone can fix). (2) **Thresholds** and **windows** (e.g. 5 min sustained). (3) **Severity** (page vs slack). (4) **Dedupe** and **group**. (5) **Runbooks** so response is clear. (6) **Tune** to reduce false positives; **review** and **disable** useless alerts.

---

## Q10. (Intermediate) Write a simple Prometheus alert rule that fires when the instance is down (e.g. up == 0) for more than 2 minutes.

**Answer:**
```yaml
groups:
- name: example
  rules:
  - alert: InstanceDown
    expr: up == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Instance {{ $labels.instance }} down"
```
**up** is 1 if scrape succeeded, 0 if not. **for** = fire only after 2m to avoid flapping.

---

## Q11. (Advanced) Production scenario: You have 50 microservices; logs are on each host and in containers. How do you design a centralized logging system so logs are searchable and you can trace a request across services?

**Answer:**  
(1) **Collect**: **agent** on host or in **sidecar** (e.g. Fluent Bit, Filebeat) that **tails** log files or **stdout**; **forward** to **central** (Elasticsearch, Loki, or cloud). (2) **Correlation**: **request_id** (or trace_id) in **every** log line (same value across services); **structured** log with `request_id`, `service`, `level`. (3) **Search**: query by **request_id** to get **all** logs for that request across services. (4) **K8s**: **sidecar** or **daemonset**; **stdout** → agent → central. **Tradeoff**: Startup = single host or cloud logs; enterprise = central cluster, retention, access control.

---

## Q12. (Advanced) What is the USE method? When would you use RED vs USE?

**Answer:**  
**USE**: **U**tilization (%), **S**aturation (queue/wait), **E**rrors (e.g. disk errors). **Use** for **resources** (CPU, memory, disk, network). **RED** for **request** services (HTTP, RPC). **Combine**: **RED** for APIs; **USE** for **nodes** and **disks**; **both** on one dashboard for full picture.

---

## Q13. (Advanced) How do you implement "log sampling" at high volume so you don't store every log line but still capture errors?

**Answer:**  
(1) **Sample** by level: **100%** of **error** and **warn**; **10%** (or 1%) of **info**; **0%** of **debug**. (2) **Config** in app or in **agent** (Fluent Bit: sample filter). (3) **Dynamic**: increase **sample** rate when **error** rate spikes. (4) **Result**: **full** errors for debugging; **reduced** volume and cost; **metrics** (counts) can still be **full** if exported separately.

---

## Q14. (Advanced) Production scenario: Alerts are firing for "high error rate" but the app team says the app is healthy. How do you validate and avoid false positives?

**Answer:**  
(1) **Validate**: **dashboard** — same metric and **time** window; **logs** — sample of "errors" (might be **4xx** client errors, not 5xx). (2) **Tune**: **exclude** 4xx from "error" rate if **SLO** is for 5xx; or **separate** alert for 5xx vs 4xx. (3) **Threshold**: raise or add **for** clause (e.g. 5 min). (4) **Document**: **runbook** and **definition** of "error". (5) **Feedback**: **post-incident** review to adjust alert. **Senior**: "I’d check if the metric matches what we care about — e.g. 5xx only — and whether the threshold and window are right; then add a runbook."

---

## Q15. (Advanced) What is a golden signal? Name them and give one example metric per signal for a web API.

**Answer:**  
**Golden signals** (Google SRE): **Latency** (e.g. p99 response time), **Traffic** (requests/sec), **Errors** (5xx rate), **Saturation** (how full the service is — e.g. queue depth, CPU). **Web API**: **latency** = histogram `http_request_duration_seconds`; **traffic** = `rate(http_requests_total[5m])`; **errors** = `rate(http_requests_total{status=~"5.."}[5m])`; **saturation** = CPU or connection pool usage.

---

## Q16. (Advanced) How do you monitor a batch job (e.g. nightly ETL) that doesn't expose an HTTP endpoint?

**Answer:**  
(1) **Push metrics**: job **pushes** to **Pushgateway** (Prometheus) or **writes** to **StatsD** at **end** (duration, status, rows). (2) **Scrape** Pushgateway from Prometheus. (3) **Alert**: **no** successful run in **25h** (e.g. `time() - last_success_timestamp > 90000`) or **failure** count. (4) **Logs**: send **completion** log to central; **alert** if no log by 6 AM. (5) **Orchestrator** (Airflow, etc.) can **emit** metrics or **webhook** on success/failure.

---

## Q17. (Advanced) What is the difference between black-box and white-box monitoring? When would you use each?

**Answer:**  
**Black-box**: **external** probe (e.g. HTTP from outside); **user** perspective; **does** the endpoint respond? **White-box**: **internal** metrics (CPU, queue depth, errors from app). **Use**: **black-box** for **availability** and **UX**; **white-box** for **cause** (why slow, what failed). **Both**: black-box to **alert** "down"; white-box to **debug** and **trend**.

---

## Q18. (Advanced) Production scenario: Log volume is 1 TB/day; storage cost is high. Propose retention, sampling, and archival strategy.

**Answer:**  
(1) **Retention**: **hot** (searchable) **7–30** days; **warm** (cheaper, slower) **30–90**; **cold** (archive, e.g. S3/Glacier) **1–7 years** for compliance. (2) **Sampling**: **100%** errors; **10%** info; **0%** debug after 24h. (3) **Archive**: **export** from Elasticsearch/Loki to **S3**; **lifecycle** to Glacier; **delete** from hot after export. (4) **Index** only needed **fields**; **curate** what is indexed. **Result**: lower **hot** storage and cost; **full** errors; **archived** for audit.

---

## Q19. (Advanced) How do you correlate logs with traces (distributed tracing)? What fields should be in every log line?

**Answer:**  
**Trace**: **trace_id** (and **span_id**) from tracing system (Jaeger, Zipkin). **Logs**: **same trace_id** (and span_id) in **every** log line (structured field). **Query**: by **trace_id** in log store to get **all** logs for that request; **link** from trace UI to logs. **Fields**: `trace_id`, `span_id`, `service`, `level`, `message`, `timestamp`. **App**: **middleware** injects trace_id into logger context.

---

## Q20. (Advanced) Senior red flags to avoid in monitoring/logging

**Answer:**  
- **No** alerts for **errors** or **latency**.  
- **Alerting** on **everything** (alert fatigue).  
- **Logging** secrets or **PII**.  
- **No** **request_id** or **trace_id** (can’t trace).  
- **Only** black-box (no white-box to debug).  
- **No** retention or **archival** (cost and compliance).  
- **Unstructured** logs at scale (hard to query).  
- **Ignoring** log volume and **sampling** (cost explosion).

---

**Tradeoffs:** Startup: basic metrics + log files. Medium: central logs, RED metrics, few alerts. Enterprise: retention, sampling, tracing, runbooks, SLOs.
