# 10. API Gateway

## Q1. (Beginner) What is API Gateway? What are the two API types (REST and HTTP)?

**Answer:**  
**API Gateway** is managed **API** front-end: routing, auth, throttling, and integration with Lambda, HTTP, AWS services. **REST API** (v1): resources, methods, stages; request/response mapping; usage plans and API keys. **HTTP API** (v2): simpler, lower cost; native JWT/OIDC; direct Lambda/HTTP integration; no request mapping. Use **HTTP API** for most new serverless APIs; **REST** when you need request transformation, API keys, or WAF.

---

## Q2. (Beginner) How does API Gateway integrate with Lambda? What is the Lambda proxy integration?

**Answer:**  
**Integration**: API Gateway invokes Lambda when a route is hit; can pass through the request (proxy) or map to a custom payload. **Lambda proxy integration**: request (path, query, headers, body) is passed as the **event** to Lambda; Lambda returns **statusCode**, **headers**, **body**; no mapping in API Gateway. Easiest for dynamic responses. **Non-proxy**: you define mapping templates (VTL) to shape request/response; more control, more config.

---

## Q3. (Intermediate) How do you protect an API with an API key? What are usage plans?

**Answer:**  
**API key**: create a key in API Gateway; attach to **usage plan**. **Usage plan**: throttling (rate + burst) and quota per key (or per plan). **Protection**: require API key on method (or stage); client sends `x-api-key` header. Use for **partner** or **tiered** access; not for end-user auth (use Cognito/JWT). **REST API** supports keys; **HTTP API** does not (use JWT or Lambda authorizer).

---

## Q4. (Intermediate) What is a Lambda authorizer (custom authorizer)? When would you use it?

**Answer:**  
**Lambda authorizer**: a Lambda that API Gateway calls to **authorize** the request (before the backend Lambda). It receives token/headers; returns **allow** (with optional policy) or **deny**. Use for **custom** auth (e.g. validate API key, HMAC, or external JWT). **Cognito** is built-in for JWT; use Lambda authorizer when you need custom logic (e.g. API key in header, or token from non-Cognito IdP).

---

## Q5. (Intermediate) Your API must accept requests only from a frontend on https://app.example.com. How do you restrict CORS and protect the API?

**Answer:**  
**CORS**: in API Gateway (REST or HTTP), set **Access-Control-Allow-Origin** to `https://app.example.com` (not `*` in production). **Protect API**: (1) **WAF** — allow only your domain (referer or custom header) or use geo. (2) **Cognito** or **JWT** — frontend sends token; API validates. (3) **API key** for server-to-server. CORS alone does **not** secure the API (browsers enforce CORS; non-browser clients can ignore). Use auth (JWT/Cognito) + CORS.

---

## Q6. (Advanced) Production scenario: You expose a REST API (API Gateway + Lambda). Traffic grows to 10k req/min. You see 429 (throttling) during peaks. How do you fix it without changing backend logic?

**Answer:**  
(1) **Raise throttling** in API Gateway: **account-level** (default 10k req/s); request **limit increase** if needed. (2) **Per-method** or **per-route** throttling: increase in usage plan or method settings. (3) **Caching**: enable **API Gateway caching** (if REST API) for GET with cache key (e.g. query string); reduces Lambda invocations. (4) **HTTP API** has higher default limits and lower cost. (5) **WAF** or **CloudFront** in front can also cache. **Senior**: “I’d enable caching for idempotent GETs and request a limit increase; then consider HTTP API or CloudFront.”

---

## Q7. (Advanced) What is the “storage-first” or “integration without Lambda” pattern? How do you connect API Gateway directly to SQS or DynamoDB?

**Answer:**  
**Pattern**: API Gateway integrates **directly** with AWS services (SQS, DynamoDB, etc.) **without** Lambda, reducing latency and cost. **REST API**: use **AWS integration** (not Lambda); map request to SQS SendMessage or DynamoDB PutItem (VTL mapping). **HTTP API**: **direct integration** with some services (e.g. Lambda, HTTP); for SQS/DynamoDB you may still use Lambda or use REST with AWS integration. **Benefit**: no cold start; fewer moving parts; good for simple ingest (e.g. POST → SQS).

---

## Q8. (Advanced) Production scenario: You need to expose an internal HTTP API (ALB + EC2) to the internet with authentication, rate limiting, and audit. How do you use API Gateway in front?

**Answer:**  
(1) **API Gateway** (REST or HTTP) with **HTTP integration** to ALB (private VPC link or public ALB). (2) **Auth**: Cognito authorizer (JWT) or Lambda authorizer for custom auth. (3) **Rate limiting**: usage plan and API key, or throttling per stage. (4) **Audit**: **CloudTrail** for API Gateway (who called what); **access logging** to CloudWatch or S3 (request/response). (5) **WAF** optional for additional protection. Internal ALB can stay in private subnet; API Gateway is the only public entry.

---

## Q9. (Advanced) Compare API Gateway for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: HTTP API + Lambda; Cognito or API key; one stage (e.g. prod); basic CORS. **Medium**: REST or HTTP; usage plans; custom domain; WAF; CloudWatch and alarms. **Enterprise**: **private API** (VPC Link to NLB); **WAF** rules and rate limiting; **Cognito** or enterprise IdP; **stages** (dev/staging/prod); **access logging** and compliance; request validation.

---

## Q10. (Advanced) Senior red flags to avoid with API Gateway

**Answer:**  
- **No auth** on production endpoints (use Cognito or authorizer).  
- **CORS `*`** in production (restrict to known origins).  
- **No throttling** (risk of abuse and cost).  
- **Sensitive data** in query strings (use body or headers; log carefully).  
- **No access logging** or CloudTrail for audit.  
- **REST API** when HTTP API would suffice (cost and limits).  
- **Ignoring** 429 and not raising limits or adding caching.

---

**Tradeoffs:** Startup: HTTP API + Lambda, Cognito. Medium: usage plans, custom domain, WAF. Enterprise: private API, WAF, logging, compliance.
