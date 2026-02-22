# 30. Production Red Flags & Best Practices — Senior

## Q1. (Beginner) What does “production-ready” mean for an AWS workload? Name three aspects.

**Answer:**  
**Production-ready**: (1) **Availability** — multi-AZ, health checks, auto-scaling. (2) **Security** — least privilege, encryption, no secrets in code. (3) **Observability** — logging, metrics, alarms, tracing. (4) **Recovery** — backups, DR, tested failover. (5) **Cost** — right-sized, tagged, budgets. **Senior**: “I’d ensure HA, least-privilege IAM, encryption, monitoring with alarms, and a tested backup/DR plan.”

---

## Q2. (Beginner) Give one example of a “junior” answer vs a “senior” answer for: “How do you scale this?”

**Answer:**  
**Junior**: “I’ll add more RAM” or “I’ll use a bigger instance.” **Senior**: “I’d use **Auto Scaling** with **Predictive Scaling** or scale on **request count per target**; I’d identify the **bottleneck** (CPU, memory, DB connections) with **CloudWatch** and **X-Ray** and scale that tier; I’d use **read replicas** for DB if read-bound.” **Takeaway**: scale the **right** dimension with **metrics** and **automation**, not just “bigger box.”

---

## Q3. (Intermediate) Give one example of a “junior” vs “senior” answer for: “How do you secure the API?”

**Answer:**  
**Junior**: “I’ll use an IAM user with access key in the app.” **Senior**: “I’d use **IAM roles** for the app (EC2 instance profile or Lambda execution role); **no long-lived** keys. I’d put **API Gateway** in front with **Cognito** or **Lambda authorizer** for auth; **WAF** for rate limit and allow list; **VPC** and **security groups** so only ALB can reach the app.” **Takeaway**: **roles**, **auth**, **WAF**, **network** — not keys in code.

---

## Q4. (Intermediate) Give one example of a “junior” vs “senior” answer for: “The app is slow. How do you debug?”

**Answer:**  
**Junior**: “I’ll check the logs in the console.” **Senior**: “I’d use **X-Ray** for **distributed tracing** to see which service or call is slow; **CloudWatch ServiceLens** to correlate **traces**, **logs**, and **metrics**. I’d check **ALB** target response time and **Lambda** duration; **RDS** Performance Insights for slow queries. I’d set **alarms** so we’re alerted next time.” **Takeaway**: **tracing**, **correlation**, **metrics** — not only ad-hoc log diving.

---

## Q5. (Intermediate) What are the top five “red flags” you would call out in a design review for a new production system on AWS?

**Answer:**  
(1) **Single point of failure** (one AZ, one instance, no backup). (2) **Secrets in code or env** (use Secrets Manager, IAM roles). (3) **Overly broad IAM** (s3:*, Resource *) or root. (4) **No monitoring** (no alarms on errors, latency, or availability). (5) **DB or app in public subnet** or **0.0.0.0/0** on security groups. (6) **No backup or DR** plan. (7) **No idempotency** for event-driven or payment flows.

---

## Q6. (Advanced) Production scenario: You inherit a system that has: IAM user with access key for the app, RDS in public subnet, no CloudWatch alarms, single EC2 instance. List the fixes in priority order and justify.

**Answer:**  
(1) **Secrets/access**: **Remove** IAM user key from app; create **IAM role** (instance profile or Lambda role); use **Secrets Manager** for RDS password; rotate credentials. **Priority**: **critical** (credential leak risk). (2) **RDS**: **Move** RDS to **private** subnet (or create new instance in private, migrate, switch). **Priority**: **critical** (exposure). (3) **Alarms**: Add **CloudWatch** alarms (RDS CPU, connections, EC2 status, errors); **SNS** to Slack/email. **Priority**: **high** (visibility). (4) **HA**: Add **second** instance (ASG min=2) and **multi-AZ** RDS; **ALB** in front. **Priority**: **high** (availability). (5) **Backup**: Verify **RDS** automated backup and **retention**; **EBS** snapshots or AMI for EC2. **Order**: security first (credentials, RDS exposure), then observability, then HA and backup.

---

## Q7. (Advanced) What does “security first” mean in practice when designing an AWS workload? Give five concrete practices.

**Answer:**  
(1) **Least privilege**: IAM roles with **minimal** actions and resources; **Permission Boundaries** when delegating. (2) **No secrets in code**: **Secrets Manager** or Parameter Store; **rotation** where possible. (3) **Encryption**: **at rest** (S3, RDS, EBS default or KMS); **in transit** (TLS, HTTPS). (4) **Network**: **private** subnets for app and data; **security groups** allow only needed sources (e.g. ALB SG, not 0.0.0.0/0). (5) **Audit**: **CloudTrail** on; **Config** or **GuardDuty**; review access and changes. (6) **WAF** and **rate limiting** on public endpoints.

---

## Q8. (Advanced) How do you avoid “it works on my machine” and “we’ll fix it in prod” when deploying to AWS? What practices do you recommend?

**Answer:**  
(1) **Infrastructure as Code** (CloudFormation, Terraform) — same config in dev and prod. (2) **Environments**: **dev**, **staging**, **prod** with similar topology (multi-AZ in staging too). (3) **CI/CD** — automated **test** and **deploy**; **staging** before prod. (4) **Feature flags** and **gradual** rollout (canary, weighted). (5) **Monitoring** and **alarms** so issues are caught in staging or early in prod. (6) **Runbooks** and **post-mortems** so “fix in prod” becomes “fix process and prevent.”

---

## Q9. (Advanced) Summarize the “senior vs junior” table: scaling, security, databases, and failures. What should an intermediate developer aiming for senior avoid saying?

**Answer:**  
| Topic    | Avoid (junior)                    | Prefer (senior)                                                                 |
|----------|-----------------------------------|----------------------------------------------------------------------------------|
| Scaling  | “Add more RAM”                    | Auto Scaling, metrics, bottleneck analysis, read replicas, right-sizing         |
| Security | “IAM user with key”               | IAM roles, Secrets Manager, no long-lived keys, WAF, least privilege            |
| Databases| “RDS for everything”              | Right store per access pattern: DynamoDB, Aurora, OpenSearch; RDS Proxy for Lambda |
| Failures | “Check logs in console”           | X-Ray, ServiceLens, alarms, runbooks, tracing, correlation                       |

**Avoid**: one-size-fits-all, manual fixes only, no metrics, no automation, secrets in code, single point of failure.

---

## Q10. (Advanced) What are the top 10 production red flags to avoid (consolidated list)?

**Answer:**  
1. **Single point of failure** (one AZ, one instance).  
2. **Secrets in code or env** (use Secrets Manager, roles).  
3. **Overly broad IAM** or root use.  
4. **No monitoring/alarms** (errors, latency, availability).  
5. **DB or app in public subnet** or **0.0.0.0/0** on SG.  
6. **No backup or DR** (no tested restore).  
7. **No idempotency** for payments or event-driven flows.  
8. **Lambda + RDS** without **RDS Proxy** (connection exhaustion).  
9. **No retry/DLQ** for async (SQS, Lambda).  
10. **Ignoring cost** (no budgets, no tags, no right-sizing).  

**Plus**: no runbooks, no correlation (trace ID), logging sensitive data, manual-only deploy, no health checks.

---

**Tradeoffs:** Always aim for: HA, least privilege, encryption, observability, backup/DR, and automation. Adjust depth (startup vs enterprise) but not these principles.
