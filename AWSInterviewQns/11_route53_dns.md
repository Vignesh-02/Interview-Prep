# 11. Route 53 & DNS

## Q1. (Beginner) What is Route 53? What is a hosted zone and a record set?

**Answer:**  
**Route 53** is AWS **DNS** and **traffic** management. **Hosted zone**: container for DNS records for a domain (e.g. example.com). **Record set**: a single record (e.g. A, CNAME, ALIAS) with a name, type, TTL, and value. You create a hosted zone (or use one from your registrar) and add record sets to point domains to your resources.

---

## Q2. (Beginner) What is the difference between an A record and a CNAME? When can you use an ALIAS record (Route 53)?

**Answer:**  
**A**: maps name to **IP**. **CNAME**: maps name to **another name** (no A/AAAA at apex for standard DNS). **ALIAS** (Route 53): like CNAME but works at **apex** (e.g. example.com); can point to ALB, CloudFront, S3; no charge for queries to AWS resources. Use **ALIAS** for apex and for AWS targets; use **CNAME** for subdomains pointing to another name.

---

## Q3. (Intermediate) How do you point your domain (e.g. api.myapp.com) to an API Gateway or ALB? Show record type and value.

**Answer:**  
**API Gateway**: create **custom domain** in API Gateway (e.g. api.myapp.com) → get **API Gateway domain name** (e.g. d-xxx.execute-api.us-east-1.amazonaws.com) and **hosted zone ID**. In Route 53: create **ALIAS** record: api.myapp.com → API Gateway endpoint (choose “Alias to API Gateway”). **ALB**: ALIAS record api.myapp.com → ALB (select ALB in same region). **CloudFront**: ALIAS to CloudFront distribution. No CNAME at apex; use ALIAS.

---

## Q4. (Intermediate) What is a health check in Route 53? How does it relate to failover routing?

**Answer:**  
**Health check**: Route 53 periodically checks an endpoint (HTTP/HTTPS/TCP); marks it healthy or unhealthy. **Failover routing**: you have **primary** and **secondary** record sets; Route 53 returns **secondary** only when **primary** is unhealthy (based on health check). Use for **active-passive** failover (e.g. primary region and DR region).

---

## Q5. (Intermediate) You have an ALB in us-east-1 and one in eu-west-1. How do you route users to the nearest region using Route 53?

**Answer:**  
Use **latency-based routing**: create **two** (or more) record sets with the **same name and type** (e.g. app.example.com A ALIAS), each pointing to the ALB in one region; set **routing policy** to **Latency** and set the **region** for each (e.g. us-east-1, eu-west-1). Route 53 returns the record for the region with lowest latency from the user’s location.

---

## Q6. (Advanced) Production scenario: Your primary site is in us-east-1. If us-east-1 is down, you want traffic to fail over to eu-west-1 automatically. Design Route 53 and health checks.

**Answer:**  
(1) **Two record sets** for the same name (e.g. www.example.com): **Primary** (us-east-1 ALB), **Secondary** (eu-west-1 ALB). (2) **Routing**: **Failover**; primary has higher priority (e.g. 1), secondary (e.g. 2). (3) **Health checks**: one per ALB (e.g. HTTPS to /health); attach health check to each record set. When primary’s health check fails, Route 53 returns secondary. (4) **RTO**: health check interval (e.g. 30 s) + failover threshold (e.g. 3 failures) → ~2–3 min. (5) Use **ALIAS** to ALB to avoid charge and to get correct IP when ALB scales.

---

## Q7. (Advanced) What is Route 53 weighted routing? Give a use case (e.g. canary or blue-green).

**Answer:**  
**Weighted routing**: multiple record sets (same name/type) with **weights** (e.g. 90 and 10). Route 53 returns each with probability proportional to weight. **Use**: **canary** — 10% to new version, 90% to old; **blue-green** — shift 0/100 then 100/0; **A/B** — split traffic by weight. Combine with health checks so unhealthy targets get no traffic.

---

## Q8. (Advanced) How do you use Route 53 for private DNS (e.g. resolve internal-service.company.internal to an ALB in VPC)?

**Answer:**  
Create a **private hosted zone** (same name, e.g. company.internal); **associate** the zone with your **VPC(s)**. Add record sets (e.g. internal-service → ALB or NLB). Resolvers in the VPC (e.g. EC2, Lambda in VPC) use the VPC DNS and get the private hosted zone records. **No public** resolution for that zone. Use for service discovery inside AWS.

---

## Q9. (Advanced) Compare DNS for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one domain; A/ALIAS to ALB or CloudFront; maybe one health check for failover. **Medium**: custom domain for API and app; health checks; failover or latency routing if multi-region. **Enterprise**: **private hosted zones** for internal services; **geoproximity** or latency; **traffic flow** (advanced); **DNSSEC**; multiple domains and delegated subdomains; compliance (logging, retention).

---

## Q10. (Advanced) Senior red flags to avoid with Route 53

**Answer:**  
- **CNAME at apex** (use ALIAS).  
- **No health checks** for failover (traffic can go to dead endpoint).  
- **Low TTL** in production without need (increases cost and latency).  
- **Forgetting** to create the health check or attach it to the record.  
- **Single region** with no failover when SLA requires HA.  
- **No documentation** of which record points where and why.

---

**Tradeoffs:** Startup: ALIAS to ALB/CloudFront. Medium: health checks, failover. Enterprise: private zones, multi-region, traffic policies.
