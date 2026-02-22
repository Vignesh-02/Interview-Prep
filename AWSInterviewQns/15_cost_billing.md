# 15. Cost Optimization & Billing

## Q1. (Beginner) What are the main cost dimensions for EC2, S3, and Lambda?

**Answer:**  
**EC2**: instance **hours** (on-demand or reserved), **EBS** storage, **data transfer** out. **S3**: **storage** (per class), **requests** (GET/PUT), **data transfer** out. **Lambda**: **invocations** and **duration** (GB-second). **Data transfer**: out to internet is often a large cost; in and same-region is often free or cheap.

---

## Q2. (Beginner) What are Reserved Instances and Savings Plans? How do they reduce cost?

**Answer:**  
**Reserved Instances (RI)**: commit to EC2 (or RDS) for 1 or 3 years; **discount** vs on-demand (e.g. 30–60%). **Savings Plans**: commit to **$ per hour** of compute (EC2, Fargate, Lambda); flexible across instance types and regions (for Compute SP). Both reduce cost for **steady** usage; avoid for variable or short-term workloads. **Startup**: maybe 1-year RI for baseline; **enterprise**: 3-year + Savings Plans.

---

## Q3. (Intermediate) How would you get an alert when the AWS bill (or a service cost) exceeds a threshold?

**Answer:**  
Use **AWS Budgets**: create a **cost budget** (e.g. total account or per-service); set **threshold** (e.g. 80% of $1000); add **alert** (email or SNS). **Forecast** budget can alert on projected overspend. **Billing alarm** (CloudWatch): create alarm on **Billing** metric (Total Estimated Charge) — requires **opt-in** to receive billing metrics. **Best**: Budgets for threshold and forecast; SNS to Slack/email.

---

## Q4. (Intermediate) Your Lambda runs 100M invocations/month at 512 MB, 200 ms average. Roughly how do you estimate cost and what levers reduce it?

**Answer:**  
**Rough**: 100M × (200 ms × 0.5 GB) = 10M GB-s; free tier is 400k GB-s; so pay for ~9.6M GB-s; plus 100M requests. **Levers**: (1) **Reduce duration** (optimize code, more memory for more CPU). (2) **Reduce memory** if CPU is not the bottleneck (right-size). (3) **Provisioned concurrency** only if needed (adds cost). (4) **Fewer invocations** (cache, batch). Use **Cost Explorer** and **Lambda cost** in calculator for exact numbers.

---

## Q5. (Intermediate) What is the Cost Explorer? What can you use it for in a multi-service setup?

**Answer:**  
**Cost Explorer** shows **historical** and **forecasted** costs; filter by **service**, **region**, **tag**, **usage type**. Use to: (1) See which **service** or **resource** costs the most. (2) **Forecast** next month. (3) **Filter by tag** (e.g. env=prod, team=backend) for chargeback or showback. (4) Compare **on-demand vs reserved** savings. Enable **Cost Explorer** (may take 24 h for data); use **tags** consistently for useful breakdowns.

---

## Q6. (Advanced) Production scenario: Your startup’s monthly AWS bill is $5k. Breakdown: EC2 40%, RDS 25%, S3 15%, data transfer 15%, other 5%. You need to cut 20% without sacrificing reliability. Propose a plan.

**Answer:**  
(1) **EC2**: **Reserved** or **Savings Plans** for baseline (e.g. 1-year); **right-size** (Graviton, smaller instance if over-provisioned); **Spot** for non-critical batch. (2) **RDS**: **Reserved** instance; **right-size**; consider **read replica** only if needed (don’t add for no reason). (3) **S3**: **Lifecycle** to IA/Glacier for old data; **Intelligent-Tiering**; review **request** cost (reduce LIST/GET with caching). (4) **Data transfer**: **CloudFront** for static assets; reduce **cross-region** and **out to internet**; compress. (5) **Other**: review **unused** (EBS snapshots, old EIPs, idle resources). **Target**: 20% = $1k; prioritize Reserved + right-size + lifecycle.

---

## Q7. (Advanced) What are cost allocation tags? How do you use them for showback or chargeback?

**Answer:**  
**Cost allocation tags**: **tags** (e.g. Team, Project, Env) that you **activate** in Billing for cost allocation. Once activated, **Cost Explorer** and **reports** can group by these tags. **Showback/chargeback**: tag resources by **team** or **project**; run reports by tag; each team sees its share. **Best practice**: tag at creation (enforce with policy); use **consistent** key names (e.g. team, not Team).

---

## Q8. (Advanced) Compare cost strategy for startup vs enterprise. What does each typically do?

**Answer:**  
**Startup**: **on-demand** first; **budgets** and alerts; **tags** (env); **right-size** after a few months; maybe **1-year RI** for biggest line items. **Medium**: **Reserved**/Savings Plans for baseline; **lifecycle** (S3, snapshots); **Cost Explorer** by tag; **right-size** (Compute Optimizer). **Enterprise**: **central** billing (Consolidated Billing or Organizations); **Savings Plans** and **RI** at scale; **cost allocation** and chargeback; **policies** (e.g. no prod without tag); **FinOps** team.

---

## Q9. (Advanced) What is AWS Compute Optimizer? When would you use it?

**Answer:**  
**Compute Optimizer** analyzes **EC2**, **Lambda**, **EBS** usage and recommends **right-sizing** (e.g. smaller instance, Graviton). It uses **CloudWatch** and **historical** data. **Use**: after a few weeks of steady workload; review recommendations and **test** in non-prod before resizing prod. Complements **Cost Explorer** (what you spend) with **what you should use**.

---

## Q10. (Advanced) Senior red flags to avoid with cost

**Answer:**  
- **No budgets or alerts** (bill shock).  
- **Leaving** unused resources (EBS, EIP, old snapshots, idle RDS).  
- **No tags** (can’t attribute cost).  
- **Over-provisioning** (e.g. always xlarge) without right-sizing.  
- **Ignoring** data transfer (out to internet, cross-region).  
- **No lifecycle** (S3, backups) so storage grows forever.  
- **Using** on-demand only at scale without Reserved/Savings Plans.

---

**Tradeoffs:** Startup: budgets, tags, right-size. Medium: Reserved, lifecycle, Cost Explorer. Enterprise: Savings Plans, chargeback, FinOps.
