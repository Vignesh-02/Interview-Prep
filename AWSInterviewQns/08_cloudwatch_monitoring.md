# 8. CloudWatch & Monitoring

## Q1. (Beginner) What is CloudWatch? What are metrics, logs, and alarms?

**Answer:**  
**CloudWatch** is AWS monitoring and observability: **Metrics** — numeric data (CPU, custom); **Logs** — log groups/streams (e.g. Lambda, app logs); **Alarms** — trigger when a metric crosses a threshold (notify or act). Use for health, performance, and alerting.

---

## Q2. (Beginner) How do you send a custom metric from an EC2 instance or Lambda to CloudWatch?

**Answer:**  
**PutMetricData** API (or SDK). **Lambda**: use `cloudwatch.putMetricData()` with namespace (e.g. MyApp), metric name, value, dimensions (e.g. env=prod). **EC2**: same from app, or install **CloudWatch agent** to push system metrics and log files. **Example (Node.js)**: `await cw.putMetricData({ Namespace: 'MyApp', MetricData: [{ MetricName: 'OrdersCreated', Value: 1, Unit: 'Count', Dimensions: [{ Name: 'Env', Value: 'prod' }] }] });`

---

## Q3. (Intermediate) What is a CloudWatch Alarm? What actions can it take when it fires?

**Answer:**  
**Alarm** evaluates a metric (e.g. CPU > 80%) over a period and number of datapoints. **Actions**: (1) **SNS** topic (email, SMS, Lambda, etc.). (2) **Auto Scaling** (scale in/out). (3) **EC2** (stop/terminate/reboot). (4) **EventBridge** (custom automation). Define **OK / Alarm / Insufficient data** states; use **composite alarms** to combine multiple alarms.

---

## Q4. (Intermediate) Your Lambda writes logs with console.log. Where do they go and how do you search them?

**Answer:**  
Lambda **automatically** sends stdout/stderr to **CloudWatch Logs** in a log group per function (e.g. /aws/lambda/myFunc); each invocation can create a log stream. **Search**: **CloudWatch Logs Insights** — query with a simple language (e.g. `fields @message | filter @message like /error/ | sort @timestamp desc`). Or **filter patterns** in the console. Set **retention** on the log group to control cost.

---

## Q5. (Intermediate) How do you create an alarm that triggers when Lambda errors exceed 10 in 5 minutes? What notification would you attach?

**Answer:**  
**Metric**: use built-in **Invocations** and **Errors** for the function. **Alarm**: metric = Errors, threshold = 10, period = 5 min, evaluation = 1 period (or 2 of 2 for stability). **Action**: SNS topic → email/Slack/Lambda. In console: Create alarm → Select metric (Lambda, Errors) → Threshold 10 → Add SNS topic. **Better**: use **percentage** (Errors/Invocations) if traffic varies.

---

## Q6. (Advanced) Production scenario: Your API (ALB + Lambda) has intermittent 5xx errors. How do you set up monitoring and alerting so the team is notified and can trace the cause?

**Answer:**  
(1) **ALB metrics**: **HTTPCode_ELB_5XX_Count** and **TargetResponseTime** — alarm when 5xx > 0 or response time > threshold. (2) **Lambda**: alarm on **Errors** and **Duration** (timeout). (3) **Logs**: CloudWatch Logs for Lambda; use **Logs Insights** with request ID (from ALB or API Gateway) to trace one request. (4) **X-Ray**: enable tracing on ALB and Lambda; use **ServiceLens** to see the path and latency per segment. (5) **SNS** → Slack/PagerDuty for alarms. **Senior**: “I’d use X-Ray and ServiceLens to see where the 5xx occurs in the chain, and alarm on ALB 5xx and Lambda errors with SNS to Slack.”

---

## Q7. (Advanced) What are CloudWatch Logs Insights and metric filters? When would you create a metric from a log pattern?

**Answer:**  
**Logs Insights**: query language over log groups (filter, parse, aggregate). **Metric filter**: pattern in logs → emit a **CloudWatch metric** (e.g. count of “ERROR” per 5 min). **Use metric from logs** when you want to **alarm** on a log pattern (e.g. “payment failed” count) or graph it. Create filter → metric → alarm; then you don’t have to query logs to know if the pattern spiked.

---

## Q8. (Advanced) Production scenario: You need to retain application logs for 7 years for compliance. CloudWatch Logs is expensive at scale. What strategy do you use?

**Answer:**  
(1) **Export** CloudWatch Logs to **S3** (subscription filter or export task); then **lifecycle** S3 to Glacier/Deep Archive for 7 years. (2) **Shorter retention** in CloudWatch (e.g. 30–90 days) for active search; long-term in S3/Glacier. (3) **Athena** or **OpenSearch** on S3 for querying archived logs. (4) **Cost**: S3 + Glacier is much cheaper than long CloudWatch retention. **Compliance**: ensure lifecycle and access control on the log bucket; consider Object Lock.

---

## Q9. (Advanced) Compare monitoring for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: basic CloudWatch (CPU, errors); one or two alarms (e.g. errors, downtime); email/Slack. **Medium**: custom metrics; Logs Insights; dashboards; alarms per service; SNS → Slack. **Enterprise**: **centralized** logging (cross-account, OpenSearch or external); **X-Ray** and distributed tracing; **SLO/SLI** and error budget alarms; **runbooks**; PagerDuty/incident management; compliance and long retention.

---

## Q10. (Advanced) Senior red flags to avoid with CloudWatch

**Answer:**  
- **No alarms** for errors, latency, or availability.  
- **Logging sensitive data** (passwords, tokens) to CloudWatch.  
- **Infinite retention** on log groups (set retention; export to S3 for long-term).  
- **Only checking console** when something breaks — use alarms and dashboards.  
- **No correlation** (request ID, trace ID) across logs and services.  
- **Ignoring** costs (logs and custom metrics can be expensive at scale).  
- **No runbook** or automation when an alarm fires.

---

**Tradeoffs:** Startup: basic metrics + 1–2 alarms. Medium: dashboards, Logs Insights, SNS. Enterprise: X-Ray, centralized logs, SLOs, runbooks.
