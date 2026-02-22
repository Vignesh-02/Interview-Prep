# 17. Lambda at Scale (Concurrency, RDS Proxy) — Senior

## Q1. (Beginner) What is reserved concurrency vs provisioned concurrency?

**Answer:**  
**Reserved concurrency**: **cap** on how many concurrent executions of this function can run; guarantees this function gets that share of the account pool; can **throttle** others. **Provisioned concurrency**: keep a number of execution environments **warm** (no cold start for those); you pay for pre-warmed capacity. Use **reserved** to limit (e.g. protect downstream); use **provisioned** to reduce latency (e.g. critical API).

---

## Q2. (Beginner) Why do Lambdas and RDS often have a “too many connections” problem? What is the fix?

**Answer:**  
**Problem**: each Lambda invocation can open a **new** DB connection; with **high concurrency** you exceed RDS **max_connections**. **Fix**: (1) **RDS Proxy** — Lambdas connect to Proxy; Proxy **pools** connections to RDS (few hundred Lambdas → tens of connections). (2) **Reuse** connection per execution context (global variable); limit **reserved concurrency** so not all Lambdas run at once. **Best**: RDS Proxy + connection reuse.

---

## Q3. (Intermediate) Your Lambda times out in production under load but not in dev. How do you distinguish cold start from downstream (e.g. DB) bottleneck?

**Answer:**  
(1) **CloudWatch** — **Duration** metric (p50, p99); **ConcurrentExecutions**; **Throttles**. (2) **X-Ray** — see **segments**: init vs DB call; if DB segment is long, downstream. (3) **Provisioned concurrency** test: enable for a few; if timeouts drop, cold start was a factor. (4) **Load test** with fixed concurrency: if duration grows with concurrency, likely **connection pool** or **DB** saturation. **Senior**: “I’d use X-Ray to see where time is spent; if it’s the DB segment, I’d add RDS Proxy and tune concurrency.”

---

## Q4. (Intermediate) What is Step Functions Distributed Map? When would you use it instead of invoking Lambda in a loop from another Lambda?

**Answer:**  
**Distributed Map** (Step Functions): process **large** collections (e.g. millions of S3 keys) in **parallel**; each item invokes a Lambda (or other step); **managed** concurrency and failure handling. **vs Lambda loop**: Lambda has **15 min** and **memory** limits; loop is sequential or you fan-out (complex). Use **Distributed Map** for “process every item in a large set” (e.g. S3 inventory, bulk transform); use Lambda loop only for small sets.

---

## Q5. (Intermediate) How do you configure RDS Proxy for a Lambda-backed API that uses RDS MySQL? What does the Lambda need to change?

**Answer:**  
(1) Create **RDS Proxy** in front of RDS; **auth** via **Secrets Manager** (store DB credentials). (2) **Lambda**: change **connection string** (host) from RDS endpoint to **Proxy endpoint**; port same (e.g. 3306). (3) **IAM**: Lambda execution role needs `rds-db:connect` (for IAM auth) or Proxy uses Secrets Manager (no IAM auth required). (4) **Connection reuse**: keep reusing the same connection in the handler (global); Proxy pools. **No code change** beyond host; connection reuse is best practice anyway.

---

## Q6. (Advanced) Production scenario: Lambda processes S3 uploads (10k files/day); each invocation reads from RDS and writes to DynamoDB. You see throttling and “too many connections.” Design the fix with concurrency, RDS Proxy, and idempotency.

**Answer:**  
(1) **RDS Proxy**: put Proxy in front of RDS; Lambda connects to Proxy; set Proxy **max connections** to RDS max or slightly less. (2) **Reserved concurrency**: set Lambda **reserved concurrency** (e.g. 50) so you don’t burst to 1000 and exhaust Proxy/RDS. (3) **Idempotency**: S3 can deliver duplicate events; use **DynamoDB** or **SQS** to dedupe (e.g. key by S3 ETag or object key + event time); skip if already processed. (4) **DynamoDB**: use on-demand or sufficient capacity; no connection pool issue. (5) **DLQ**: send failed S3 events to SQS DLQ; alarm on depth. **Result**: controlled concurrency, pooled DB connections, idempotent processing.

---

## Q7. (Advanced) What is Lambda’s synchronous vs asynchronous invocation limit? How does it affect scaling?

**Answer:**  
**Synchronous** (e.g. API Gateway, ALB): limit is **concurrent executions** (account default 1000; can request more). **Asynchronous** (e.g. S3, SNS): invocations are **queued**; Lambda reads from internal queue; **burst** limit applies (e.g. 1000 initial, then 500/min scale). So **async** can accept huge spikes (queue grows); **sync** can return 429 if you exceed concurrency. For **sync** at scale, request quota increase or use **provisioned concurrency** to reserve capacity.

---

## Q8. (Advanced) How would you process 1M S3 objects with Lambda without hitting timeouts or concurrency limits? Describe the architecture.

**Answer:**  
(1) **S3 event** → **SQS** (one message per object or batch); **Lambda** triggered by SQS (batch size 1–10). **Or** (2) **Step Functions Distributed Map**: list 1M keys (S3 List or inventory); Map state runs **Lambda** per item with **maxConcurrency** (e.g. 500). (3) **Reserved concurrency** on Lambda to protect downstream (e.g. 500). (4) **DLQ** for failed items; **idempotency** for retries. (5) Avoid “one Lambda that loops 1M times” (timeout). **Preferred**: SQS + Lambda (natural backpressure) or Distributed Map for orchestration.

---

## Q9. (Advanced) Compare Lambda at scale for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: default concurrency; connection reuse; maybe RDS Proxy if using RDS. **Medium**: **reserved concurrency** for critical functions; **RDS Proxy** for RDS; **provisioned concurrency** for user-facing API; **X-Ray** and alarms. **Enterprise**: **concurrency** and **quota** planning; **VPC** and PrivateLink; **layers** and governance; **DLQ** and retry policies; compliance (logging, encryption).

---

## Q10. (Advanced) Senior red flags to avoid with Lambda at scale

**Answer:**  
- **No concurrency control** (downstream or account throttling).  
- **Opening new DB connection** per invocation without Proxy or pooling.  
- **No idempotency** for event-driven Lambdas (duplicates).  
- **Ignoring** cold start for critical path (provisioned concurrency or design).  
- **No DLQ** or retry strategy for async invocations.  
- **Processing huge batches** in one invocation (use Step Functions or SQS).  
- **No alarms** on throttles, errors, or duration.

---

**Tradeoffs:** Startup: default concurrency, reuse connections. Medium: RDS Proxy, reserved concurrency. Enterprise: provisioned concurrency, Distributed Map, quotas.
