# 26. FinOps & Right-Sizing — Senior

## Q1. (Beginner) What is right-sizing? Give one example for EC2 and one for RDS.

**Answer:**  
**Right-sizing**: matching **resource size** to **actual usage** to reduce cost without hurting performance. **EC2**: if CPU is always < 20%, consider **smaller** instance (e.g. large → medium) or **Graviton**. **RDS**: if connections and CPU are low, **smaller** instance class or **Aurora Serverless**. Use **CloudWatch** and **Compute Optimizer** to get recommendations.

---

## Q2. (Beginner) What is AWS Compute Optimizer? What does it recommend?

**Answer:**  
**Compute Optimizer** analyzes **EC2**, **Lambda**, **EBS** usage (CloudWatch, historical) and recommends **right-sizing** (e.g. smaller instance, Graviton, different instance type) and **right-scaling** (e.g. scale down). **Recommendations** show **estimated savings** and **performance risk**. Use after a few weeks of steady workload; **test** in non-prod before applying to prod.

---

## Q3. (Intermediate) Your EC2 fleet is a mix of Intel and you want to reduce cost. What is Graviton and how do you evaluate migrating?

**Answer:**  
**Graviton** is AWS **ARM** processor (Graviton2/3); often **20–40%** better price-performance for compatible workloads. **Evaluate**: (1) **Compatibility**: app and dependencies (Node, Python, Java, Go, many others) run on ARM; check for x86-only binaries. (2) **Compute Optimizer**: see Graviton recommendations. (3) **Test**: launch **Graviton** instance (e.g. m7g same size as m5); run load test; compare latency and throughput. (4) **Migrate**: AMI or rebuild for ARM; roll out gradually. **Startup**: try Graviton for new workloads; **enterprise**: pilot then migrate.

---

## Q4. (Intermediate) Production scenario: S3 storage cost is high. 80% of objects are older than 90 days and rarely accessed. What do you do?

**Answer:**  
(1) **Lifecycle**: **Transition** to **S3 IA** after 90 days (or **Intelligent-Tiering**). (2) **Analyze**: use **S3 Storage Class Analysis** to confirm access pattern. (3) **Transition** to **Glacier** after 180/365 days if acceptable retrieval delay. (4) **Result**: most data in IA/Glacier; **significant** storage cost reduction. **No data loss**; adjust retention and retrieval needs per compliance.

---

## Q5. (Intermediate) What are Savings Plans? How do they differ from Reserved Instances?

**Answer:**  
**Savings Plans**: commit to **$ per hour** of compute usage (e.g. $10/hr for 1 year); **flexible** across **EC2**, **Fargate**, **Lambda** (Compute SP) or **EC2** only (EC2 SP). **Reserved Instances**: commit to **specific** instance type (and optionally AZ); **discount** for that usage. **Savings Plans** = simpler (no instance pick); **RI** = higher discount if you can commit to specific type. **Use**: Savings Plans for **flexibility**; RI when usage is very predictable.

---

## Q6. (Advanced) Production scenario: Your monthly bill is $20k. EC2 35%, RDS 20%, data transfer 18%, S3 12%, other 15%. You must cut 25% in 3 months. Propose a plan with priorities.

**Answer:**  
(1) **EC2 (35%)**: **Savings Plans** or **RI** for baseline (e.g. 1-year); **right-size** (Compute Optimizer); **Graviton** where possible; **Spot** for non-critical; **target** ~30% EC2 reduction. (2) **RDS (20%)**: **Reserved** instance; **right-size**; consider **Aurora Serverless** for variable load. (3) **Data transfer (18%)**: **CloudFront** for static; reduce **cross-region** and **out to internet**; **compress**; **target** 30% reduction. (4) **S3 (12%)**: **Lifecycle** to IA/Glacier; **Intelligent-Tiering**; reduce **request** cost. (5) **Other**: **tag** and **identify** (Cost Explorer); remove **unused** (EBS, EIP, snapshots). **Total target**: 25% = $5k; track weekly and adjust.

---

## Q7. (Advanced) What is cost allocation and showback/chargeback? How do tags support it?

**Answer:**  
**Cost allocation**: attribute **cost** to **teams**, **projects**, or **cost centers**. **Showback**: report cost per team (no billing). **Chargeback**: **bill** each team their share. **Tags**: **tag** resources (e.g. Team=backend, Project=api); **activate** tags in **Cost Allocation Tags** (Billing); **Cost Explorer** and **reports** group by tag. **Best practice**: **enforce** tags (e.g. tag policy in Organizations); **consistent** keys (team, project, env).

---

## Q8. (Advanced) When would you use Spot instances in production? What are the risks and mitigations?

**Answer:**  
**Use**: **fault-tolerant** or **interruptible** workloads (e.g. batch, CI, some web with multiple nodes). **Risks**: **interruption** (2 min notice); **no guarantee** of capacity. **Mitigations**: (1) **Diversify** (multiple types, AZs). (2) **Spot Fleet** with **fallback** to On-Demand. (3) **Checkpoint** and **resume** (save state; restart on another Spot or On-Demand). (4) **Mixed** with On-Demand for baseline. **Don’t** use Spot for **single** critical instance without fallback.

---

## Q9. (Advanced) Compare FinOps for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: **budgets** and **alerts**; **tags** (env); **right-size** after a few months; **Reserved** or Savings Plans for biggest line items. **Medium**: **Cost Explorer** by tag; **Compute Optimizer**; **lifecycle** (S3, snapshots); **Savings Plans**; **showback** by team. **Enterprise**: **FinOps** team; **chargeback**; **policies** (tag enforcement, no prod without tag); **Reserved** and **Savings Plans** at scale; **regular** review and optimization.

---

## Q10. (Advanced) Senior red flags to avoid in FinOps

**Answer:**  
- **No budgets or alerts** (bill shock).  
- **No tags** (can’t attribute cost).  
- **Over-provisioning** and never right-sizing.  
- **Ignoring** data transfer and request costs (S3, API Gateway).  
- **On-demand only** at scale (no Reserved/Savings Plans).  
- **No lifecycle** (storage and backups grow forever).  
- **Spot** for critical single instance without strategy.  
- **Optimizing** without measuring (use Cost Explorer and metrics).

---

**Tradeoffs:** Startup: budgets, tags, right-size. Medium: Savings Plans, lifecycle, showback. Enterprise: chargeback, FinOps, policies.
