# 16. Multi-Region & High Availability — Senior

## Q1. (Beginner) What is RTO and RPO? Why do they matter for DR?

**Answer:**  
**RPO** (Recovery Point Objective): max **acceptable data loss** (e.g. 1 hour → backups/sync every hour). **RTO** (Recovery Time Objective): max **acceptable downtime** (e.g. 4 hours → you must be back in 4 h). They drive **backup frequency**, **replication**, and **failover** design. Lower RPO/RTO = more cost (e.g. continuous replication, active-active).

---

## Q2. (Beginner) What is active-passive vs active-active in multi-region?

**Answer:**  
**Active-passive**: one **primary** region serves traffic; **secondary** is standby (used only on failover). **Active-active**: **multiple** regions serve traffic (e.g. Route 53 latency or weighted); no single primary. Active-passive is simpler and cheaper; active-active gives lower RTO and better global latency but is more complex (data consistency, routing).

---

## Q3. (Intermediate) If us-east-1 goes down entirely, how can your application fail over without manual intervention? What AWS services are involved?

**Answer:**  
(1) **Route 53** **health checks** on the primary (e.g. ALB or API); when they fail, **failover** routing returns the **secondary** region’s endpoint. (2) **Data**: **RDS** cross-region replica or **DynamoDB Global Tables**; **S3** CRR (Cross-Region Replication). (3) **Compute**: secondary region has **ALB + EC2/Lambda** (or ECS) already running or started by automation. (4) **DNS** TTL low enough (e.g. 60 s) so failover is quick. **No manual step**: health check + Route 53 failover + replicated data.

---

## Q4. (Intermediate) What is DynamoDB Global Tables? How does it help multi-region?

**Answer:**  
**Global Tables**: **multi-region** replication; same table in 2+ regions; **last-writer-wins** conflict resolution; **eventually consistent**. Writes in any region replicate to others. Use for **active-active** or **DR** when you need low-latency writes in multiple regions and can accept eventual consistency. **RTO** is low (other region already has data); **RPO** is near zero for recent writes.

---

## Q5. (Intermediate) What is AWS Global Accelerator? When would you use it instead of Route 53 for global traffic?

**Answer:**  
**Global Accelerator**: **two static anycast IPs**; traffic enters AWS at the **nearest edge** and is routed over AWS backbone to your app (ALB, NLB, EC2). **Use**: when you need **static IPs** (e.g. allowlisted), **DDoS protection** (Shield), or **fast failover** (health at edge). **Route 53**: DNS-based; no static IP; good for **routing** (latency, failover, weighted). Use **Global Accelerator** for static IP and edge health; use **Route 53** for DNS-based routing and cost.

---

## Q6. (Advanced) Production scenario: You run a critical API in us-east-1 (ALB + Lambda). Define RTO 1 hour, RPO 15 minutes. Design multi-region failover with no manual steps.

**Answer:**  
**RPO 15 min**: (1) **DynamoDB Global Tables** (if DB is DynamoDB) — replication within seconds; or **RDS** with cross-region read replica + backup copy to second region every 15 min. (2) **S3** CRR for assets. **RTO 1 h**: (1) **Secondary region** (e.g. us-west-2): deploy **same** stack (ALB, Lambda, API Gateway) via **CloudFormation** or CodePipeline; or **pre-warm** minimal capacity. (2) **Route 53** health check on primary ALB/API; **failover** policy to secondary. (3) **Data**: Global Tables or promote RDS replica; update DNS or use Route 53 failover. (4) **Automation**: optional Lambda/EventBridge to detect primary failure and promote replica. **No manual**: health check + Route 53 + replicated data + pre-deployed or auto-scaled secondary.

---

## Q7. (Advanced) What are Route 53 health check types (endpoint, CloudWatch alarm, calculated)? When would you use a calculated health check?

**Answer:**  
**Endpoint**: Route 53 checks a URL (HTTP/HTTPS/TCP). **CloudWatch alarm**: health is based on an **alarm** (e.g. CPU > 90%). **Calculated**: combines **multiple** health checks (e.g. “healthy if 2 of 3 regions are healthy”). **Use calculated** for **multi-region** or **composite** health (e.g. failover only when majority of regions are down).

---

## Q8. (Advanced) How do you implement circuit breaker and exponential backoff with jitter when calling another service (e.g. cross-region API) from your application?

**Answer:**  
**Circuit breaker**: after **N** failures, **open** the circuit (stop calling); after **cooldown**, **half-open** (try one call); if success, **close**. **Exponential backoff**: wait 2^attempt seconds (capped); **jitter** = add random 0–100% to avoid thundering herd. **In code**: use a library (e.g. opossum for Node, circuitbreaker for Python) or implement state machine. **AWS**: **AppConfig** or **Lambda** can store circuit state; or implement in app. **SDK**: AWS SDK has built-in retry with exponential backoff; tune maxAttempts and backoff.

---

## Q9. (Advanced) Compare multi-region for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: often **single region**; backup to second region (S3 CRR, RDS snapshot copy); manual or scripted failover. **Medium**: **two regions**; Route 53 failover; DynamoDB Global Tables or RDS replica; pre-deployed secondary. **Enterprise**: **active-active** or multiple regions; **Global Accelerator**; **RTO/RPO** targets; automated failover and runbooks; compliance (data residency).

---

## Q10. (Advanced) Senior red flags to avoid in multi-region / HA

**Answer:**  
- **No health checks** or wrong endpoint (e.g. checking wrong region).  
- **Single region** for critical workload with no DR plan.  
- **Manual** failover only (no automation).  
- **Ignoring** RPO/RTO (data loss or downtime beyond acceptable).  
- **No testing** of failover (run drills).  
- **Assuming** “replica” means “ready to serve” (test promotion and app config).  
- **No circuit breaker** (cascading failure when dependency is down).

---

**Tradeoffs:** Startup: single region, backup to second. Medium: 2 regions, Route 53 failover. Enterprise: active-active or multi-region, Global Accelerator, RTO/RPO.
