# 5. Lambda & Serverless Basics

## Q1. (Beginner) What is AWS Lambda? What are the main limits (timeout, memory, payload)?

**Answer:**  
**Lambda** is serverless **functions**: you provide code; AWS runs it on events (API, S3, SQS, etc.). **Limits**: **timeout** max 15 min; **memory** 128 MB–10 GB (affects CPU); **payload** (request/response) 6 MB sync, 256 KB for async event; **deployment package** 50 MB zipped, 250 MB unzipped (layers help). Design for short, stateless execution; use Step Functions or queues for long workflows.

---

## Q2. (Beginner) How does a Lambda get permission to read from S3 or write to DynamoDB?

**Answer:**  
Attach an **IAM role** (execution role) to the Lambda. The role needs policies that allow the needed actions (e.g. `s3:GetObject`, `dynamodb:PutItem`). Lambda assumes this role when it runs; no access keys in code. Create a role with `lambda.amazonaws.com` as trusted principal and attach resource policies (e.g. S3 bucket policy can allow Lambda to invoke, but execution role is what grants Lambda permission to call S3).

---

## Q3. (Intermediate) What is a Lambda trigger? Give two examples: one synchronous and one asynchronous.

**Answer:**  
**Trigger** = event source that invokes the function. **Synchronous**: caller waits for response — e.g. **API Gateway**, **ALB**, **Cognito**. **Asynchronous**: event is queued; Lambda retries on failure — e.g. **S3** (object created), **SNS**, **EventBridge**. Sync: return response to client. Async: accept event, process, return; use DLQ for failed invocations.

---

## Q4. (Intermediate) Write a minimal Lambda function (Node.js or Python) that receives an API Gateway event, reads `name` from the body (JSON), and returns `{ message: "Hello, {name}" }`.

**Answer (Node.js):**
```javascript
exports.handler = async (event) => {
  const body = JSON.parse(event.body || '{}');
  const name = body.name || 'World';
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: `Hello, ${name}` })
  };
};
```

**Answer (Python):**
```python
import json
def handler(event, context):
    body = json.loads(event.get('body') or '{}')
    name = body.get('name', 'World')
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': f'Hello, {name}'})
    }
```

---

## Q5. (Intermediate) What is a Lambda layer? When would you use one?

**Answer:**  
A **layer** is a zip of libraries or runtime pieces that multiple functions can share. **Use**: (1) Share dependencies (e.g. SDK, ORM) without packaging in every deployment. (2) Separate custom runtime or large libs from code (faster deploy). (3) Enforce common code (e.g. logging, tracing). Layer is mounted at `/opt`; function code can import from there. Max 5 layers per function; total unzipped size limit applies.

---

## Q6. (Advanced) Production scenario: A Lambda is triggered by S3 uploads (10k files/day). It must resize images and write to another S3 bucket. How do you design for concurrency, errors, and cost? Include tradeoff for startup vs enterprise.

**Answer:**  
**Design**: (1) **S3 event** → Lambda (async); process one object per invocation (or batch if using S3 event notifications to SQS then Lambda). (2) **Concurrency**: set **reserved concurrency** (e.g. 50) to avoid throttling downstream (e.g. DynamoDB) or **provisioned concurrency** only if you need low latency (usually not for batch). (3) **Errors**: **on-failure** send to **SQS DLQ** or S3; retry with backoff (Lambda retries twice by default). (4) **Memory**: tune (e.g. 1–2 GB) for image processing; more memory = more CPU. (5) **Cost**: right-size memory; use S3 GET/PUT only when needed. **Startup**: default concurrency, DLQ to SQS. **Enterprise**: reserved concurrency, X-Ray, alarms on DLQ depth, lifecycle for source objects.

---

## Q7. (Advanced) What is cold start? How can you reduce its impact for an API backed by Lambda?

**Answer:**  
**Cold start**: first request (or after idle) loads the runtime and runs init code; adds latency (hundreds of ms to seconds). **Reduce**: (1) **Provisioned Concurrency** — keep a pool warm (cost). (2) **Smaller package** and **lazy load** heavy libs. (3) **ARM/Graviton** runtime often has faster cold start. (4) **Keep functions warm** with a scheduled ping (CloudWatch Events) — only helps that one instance. (5) **API Gateway** with **HTTP API** (or REST) + Lambda proxy; use provisioned concurrency for critical paths. For user-facing API, provisioned concurrency or accept p99 latency with cold starts.

---

## Q8. (Advanced) Production scenario: Lambda A calls Lambda B (synchronously). Lambda B sometimes times out. How do you make the flow resilient and observable?

**Answer:**  
**Resilience**: (1) Prefer **asynchronous** invocation: A publishes to **SNS** or **EventBridge**; B is triggered; A returns immediately. Use **SQS** between for retries and DLQ. (2) If sync is required: set **timeout** and **retry** in A; B should be idempotent and have its own timeout/DLQ. **Observability**: (1) **X-Ray** tracing across A and B (enable on both). (2) **CloudWatch Logs** with **request ID** (or correlation ID) in logs. (3) **Alarms** on B’s errors and duration. (4) **ServiceLens** (X-Ray + CloudWatch) to see the full flow.

---

## Q9. (Advanced) Compare Lambda for startup (single account, few functions) vs enterprise (multi-account, compliance, high scale). What does each typically need?

**Answer:**  
**Startup**: few Lambdas; IAM role per function or shared; CloudWatch Logs default retention; no provisioned concurrency; async + DLQ for critical flows. **Enterprise**: **separate roles** per function (least privilege); **VPC** for RDS/private APIs (use VPC connector or PrivateLink); **provisioned concurrency** for critical APIs; **X-Ray** and centralized logging; **concurrency limits** and quotas; **Lambda layers** from private registry; compliance (encryption, audit).

---

## Q10. (Advanced) Senior red flags to avoid with Lambda

**Answer:**  
- **No execution role** or over-privileged role (e.g. s3:* on *).  
- **Long-running** logic (use Step Functions or queue for > 1–2 min).  
- **No error handling** or DLQ for async invocations.  
- **Storing state** in global variables and assuming warm reuse (design for stateless).  
- **No idempotency** for event-driven Lambdas (duplicate events possible).  
- **Connecting to RDS** without connection pooling or RDS Proxy (exhaust connections).  
- **Ignoring** cold start for user-facing APIs.  
- **No alarms** on errors, throttles, or duration.

---

**Tradeoffs:** Startup: default concurrency, minimal roles, DLQ. Medium: reserved concurrency, layers, X-Ray. Enterprise: provisioned concurrency, VPC, strict IAM, compliance.
