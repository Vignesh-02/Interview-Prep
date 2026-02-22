# 24. Observability (X-Ray, ServiceLens) — Senior

## Q1. (Beginner) What is AWS X-Ray? What does it provide?

**Answer:**  
**X-Ray** is **distributed tracing**: it records **requests** as they flow through **multiple services** (Lambda, API Gateway, EC2, etc.); you see a **trace** (tree of segments) with **latency** per segment and **errors**. **Provides**: service map, trace list, segment details (subsegments for DB, HTTP). Use to find **bottlenecks** and **errors** in a multi-service flow.

---

## Q2. (Beginner) How do you enable X-Ray for a Lambda function?

**Answer:**  
(1) **Active tracing** in Lambda: set **TracingConfig** (Mode = Active) on the function (console, CLI, or CloudFormation). (2) Lambda **automatically** creates segments and sends to X-Ray; **no code change** for basic tracing. (3) **IAM**: Lambda execution role needs `xray:PutTraceSegments` and `xray:PutTelemetryRecords`. (4) **Downstream**: if Lambda calls another service (e.g. DynamoDB), SDK can add **subsegments** (AWS SDK with X-Ray SDK wrapper or automatic in some runtimes).

---

## Q3. (Intermediate) What is a trace segment vs subsegment? How do you add a custom subsegment in code?

**Answer:**  
**Segment**: one **service** (e.g. one Lambda invocation). **Subsegment**: part of that segment (e.g. DynamoDB call, custom block). **Custom subsegment** (Node.js): use **AWS X-Ray SDK** — `const segment = AWSXRay.getSegment(); const subsegment = segment.addNewSubsegment('my-operation'); subsegment.close();` (or async with callback). **Python**: `xray_recorder.begin_subsegment('my-operation')` / `end_subsegment()`. Use for **custom** logic (e.g. “validate”, “transform”) to see where time is spent.

---

## Q4. (Intermediate) What is CloudWatch ServiceLens? How does it combine X-Ray and CloudWatch?

**Answer:**  
**ServiceLens** (in CloudWatch): **unified** view of **metrics**, **logs**, and **traces**. You see **service map** (X-Ray) and can **drill** into a service to see **CloudWatch metrics** and **logs** for the same time range; **correlate** by trace ID or request ID. **Use**: when debugging — “this trace failed; show me logs and metrics for this service during this trace.” Combines X-Ray traces with Logs Insights and metrics in one place.

---

## Q5. (Intermediate) Production scenario: Your API (API Gateway → Lambda → RDS) has 5xx errors. How do you use X-Ray and CloudWatch to find whether the failure is in Lambda or RDS?

**Answer:**  
(1) **X-Ray**: open **Service map** or **Traces**; filter by **Error = true**. Open a **failed trace**; see **segment** tree — which segment has **error** or **throttle** (e.g. Lambda or RDS subsegment). (2) **Segment details**: check **subsegments** (e.g. RDS query) for **fault** or **high duration**. (3) **CloudWatch Logs**: use **trace ID** (in X-Ray) to search **Logs Insights** for that request; see exception in Lambda logs. (4) **RDS**: check **Performance Insights** or **slow query** if segment shows RDS. **Result**: pinpoint which service and often which call failed.

---

## Q6. (Advanced) How do you propagate trace context (trace ID, segment ID) from API Gateway through Lambda to another Lambda or HTTP service?

**Answer:**  
**X-Ray SDK** (and Lambda integration) **automatically** adds **trace header** (`X-Amzn-Trace-Id` or `traceparent`) to **outgoing** requests (HTTP or AWS SDK). **Downstream** service (Lambda or app) that uses X-Ray **reads** the header and **continues** the trace (same trace ID, new segment). **Manual**: pass **trace ID** in header or payload; downstream starts segment with that trace ID (X-Ray SDK supports this). **Best**: use **X-Ray SDK** in all services; propagation is automatic for supported clients.

---

## Q7. (Advanced) What is the difference between sampling in X-Ray (rule-based) and always-on? When would you use each?

**Answer:**  
**Sampling**: only a **percentage** of requests are traced (e.g. 1 req/s + 5% additional); reduces **cost** and **overhead**. **Always-on** (100%): every request traced; full visibility, higher cost. **Use sampling** for **high-traffic** production (e.g. 5% or 1 req/s); use **always-on** for **low traffic** or **debugging** (temporarily). **Reserve** (rule): guarantee minimum rate (e.g. 1/s) then sample above that. **Central** sampling rules (account-level) apply to all services.

---

## Q8. (Advanced) Production scenario: You have 20 microservices (Lambda, ECS). You want one place to see “where did this request fail?” and “what is the p99 latency per service?” How do you design observability?

**Answer:**  
(1) **X-Ray** on **all** services (Lambda active tracing; ECS with X-Ray daemon or SDK); **consistent** sampling (e.g. 5%). (2) **Service map** and **traces** answer “where did it fail?” (3) **CloudWatch ServiceLens** for **correlation** (trace → logs, metrics). (4) **Metrics**: **custom** metric per service (e.g. duration) with dimension **ServiceName**; or use **X-Ray analytics** (group by service, p99). (5) **Dashboard**: CloudWatch dashboard with **p99 by service** (from X-Ray or custom metrics). (6) **Alarms**: per-service error rate and p99; **SNS** to Slack/PagerDuty. **Result**: one place (ServiceLens + dashboard) for “where failed” and “p99 per service.”

---

## Q9. (Advanced) Compare observability for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: **CloudWatch** (logs, basic metrics); **X-Ray** on critical path; one dashboard; email alerts. **Medium**: **X-Ray** on all services; **ServiceLens**; **structured logs** and **request ID**; alarms per service. **Enterprise**: **centralized** logging (cross-account); **trace** and **metric** retention; **SLO/SLI** and error budget; **runbooks**; **integration** with PagerDuty/incident management; compliance (audit, retention).

---

## Q10. (Advanced) Senior red flags to avoid in observability

**Answer:**  
- **No tracing** (only logs; hard to see full request path).  
- **Checking console** only when something breaks (use alarms).  
- **No correlation** (request ID, trace ID) across logs and services.  
- **Logging** sensitive data (passwords, tokens).  
- **100% sampling** at very high traffic (cost and overhead).  
- **No runbook** when alarm fires.  
- **Ignoring** p99 or error rate (only watching average).  
- **No retention** policy (logs/traces grow forever, cost).

---

**Tradeoffs:** Startup: X-Ray on main path, CloudWatch. Medium: X-Ray everywhere, ServiceLens. Enterprise: centralized logs, SLOs, runbooks.
